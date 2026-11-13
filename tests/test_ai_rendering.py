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


class CharacterAndActionTests(unittest.TestCase):
    def sample(self):
        plan=demo_plan('Solar electricity',25)
        v=[
            {'type':'character_stage','prop':'solar_panel','action':'point','camera':'wide'},
            {'type':'object_chain','items':['sun','solar_panel','battery','lamp'],'camera':'pan_right'},
            {'type':'character_stage','prop':'battery','action':'operate','camera':'push_in'},
            {'type':'product_focus','prop':'lamp','camera':'detail'},
            {'type':'character_stage','prop':'lamp','action':'celebrate','camera':'pan_left'},
        ]
        for scene, config in zip(plan['scenes'],v):
            scene['visual']=config
            scene['beats']=['The starting point','Follow the change','See the result']
        return plan

    def test_five_animated_scenes_compile_for_both_aspects(self):
        plan=self.sample()
        validate_plan(plan)
        for fmt in FORMATS:
            doc=build_html(plan,fmt,[(None,5)]*5,fps=60)
            self.assertIn('id="actor-0"',doc)
            self.assertIn('id="actor-2-arm-right"',doc)
            self.assertIn('id="actor-4-eyes"',doc)
            self.assertIn('id="chain-1-0"',doc)
            self.assertIn('id="chain-1-3"',doc)
            self.assertIn('id="focus-3"',doc)
            self.assertIn('id="scene-4"',doc)
            self.assertIn('data-fps="60"',doc)
            self.assertGreater(doc.count('tl.fromTo('),90)
            self.assertNotIn('cdn.jsdelivr.net',doc)
            self.assertNotIn('<script src="https://',doc)
            self.assertEqual(doc.count('class="beat-card"'),15)

    def test_invalid_props_actions_cameras_rejected(self):
        changes=[
          {'prop':'javascript:'},
          {'action':'run_user_code'},
          {'camera':'document.write'},
          {'foo':'anything'},
        ]
        for change in changes:
            with self.subTest(change=change):
                plan=self.sample()
                plan['scenes'][0]['visual'].update(change)
                with self.assertRaisesRegex(ValueError,'(unsupported|unknown)'):
                    validate_plan(plan)

    def test_chain_must_have_bounded_known_objects(self):
        for items in ([],['sun'],['sun','battery','lamp','box','book'],
                      ['sun','<script>'],['sun',123],['sun','battery',{}]):
            with self.subTest(items=items):
                plan=self.sample()
                plan['scenes'][1]['visual']['items']=items
                with self.assertRaisesRegex(ValueError,'chain requires'):
                    validate_plan(plan)

    def test_missing_required_prop_rejected(self):
        plan=self.sample()
        plan['scenes'][3]['visual'].pop('prop')
        with self.assertRaisesRegex(ValueError,'unsupported prop'):
            validate_plan(plan)

    def test_old_visuals_and_without_visuals_preserved(self):
        for name in ('spectrum','particles','orbit','comparison','horizon','sky_dome','perception'):
            self.assertIn(name,VISUAL_TYPES)
        doc=build_html(demo_plan('Legacy compatibility',15),'horizontal',[(None,5)]*3)
        self.assertNotIn('id="actor-',doc)
        self.assertNotIn('id="chain-',doc)

    def test_all_five_character_actions_are_synthesized(self):
        from action_scenes import render_action
        for act in ('introduce','point','lift','operate','celebrate'):
            with self.subTest(action=act):
                body, gsap=render_action({'type':'character_stage','prop':'box','action':act},0,0.0,6.0)
                self.assertIn('actor-0-head',body)
                self.assertIn("tl.fromTo('#actor-0'",gsap)
                self.assertIn('duration:',gsap)

    def test_camera_selection_changes_temporal_geometry(self):
        from action_scenes import render_action
        for camera in ('wide','push_in','pan_left','pan_right','detail'):
            with self.subTest(camera=camera):
                body, events=render_action(
                    {'type':'product_focus','prop':'gear','camera':camera},1,5.0,6.0)
                self.assertIn('focus-1',body)
                self.assertIn("visual-stage-1",events)
                self.assertIn('duration:6.000',events)


class PropAnchorRegressionTests(unittest.TestCase):
    def test_prop_anchor_does_not_get_overwritten_by_gsap(self):
        from action_scenes import render_action
        body,tweens=render_action(
            {'type':'object_chain','items':['sun','solar_panel','battery','lamp']},1,0.0,6.0)
        self.assertIn('class="prop-anchor" transform="translate(150 305)"',body)
        self.assertIn('id="chain-1-0" transform="scale(0.620)"',body)
        self.assertIn('class="prop-anchor" transform="translate(850 305)"',body)
        self.assertIn('id="chain-1-3" transform="scale(0.620)"',body)
        self.assertIn("tl.fromTo('#chain-1-3'",tweens)

    def test_lamp_focus_retains_position_through_scale_animation(self):
        from action_scenes import render_action
        body,tweens=render_action({'type':'product_focus','prop':'lamp'},0,0.0,6.0)
        self.assertIn('class="prop-anchor" transform="translate(500 339)"',body)
        self.assertIn('id="focus-0" transform="scale(1.700)"',body)
        self.assertIn("tl.fromTo('#focus-0'",tweens)

    def test_action_illustrations_have_separate_styling(self):
        plan=demo_plan('Action scene',15)
        plan['scenes'][0]['visual']={'type':'character_stage','prop':'gear','action':'point'}
        validate_plan(plan)
        page=build_html(plan,'vertical',[(None,5)]*3)
        self.assertIn('id="scene-0" class="clip scene rich action"',page)
        self.assertIn('transform:scale(1.10)',page)
        self.assertIn('id="scene-1" class="clip scene"',page)


class InverseKinematicsTests(unittest.TestCase):
    def test_limb_lengths_preserved_at_all_contact_poses(self):
        from kinematic_actions import (solve_ik, SHOULDER, ARM_LENGTHS,
                                       HAND_REST, HAND_CONTACT, HAND_CARRY, HAND_INSPECT)
        import math
        for hand in (HAND_REST,HAND_CONTACT,HAND_CARRY,HAND_INSPECT):
            elbow=solve_ik(SHOULDER,hand,*ARM_LENGTHS)
            self.assertAlmostEqual(math.dist(SHOULDER,elbow),ARM_LENGTHS[0],places=5)
            self.assertAlmostEqual(math.dist(elbow,hand),ARM_LENGTHS[1],places=5)

    def test_unreachable_target_rejected(self):
        from kinematic_actions import solve_ik,SHOULDER,ARM_LENGTHS
        for target in ((1200,200),SHOULDER,(float('nan'),300)):
            with self.subTest(target=target),self.assertRaisesRegex(ValueError,"Unreachable"):
                solve_ik(SHOULDER,target,*ARM_LENGTHS)

    def test_correct_contact_to_lift_offsets(self):
        from kinematic_actions import (HAND_CONTACT,HAND_CARRY,PROP_LIFT)
        self.assertEqual((round(HAND_CARRY[0]-HAND_CONTACT[0]),
                          round(HAND_CARRY[1]-HAND_CONTACT[1])),PROP_LIFT)

    def test_all_behaviors_have_hand_pose_and_prop_anchor(self):
        from kinematic_actions import render_kinematic, BEHAVIORS
        for behavior in BEHAVIORS:
            with self.subTest(behavior=behavior):
                config={"type":"kinematic_stage","prop":"battery","behavior":behavior}
                body,motion=render_kinematic(config,0,6.,6.)
                self.assertIn('id="ik-arm-0-upper"',body)
                self.assertIn('id="ik-arm-0-lower"',body)
                self.assertIn('id="ik-arm-0-hand"',body)
                self.assertIn('id="prop-mover-0"',body)
                self.assertIn('class="prop-anchor"',body)
                self.assertIn("tl.fromTo('#visual-stage-0'",motion)
                self.assertIn('duration',motion)

    def test_walk_has_foot_ik_and_translating_actor(self):
        from kinematic_actions import render_kinematic
        body, motion=render_kinematic(
            {"type":"kinematic_stage","prop":"box","behavior":"walk_to"},1,5.,7.)
        self.assertIn('id="ik-leg-1-left-upper"',body)
        self.assertIn('id="ik-leg-1-right-lower"',body)
        self.assertIn("tl.fromTo('#walking-actor-1'",motion)
        self.assertIn("tl.fromTo('#ik-leg-1-left-upper'",motion)
        self.assertIn('"attr"',motion)

    def test_pickup_object_moves_in_same_time_window_as_hand(self):
        from kinematic_actions import render_kinematic
        _,motion=render_kinematic(
            {"type":"kinematic_stage","prop":"battery","behavior":"pick_up"},2,0.,8.)
        self.assertIn("tl.fromTo('#prop-mover-2'",motion)
        # Wrist and carried prop share the .52-.71 scene interval.
        self.assertIn(",4.160);",motion)
        self.assertIn('x:-40.000,y:-75.000',motion)

    def test_unsafe_kinematic_data_fails_before_compile(self):
        from kinematic_actions import BEHAVIORS
        for config in (
                {'type':'kinematic_stage','prop':'javascript','behavior':'pick_up'},
                {'type':'kinematic_stage','prop':'box','behavior':'exec'},
                {'type':'kinematic_stage','prop':'box','behavior':'pick_up','camera':'eval'},
                {'type':'kinematic_stage','prop':'box','behavior':'pick_up','script':'alert(1)'}):
            plan=demo_plan("Invalid action",15)
            plan['scenes'][0]['visual']=config
            with self.subTest(config=config),self.assertRaises(ValueError):
                validate_plan(plan)

    def test_legacy_action_scene_still_compiles(self):
        plan=demo_plan('Legacy action',15)
        plan['scenes'][0]['visual']={'type':'character_stage','prop':'lamp',
                                    'action':'point','camera':'wide'}
        validate_plan(plan)
        page=build_html(plan,'vertical',[(None,5)]*3)
        self.assertIn('id="actor-0-arm-right"',page)
        self.assertNotIn('id="ik-arm-0-upper"',page)

    def test_renderer_handles_kinematic_stage_in_two_video_formats(self):
        plan=demo_plan('Physical storytelling',15)
        plan['scenes'][0]['visual']={'type':'kinematic_stage',
                                   'prop':'battery','behavior':'pick_up','camera':'push_in'}
        plan['scenes'][0]['beats']=['Reach','Grasp','Lift']
        validate_plan(plan)
        for fmt in FORMATS:
            page=build_html(plan,fmt,[(None,5)]*3,fps=60)
            self.assertIn('id="ik-arm-0-upper"',page)
            self.assertIn('id="prop-mover-0"',page)
            self.assertIn('data-fps="60"',page)
            self.assertIn('id="beat-0-2"',page)
            self.assertNotIn('cdn.jsdelivr.net',page)

class TimelineInitializationTests(unittest.TestCase):
    def test_later_keyframes_do_not_eagerly_override_earlier_poses(self):
        from kinematic_actions import render_kinematic
        for behavior in ('walk_to','pick_up','inspect','set_down','operate'):
            with self.subTest(behavior=behavior):
                _, script=render_kinematic(
                    {'type':'kinematic_stage','prop':'battery','behavior':behavior},
                    0,0.,6.)
                # .fromTo on a reused target must opt out of GSAP's eager
                # immediateRender to preserve the original seekable baseline.
                self.assertEqual(script.count('tl.fromTo('),
                                 script.count('immediateRender'),
                                 script[:1600])

    def test_demonstration_has_speech_length_suitable_for_30s_target(self):
        from pathlib import Path
        import json
        plan=json.loads((Path(__file__).resolve().parents[1] /
                         'examples/lamp_repair_ik_30s.json').read_text())
        words=sum(len(s['narration'].split()) for s in plan['scenes'])
        self.assertGreaterEqual(words,85)
        self.assertLessEqual(words,95)
        validate_plan(plan)


if __name__ == '__main__':
    unittest.main()
