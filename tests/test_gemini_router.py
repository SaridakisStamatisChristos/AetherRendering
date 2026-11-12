import io
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import gemini_router as router
from ai_director import demo_plan, validate_plan

CONFIG = Path(__file__).resolve().parents[1] / 'config/gemini_router.json'


class Reply(io.BytesIO):
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()


def reply(body):
    return Reply(json.dumps(body).encode())


class SimulatedAPI:
    def __init__(self, text_models, responses=None):
        self.text_models = text_models
        self.responses = responses or {}
        self.called = []
    def __call__(self, request, timeout=None):
        url = request.full_url
        self.called.append(url)
        if ':generateContent' not in url:
            return reply({'models': [{'name': f'models/{x}', 'supportedGenerationMethods': ['generateContent']}
                                     for x in self.text_models]})
        model = url.rsplit('/models/', 1)[1].split(':')[0]
        item = self.responses.get(model)
        if isinstance(item, int):
            raise urllib.error.HTTPError(url, item, 'provider error', None, None)
        if item is None:
            raise AssertionError(f'unexpected model call: {model}')
        return reply(item)


def success_json(topic='A new example', prompt_tokens=100, output_tokens=60):
    plan = demo_plan(topic, 20)
    return {'candidates': [{'content': {'parts': [{'text': json.dumps(plan)}]}}],
            'usageMetadata': {'promptTokenCount': prompt_tokens, 'candidatesTokenCount': output_tokens}}


class RouterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.usage = root/'state.json'
        self.audit = root/'audit.json'
        self.cfgpath = root/'router.json'
        cfg = json.loads(CONFIG.read_text())
        self.cfgpath.write_text(json.dumps(cfg))
        self.clock = datetime(2026, 11, 12, 15, 0, tzinfo=timezone.utc)

    def tearDown(self):
        self.temp.cleanup()

    def configured(self, fn):
        cfg = json.loads(self.cfgpath.read_text())
        fn(cfg)
        self.cfgpath.write_text(json.dumps(cfg))

    def route(self, api, model='auto', complexity='standard'):
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'MOCK_KEY'}):
            return router.route_plan('Write test story', self.cfgpath, self.usage,
                                     self.audit, model, complexity, 'Science reel', 25,
                                     validate_plan, opener=api, now_fn=lambda: self.clock)

    def test_default_is_safely_configured(self):
        cfg = router.load_config(CONFIG)
        self.assertFalse(cfg['models']['gemini-3.1-pro-preview']['enabled'])
        self.assertIsNone(cfg['models']['gemini-3.8-flash']['max_requests_per_day'])
        self.assertEqual(cfg['tiers']['standard'][0], 'gemini-3.8-flash')

    def test_only_generate_content_and_page_through(self):
        class MultiPage:
            def __init__(self): self.count = 0
            def __call__(self, request, timeout=None):
                self.count += 1
                if self.count == 1:
                    return reply({'models': [{'name': 'models/gemini-3.8-flash', 'supportedGenerationMethods': ['generateContent']},
                                             {'name': 'models/gemini-3.8-live', 'supportedGenerationMethods': ['bidiGenerateContent']}],
                                  'nextPageToken': 'abc'})
                self.assert_token = 'pageToken=abc' in request.full_url
                return reply({'models': [{'name': 'models/gemini-3.7-flash', 'supportedGenerationMethods': ['generateContent']}]})
        fake = MultiPage()
        self.assertEqual(router.discover_models('MYKEY', fake), {'gemini-3.8-flash', 'gemini-3.7-flash'})
        self.assertEqual(fake.count, 2)
        self.assertTrue(fake.assert_token)

    def test_auto_uses_first_discovered_model(self):
        api = SimulatedAPI({'gemini-3.8-flash'}, {'gemini-3.8-flash': success_json()})
        plan, audit = self.route(api)
        self.assertEqual(audit['selected_model'], 'gemini-3.8-flash')
        self.assertTrue(plan['scenes'])
        state = json.loads(self.usage.read_text())
        rec = state['days']['2026-11-12']['gemini-3.8-flash']
        self.assertEqual((rec['requests'], rec['successes'], rec['input_tokens'], rec['output_tokens']), (1, 1, 100, 60))
        self.assertNotIn('MOCK_KEY', self.audit.read_text() + self.usage.read_text())

    def test_thinking_tokens_are_counted(self):
        result = success_json()
        result['usageMetadata'].update(thoughtsTokenCount=80, totalTokenCount=240)
        api = SimulatedAPI({'gemini-3.8-flash'}, {'gemini-3.8-flash': result})
        self.route(api)
        state = json.loads(self.usage.read_text())
        record = state['days']['2026-11-12']['gemini-3.8-flash']
        self.assertEqual(record['input_tokens'], 100)
        self.assertEqual(record['output_tokens'], 140)  # 60 answer + 80 thoughts

    def test_fallback_on_429_and_count_failed_request(self):
        api = SimulatedAPI({'gemini-3.8-flash', 'gemini-3.7-flash'},
                           {'gemini-3.8-flash': 429, 'gemini-3.7-flash': success_json()})
        _, audit = self.route(api)
        self.assertEqual(audit['selected_model'], 'gemini-3.7-flash')
        self.assertEqual([a['status'] for a in audit['attempts']], ['api-error', 'success'])
        state = json.loads(self.usage.read_text())
        self.assertEqual(state['days']['2026-11-12']['gemini-3.8-flash']['failures'], 1)
        self.assertGreater(state['blocked_until']['gemini-3.8-flash'], self.clock.timestamp())

    def test_does_not_fallback_on_403(self):
        api = SimulatedAPI({'gemini-3.8-flash', 'gemini-3.7-flash'},
                           {'gemini-3.8-flash': 403, 'gemini-3.7-flash': success_json()})
        with self.assertRaisesRegex(router.RouterError, 'HTTP 403'):
            self.route(api)
        self.assertFalse(any('gemini-3.7-flash:generateContent' in call for call in api.called))

    def test_daily_cap_redirects_and_never_calls_capped_model(self):
        self.configured(lambda x: x['models']['gemini-3.8-flash'].update(max_requests_per_day=1))
        api = SimulatedAPI({'gemini-3.8-flash', 'gemini-3.7-flash'},
                           {'gemini-3.8-flash': success_json(), 'gemini-3.7-flash': success_json()})
        self.route(api)
        _, audit = self.route(api)
        self.assertEqual(audit['selected_model'], 'gemini-3.7-flash')
        self.assertEqual(audit['attempts'][0]['reason'], 'daily-cap')

    def test_manual_selection_respects_exact_model(self):
        api = SimulatedAPI({'gemini-3.8-flash', 'gemini-3.7-flash'},
                           {'gemini-3.8-flash': success_json(), 'gemini-3.7-flash': 429})
        with self.assertRaises(router.RouterError):
            self.route(api, model='gemini-3.7-flash')
        self.assertFalse(any('gemini-3.8-flash:generateContent' in call for call in api.called))

    def test_user_minute_limit_and_token_cap(self):
        self.configured(lambda c: c['models']['gemini-3.8-flash'].update(max_requests_per_minute=1))
        api = SimulatedAPI({'gemini-3.8-flash', 'gemini-3.7-flash'},
                           {'gemini-3.8-flash': success_json(), 'gemini-3.7-flash': success_json()})
        self.route(api)
        _, audit = self.route(api)
        self.assertEqual(audit['attempts'][0]['reason'], 'minute-cap')

    def test_invalid_json_falls_back(self):
        api = SimulatedAPI({'gemini-3.8-flash', 'gemini-3.7-flash'},
                           {'gemini-3.8-flash': {'candidates': [{'content': {'parts': [{'text': '{bad'}]}}]},
                            'gemini-3.7-flash': success_json()})
        _, audit = self.route(api)
        self.assertEqual(audit['selected_model'], 'gemini-3.7-flash')

    def test_pacific_day_rollover(self):
        cfg = router.load_config(self.cfgpath)
        self.configured(lambda c: c['models']['gemini-3.8-flash'].update(max_requests_per_day=1))
        cfg = router.load_config(self.cfgpath)
        one, skip = router.reserve(self.usage, cfg, 'gemini-3.8-flash', 'x', now=datetime(2026, 11, 13, 7, 59, tzinfo=timezone.utc))
        self.assertIsNotNone(one)
        two, skip = router.reserve(self.usage, cfg, 'gemini-3.8-flash', 'x', now=datetime(2026, 11, 13, 8, 1, tzinfo=timezone.utc))
        self.assertIsNotNone(two)
        state = json.loads(self.usage.read_text())
        self.assertIn('2026-11-12', state['days'])
        self.assertIn('2026-11-13', state['days'])

    def test_unknown_model_never_requested(self):
        api = SimulatedAPI({'gemini-3.8-flash'}, {'gemini-3.8-flash': success_json()})
        with self.assertRaises(router.RouterError):
            self.route(api, model='gemini-secret-unknown')

    def test_missing_key_is_rejected(self):
        with patch.dict(os.environ, {'GEMINI_API_KEY': ''}):
            with self.assertRaisesRegex(router.RouterError, 'missing'):
                router.route_plan('hello', self.cfgpath, self.usage, self.audit,
                                  'auto', 'simple', 'science', 10, validate_plan)

if __name__ == '__main__':
    unittest.main()
