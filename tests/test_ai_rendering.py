import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from ai_director import demo_plan, validate_plan
from hyperframes_pipeline import build_html, write_project, verify_video, FORMATS
from unittest.mock import patch
from subprocess import CompletedProcess

class DirectorTests(unittest.TestCase):
    def test_demo_plan_valid(self):
        plan = demo_plan('What causes eclipses?', 25)
        self.assertEqual(len(plan['scenes']), 5)
        self.assertAlmostEqual(sum(s['duration'] for s in plan['scenes']), 25)

    def test_reject_unapproved_attributes(self):
        plan = demo_plan('Safety audit', 15)
        plan['scenes'][0]['javascript'] = 'alert(1)'
        with self.assertRaises(ValueError):
            validate_plan(plan)

    def test_reject_invalid_color(self):
        plan = demo_plan('Safety audit', 15)
        plan['accent'] = 'red; background:url(http://bad.example)'
        with self.assertRaises(ValueError):
            validate_plan(plan)

    def test_reject_oversized_scenes(self):
        plan = demo_plan('Safety audit', 15)
        plan['scenes'][0]['title'] = 'x' * 1000
        with self.assertRaises(ValueError):
            validate_plan(plan)

class CompilerTests(unittest.TestCase):
    def test_compositions_are_written(self):
        plan = demo_plan('Quantum circuits', 25)
        with tempfile.TemporaryDirectory() as temp:
            out = write_project(plan, temp)
            for fmt, (w, h) in FORMATS.items():
                html = (out / fmt / 'index.html').read_text()
                self.assertIn(f'data-width="{w}"', html)
                self.assertIn(f'data-height="{h}"', html)
                self.assertIn(f'data-composition-id="aether-{fmt}"', html)
                self.assertIn("gsap.timeline({paused:true})", html)
                self.assertIn('src="assets/vendor/gsap.min.js"', html)
                self.assertNotIn('cdn.jsdelivr.net', html)
                self.assertEqual(html.count('<section id="scene-'), len(plan['scenes']))
            resolved = json.loads((out / 'resolved_plan.json').read_text())
            self.assertEqual(resolved['voice'], 'none')

    def test_escape_untrusted_model_text(self):
        plan = demo_plan('Safety demo', 15)
        plan['scenes'][0]['title'] = '<script>alert("x")</script>'
        validate_plan(plan)
        voices = [(None, s['duration']) for s in plan['scenes']]
        content = build_html(plan, 'vertical', voices)
        self.assertNotIn('<script>alert("x")</script>', content)
        self.assertIn('&lt;script&gt;', content)

    def test_invalid_plan_prevents_file_creation(self):
        plan = demo_plan('Safety demo', 15)
        plan['scenes'][0]['motion'] = 'exploit'
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / 'result'
            with self.assertRaises(ValueError):
                write_project(plan, dest)
            self.assertFalse(dest.exists())

class DeliveryValidationTests(unittest.TestCase):
    def test_reject_missing_audio_stream(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'test.mp4'
            path.write_bytes(b'fixture')
            probe = {'streams': [{'codec_type': 'video', 'width': 1080,
                                  'height': 1920, 'codec_name': 'h264'}],
                     'format': {'duration': '4.5'}}
            with patch('hyperframes_pipeline.command',
                       return_value=CompletedProcess([], 0, json.dumps(probe), '')):
                with self.assertRaisesRegex(RuntimeError, 'Missing narration audio stream'):
                    verify_video(path, 1080, 1920)

    def test_reject_silent_audio(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'test.mp4'
            path.write_bytes(b'fixture')
            probe = {'streams': [{'codec_type': 'video', 'width': 1080,
                                  'height': 1920, 'codec_name': 'h264'},
                                 {'codec_type': 'audio', 'codec_name': 'aac'}],
                     'format': {'duration': '4.5'}}
            answers = [CompletedProcess([], 0, json.dumps(probe), ''),
                       CompletedProcess([], 0, '', ''),
                       CompletedProcess([], 0, '', '[Parsed_volumedetect_0] mean_volume: -inf dB')]
            with patch('hyperframes_pipeline.command', side_effect=answers):
                with self.assertRaisesRegex(RuntimeError, 'silent or below audibility'):
                    verify_video(path, 1080, 1920)

    def test_accept_audio_with_measured_non_silent_level(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'test.mp4'
            path.write_bytes(b'fixture')
            probe = {'streams': [{'codec_type': 'video', 'width': 1080,
                                  'height': 1920, 'codec_name': 'h264'},
                                 {'codec_type': 'audio', 'codec_name': 'aac'}],
                     'format': {'duration': '4.5'}}
            answers = [CompletedProcess([], 0, json.dumps(probe), ''),
                       CompletedProcess([], 0, '', ''),
                       CompletedProcess([], 0, '', '[Parsed_volumedetect_0] mean_volume: -27.4 dB')]
            with patch('hyperframes_pipeline.command', side_effect=answers):
                result = verify_video(path, 1080, 1920)
            self.assertTrue(result['audio_verified'])
            self.assertEqual(result['mean_volume_db'], -27.4)



class BundlingTests(unittest.TestCase):
    def test_gsap_copied_into_generated_composition(self):
        from hyperframes_pipeline import bundle_gsap
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / 'gsap.min.js'
            source.write_text('/* fixture GSAP */')
            with patch('hyperframes_pipeline.GSAP_BUNDLE', source):
                out = bundle_gsap(root / 'vertical')
            self.assertEqual(out.read_text(), '/* fixture GSAP */')
            self.assertEqual(out.relative_to(root).as_posix(),
                             'vertical/assets/vendor/gsap.min.js')

if __name__ == '__main__':
    unittest.main()
