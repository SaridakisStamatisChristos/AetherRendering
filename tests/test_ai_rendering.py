import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from ai_director import demo_plan, validate_plan
from visual_scenes import VISUAL_TYPES
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


class VisualSceneTests(unittest.TestCase):
    def visual_plan(self):
        plan = demo_plan('Visual demo', 25)
        visuals = [{'type':'spectrum'}, {'type':'particles'}, {'type':'orbit'},
                   {'type':'comparison','labels':['ALPHA','BETA','GAMMA'],
                    'values':[0.3,0.85,0.55]}, {'type':'horizon'}]
        for scene,visual in zip(plan['scenes'],visuals):
            scene['visual']=visual
        return plan

    def test_five_reusable_templates(self):
        plan=self.visual_plan()
        validate_plan(plan)
        voices=[(None, s['duration']) for s in plan['scenes']]
        for fmt in FORMATS:
            doc=build_html(plan,fmt,voices,fps=60)
            self.assertIn('data-fps="60"',doc)
            for i,kind in enumerate(('spectrum','particles','orbit','comparison','horizon')):
                self.assertIn(f'id="visual-stage-{i}"',doc)
                self.assertIn(f'id="scene-{i}" class="clip scene rich"',doc)
            self.assertIn('v-3-bar-2',doc)
            self.assertIn('v-4-sun',doc)
            self.assertIn('v-1-scatter-6',doc)
            self.assertGreater(doc.count('tl.fromTo('),65)
            self.assertNotIn('cdn.jsdelivr.net',doc)

    def test_legacy_plan_unchanged(self):
        doc=build_html(demo_plan('Legacy test',15),'vertical',
                       [(None,5.0)]*3)
        self.assertNotIn('class="clip scene rich"', doc)
        self.assertNotIn('visual-stage-', doc)

    def test_reject_unknown_visual(self):
        plan=self.visual_plan()
        plan['scenes'][0]['visual']={'type':'custom-js','code':'alert(1)'}
        with self.assertRaisesRegex(ValueError,'invalid visual type'):
            validate_plan(plan)

    def test_reject_injection_in_visual(self):
        plan=self.visual_plan()
        plan['scenes'][0]['visual']['javascript']='alert(1)'
        with self.assertRaisesRegex(ValueError,'unsupported visual configuration'):
            validate_plan(plan)

    def test_reject_invalid_comparisons(self):
        for labels,values in ((['A','B'],[0.5]),(['A','B'],[0.3,1.5]),
                              (['A','B'],[0.1,float('nan')]),(['A','B'],[True,0.5])):
            plan=self.visual_plan()
            plan['scenes'][3]['visual']={'type':'comparison','labels':labels,'values':values}
            with self.assertRaises(ValueError):
                validate_plan(plan)

    def test_escaped_comparison_labels(self):
        plan=self.visual_plan()
        plan['scenes'][3]['visual']['labels'][0]='<script>alert(1)</script>'
        validate_plan(plan)
        doc=build_html(plan,'vertical',[(None,5.0)]*5)
        self.assertIn('&lt;script&gt;',doc)
        self.assertNotIn('<script>alert(1)</script>',doc)


class KineticStorytellingTests(unittest.TestCase):
    def test_three_beats_are_timed_relative_to_measured_audio(self):
        from kinetic_storytelling import compile_beats
        scene={'beats':['White light arrives','Colors separate','Blue scatters outward']}
        structure,commands=compile_beats(scene,2,7.5,6.4)
        self.assertIn('beat-2-0',structure)
        self.assertIn('beat-2-2',structure)
        self.assertNotIn('beat-2-3',structure)
        self.assertIn("'#beat-2-1'",commands)
        self.assertIn('tl.to(',commands)
        self.assertEqual(commands.count('tl.fromTo('),6)
        self.assertEqual(commands.count('tl.to('),3)

    def test_optional_beats_preserve_old_rendering(self):
        plan=demo_plan('Classic source',15)
        doc=build_html(plan,'vertical',[(None,5.0)]*3)
        self.assertNotIn('beat-stage',doc.split('<body>')[1])
        self.assertNotIn('id="scene-veil-',doc)

    def test_full_sky_plan_has_independent_explanatory_beats(self):
        plan=demo_plan('Kinetic demo',25)
        visual_types=['spectrum','particles','orbit','comparison','horizon']
        for i,scene in enumerate(plan['scenes']):
            scene['visual']={'type':visual_types[i]}
            scene['beats']=['Step one','Step two','The result']
        validate_plan(plan)
        doc=build_html(plan,'vertical',[(None,5)]*5,fps=60)
        self.assertEqual(doc.count('class="beat-card"'),15)
        self.assertEqual(doc.count('class="scene-veil"'),5)
        self.assertIn("tl.to('#v-1-particle-20'",doc)
        self.assertIn("tl.to('#v-0-ray-5'",doc)
        self.assertIn("tl.to('#v-2-dot-4'",doc)
        self.assertIn("tl.to('#v-4-sun'",doc)
        self.assertIn('data-fps="60"',doc)

    def test_escapes_text_and_rejects_html_attributes(self):
        plan=demo_plan('Escape', 15)
        plan['scenes'][0]['beats']=['<script>alert(1)</script>', 'Keep & verify']
        validate_plan(plan)
        doc=build_html(plan,'vertical',[(None,5)]*3)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;',doc)
        self.assertIn('Keep &amp; verify',doc)
        self.assertNotIn('<script>alert(1)</script>',doc)

    def test_reject_malformed_beats(self):
        bad=[['one'],['1','2','3','4','5'],['valid', ''],['valid', 'x'*67],
             ['valid', 7],['valid', chr(10) + 'control']]
        for beats in bad:
            with self.subTest(beats=beats):
                plan=demo_plan('Invalid', 15)
                plan['scenes'][0]['beats']=beats
                with self.assertRaisesRegex(ValueError, 'beat'):
                    validate_plan(plan)

    def test_beats_span_actual_voice_length(self):
        from kinetic_storytelling import compile_beats
        scene={'beats':['OPEN','REVEAL','EXPLAIN','CLOSE']}
        _,short=compile_beats(scene,0,0.0,4.0)
        _,long=compile_beats(scene,0,0.0,8.0)
        self.assertNotEqual(short,long)
        self.assertIn('7.',long)
        self.assertNotIn('7.',short)


class CinematicScenesTests(unittest.TestCase):
    def test_safe_cinematic_visuals_have_multiple_timed_events(self):
        plan=demo_plan('Rayleigh scattering',25)
        plan['scenes'][0]['visual']={'type':'sky_dome'}
        plan['scenes'][1]['visual']={'type':'perception'}
        validate_plan(plan)
        doc=build_html(plan,'vertical',[(None,5)]*5,fps=60)
        self.assertIn('v-0-ray-4',doc)
        self.assertIn('v-1-channel-2',doc)
        self.assertIn('v-1-response',doc)
        self.assertIn('YOUR EYES',doc)
        self.assertIn('PERCEIVED COLOR',doc)
        self.assertNotIn('cdn.jsdelivr.net',doc)
        self.assertGreater(doc.count('tl.fromTo('),30)
        self.assertNotIn("duration:.85,ease:'power2.out'}},",doc)

    def test_unknown_visual_still_rejected(self):
        plan=demo_plan('Invalid visual',15)
        plan['scenes'][0]['visual']={'type':'anything'}
        with self.assertRaisesRegex(ValueError,'invalid visual type'):
            validate_plan(plan)

    def test_cinematic_configuration_remains_strict(self):
        plan=demo_plan('Safety',15)
        plan['scenes'][0]['visual']={'type':'perception','labels':['not allowed']}
        with self.assertRaisesRegex(ValueError,'unsupported visual configuration'):
            validate_plan(plan)

    def test_old_visuals_remain_available(self):
        for visual in ('spectrum','particles','orbit','comparison','horizon'):
            self.assertIn(visual,VISUAL_TYPES)
        self.assertIn('sky_dome', VISUAL_TYPES)
        self.assertIn('perception', VISUAL_TYPES)


class LandscapeLayoutTests(unittest.TestCase):
    def test_landscape_art_and_beat_strip_are_separated(self):
        p=demo_plan('No occlusion',15)
        p['scenes'][0]['visual']={'type':'sky_dome'}
        p['scenes'][0]['beats']=['Understand blue light','Observe the sky']
        validate_plan(p)
        page=build_html(p,'horizontal',[(None,5.0)]*3,fps=60)
        self.assertIn('top:65px;height:575px',page)
        self.assertIn('top:685px;height:90px',page)
        self.assertIn('beat-0-1',page)
        self.assertIn('data-fps="60"',page)
    def test_portrait_position_is_preserved(self):
        p=demo_plan('Portrait baseline',15)
        page=build_html(p,'vertical',[(None,5.0)]*3)
        self.assertIn('top:345px;height:850px',page)
        self.assertIn('top:1240px;height:145px',page)

if __name__ == '__main__':
    unittest.main()
