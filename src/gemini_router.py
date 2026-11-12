#!/usr/bin/env python3
"""Gemini model discovery, safe routing, configurable caps and local usage accounting.

The quota tracker enforces *user-configured* guardrails; it is not Google's
project-side quota service. Use a shared state file for all runs in a project.
No secrets, prompts, or generated contents are written to the audit or state.
"""
import contextlib
from datetime import datetime, timedelta, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from uuid import uuid4
from zoneinfo import ZoneInfo

BASE_URL = 'https://generativelanguage.googleapis.com/v1beta/models'
MODEL_PATTERN = re.compile(r'^gemini-[A-Za-z0-9_.-]+$')
PACIFIC = ZoneInfo('America/Los_Angeles')
RETRYABLE_HTTP = {429, 500, 502, 503, 504}
MODEL_UNAVAILABLE_HTTP = {404}


class RouterError(RuntimeError):
    pass


class APIError(RouterError):
    def __init__(self, code, message='Gemini request failed'):
        self.code = code
        super().__init__(f'{message} (HTTP {code})')


def _now():
    return datetime.now(timezone.utc)


def _read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding='utf-8'))


def _atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=f'.{path.name}.', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


@contextlib.contextmanager
def _locked(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with (path.with_suffix(path.suffix + '.lock')).open('a+b') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def load_config(path):
    cfg = _read_json(path)
    if not isinstance(cfg, dict) or cfg.get('version') != 1:
        raise RouterError('Invalid router config or schema version')
    models = cfg.get('models')
    tiers = cfg.get('tiers')
    if not isinstance(models, dict) or not models or not isinstance(tiers, dict):
        raise RouterError('Config needs models and tiers')
    for name, rules in models.items():
        if not MODEL_PATTERN.fullmatch(name) or not isinstance(rules, dict) or type(rules.get('enabled')) is not bool:
            raise RouterError(f'Invalid model configuration: {name}')
        for key in ('max_requests_per_day', 'max_requests_per_minute', 'max_tokens_per_minute'):
            value = rules.get(key)
            if value is not None and (type(value) is not int or value <= 0):
                raise RouterError(f'{name}: {key} must be a positive integer or null')
        output = rules.get('max_output_tokens')
        if type(output) is not int or not 256 <= output <= 65536:
            raise RouterError(f'{name}: invalid max_output_tokens')
    for tier in ('simple', 'standard', 'complex'):
        names = tiers.get(tier)
        if not isinstance(names, list) or not names or len(names) != len(set(names)) or any(n not in models for n in names):
            raise RouterError(f'Invalid model tier {tier}')
    if cfg.get('discovery_required') is not True:
        raise RouterError('Live model discovery is mandatory; discovery_required must be true')
    return cfg


def discover_models(api_key, opener=None):
    """List only models advertising generateContent. Pagination is mandatory."""
    if not api_key:
        raise RouterError('GEMINI_API_KEY is missing')
    opener = opener or urllib.request.urlopen
    available = set()
    page = ''
    seen = set()
    for _ in range(30):
        query = {'pageSize': '100'}
        if page:
            query['pageToken'] = page
        request = urllib.request.Request(
            BASE_URL + '?' + urllib.parse.urlencode(query),
            headers={'x-goog-api-key': api_key, 'Accept': 'application/json'})
        try:
            with opener(request, timeout=30) as response:
                data = json.load(response)
        except urllib.error.HTTPError as exc:
            raise APIError(exc.code, 'Model discovery failed') from None
        except (ValueError, OSError) as exc:
            raise RouterError('Model discovery returned an invalid response') from exc
        for entry in data.get('models', []):
            raw = entry.get('name', '')
            name = raw[7:] if raw.startswith('models/') else ''
            if MODEL_PATTERN.fullmatch(name) and 'generateContent' in entry.get('supportedGenerationMethods', []):
                available.add(name)
        token = data.get('nextPageToken')
        if not token:
            return available
        if token in seen:
            raise RouterError('Model discovery pagination loop')
        seen.add(token)
        page = token
    raise RouterError('Model discovery exceeded page limit')


def resolve_complexity(topic, duration, requested):
    if requested != 'auto':
        if requested not in ('simple', 'standard', 'complex'):
            raise RouterError('Invalid complexity setting')
        return requested
    # Deterministic heuristic; callers can explicitly override it.
    if duration >= 70 or re.search(r'\b(academic|technical|research|science|mathematics|physics|documentary|medical|history)\b', topic, re.I):
        return 'complex'
    return 'simple' if duration <= 20 else 'standard'


def candidates(cfg, available, tier, requested_model='auto'):
    names = [requested_model] if requested_model != 'auto' else cfg['tiers'][tier]
    if requested_model != 'auto' and requested_model not in cfg['models']:
        raise RouterError('Manually selected model is not configured; add it to config/gemini_router.json first')
    return [n for n in names if n in available and cfg['models'][n]['enabled']]


def _default_state():
    return {'schema_version': 1, 'days': {}, 'minute_events': [], 'blocked_until': {}}


def _state_at(path, now):
    state = _read_json(path, _default_state())
    if not isinstance(state, dict) or state.get('schema_version') != 1:
        raise RouterError('Invalid usage state; refusing to discard existing accounting')
    state.setdefault('days', {})
    state.setdefault('minute_events', [])
    state.setdefault('blocked_until', {})
    threshold = now.timestamp() - 60
    state['minute_events'] = [e for e in state['minute_events'] if e['at'] > threshold]
    # Retain recent accounting for audit and avoid perpetual growth.
    today = now.astimezone(PACIFIC).date()
    state['days'] = {d: v for d, v in state['days'].items() if (today - datetime.fromisoformat(d).date()).days <= 8}
    return state


def reserve(path, cfg, model, prompt, now=None):
    """Reserve one request and pessimistic TPM estimate BEFORE sending to Google."""
    now = now or _now()
    limit = cfg['models'][model]
    day = now.astimezone(PACIFIC).date().isoformat()
    # Approximation for proactive TPM safety, NOT Google's exact token count.
    input_estimate = max(1, (len(prompt) + 3) // 4)
    estimated = input_estimate + limit['max_output_tokens']
    with _locked(path):
        state = _state_at(path, now)
        if state['blocked_until'].get(model, 0) > now.timestamp():
            return None, 'temporary-cooldown'
        record = state['days'].setdefault(day, {}).setdefault(model, {'requests': 0, 'successes': 0, 'failures': 0, 'input_tokens': 0, 'output_tokens': 0})
        if limit['max_requests_per_day'] is not None and record['requests'] >= limit['max_requests_per_day']:
            return None, 'daily-cap'
        window = [e for e in state['minute_events'] if e['model'] == model]
        if limit['max_requests_per_minute'] is not None and len(window) >= limit['max_requests_per_minute']:
            return None, 'minute-cap'
        if limit['max_tokens_per_minute'] is not None and sum(e['tokens'] for e in window) + estimated > limit['max_tokens_per_minute']:
            return None, 'tokens-minute-cap'
        rid = uuid4().hex
        state['minute_events'].append({'id': rid, 'at': now.timestamp(), 'model': model, 'tokens': estimated})
        record['requests'] += 1
        _atomic_json(path, state)
    return {'id': rid, 'day': day, 'input_estimate': input_estimate}, None


def finish(path, model, reservation, success, input_tokens=None, output_tokens=None, cooldown_seconds=0, now=None):
    now = now or _now()
    with _locked(path):
        state = _state_at(path, now)
        rec = state['days'][reservation['day']][model]
        rec['successes' if success else 'failures'] += 1
        actual_in = input_tokens if type(input_tokens) is int and input_tokens >= 0 else reservation['input_estimate']
        actual_out = output_tokens if type(output_tokens) is int and output_tokens >= 0 else 0
        rec['input_tokens'] += actual_in
        rec['output_tokens'] += actual_out
        if input_tokens is not None and output_tokens is not None:
            for event in state['minute_events']:
                if event['id'] == reservation['id']:
                    event['tokens'] = actual_in + actual_out
                    break
        if cooldown_seconds:
            state['blocked_until'][model] = max(state['blocked_until'].get(model, 0), now.timestamp() + cooldown_seconds)
        _atomic_json(path, state)


def _invoke(api_key, model, prompt, max_output_tokens, opener=None):
    opener = opener or urllib.request.urlopen
    body = json.dumps({
        'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
        'generationConfig': {
            'responseMimeType': 'application/json',
            'temperature': 0.65,
            'maxOutputTokens': max_output_tokens
        }
    }).encode('utf-8')
    req = urllib.request.Request(
        f'{BASE_URL}/{model}:generateContent', data=body,
        headers={'Content-Type': 'application/json', 'x-goog-api-key': api_key}, method='POST')
    try:
        with opener(req, timeout=100) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        raise APIError(exc.code) from None
    except (ValueError, OSError) as exc:
        raise RouterError('Gemini returned an invalid network/JSON response') from exc


def route_plan(prompt, cfg_path, usage_path, audit_path, model, complexity, topic, duration, validator, opener=None, now_fn=None):
    """Run one request with safe fallback. `validator` rejects malformed storyboards."""
    now_fn = now_fn or _now
    cfg = load_config(cfg_path)
    key = os.environ.get('GEMINI_API_KEY', '')
    available = discover_models(key, opener=opener)
    tier = resolve_complexity(topic, duration, complexity)
    options = candidates(cfg, available, tier, model)
    audit = {'schema_version': 1, 'complexity': tier, 'requested_model': model,
             'candidates': options, 'attempts': [], 'selected_model': None,
             'generated_at_utc': now_fn().isoformat()}
    if not options:
        _atomic_json(audit_path, audit)
        raise RouterError('No configured, enabled, text-generation Gemini model was discovered for this selection')
    for name in options:
        reserved, skip = reserve(usage_path, cfg, name, prompt, now=now_fn())
        if skip:
            audit['attempts'].append({'model': name, 'status': 'skipped', 'reason': skip})
            continue
        try:
            response = _invoke(key, name, prompt, cfg['models'][name]['max_output_tokens'], opener=opener)
            parts = response['candidates'][0]['content']['parts']
            raw = ''.join(part.get('text', '') for part in parts)
            parsed = json.loads(raw)
            plan = validator(parsed)
            usage = response.get('usageMetadata', {})
            finish(usage_path, name, reserved, True, usage.get('promptTokenCount'),
                   usage.get('candidatesTokenCount'), now=now_fn())
            audit['attempts'].append({'model': name, 'status': 'success'})
            audit['selected_model'] = name
            _atomic_json(audit_path, audit)
            return plan, audit
        except APIError as exc:
            finish(usage_path, name, reserved, False, cooldown_seconds=90 if exc.code == 429 else 0, now=now_fn())
            audit['attempts'].append({'model': name, 'status': 'api-error', 'http_status': exc.code})
            if exc.code not in RETRYABLE_HTTP | MODEL_UNAVAILABLE_HTTP:
                _atomic_json(audit_path, audit)
                raise RouterError(f'Gemini rejected request with HTTP {exc.code}; not trying other models') from None
        except (KeyError, IndexError, TypeError, ValueError, RouterError):
            finish(usage_path, name, reserved, False, now=now_fn())
            audit['attempts'].append({'model': name, 'status': 'invalid-response'})
    _atomic_json(audit_path, audit)
    raise RouterError('No Gemini model succeeded: inspect the redacted routing audit for attempted models')
