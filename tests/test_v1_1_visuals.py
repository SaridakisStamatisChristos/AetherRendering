import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1] / 'src'))
from ai_director import validate_plan, gemini_prompt
from visual_scenes import VISUALS, render_visual
from captions import segments, cues_for_plan, to_srt
from hyperframes_pipeline import build_html, write_project


def sample():
    return {
        'topic': 'Why is the sky blue?',
        'accent': '#4CE0C1',
        'scenes': [
            {'title': 'LIGHT', 'subtitle': 'Light enters.', 'narration': 'White light enters a prism. Different colors bend differently.',
             'duration': 5, 'motion': 'rise', 'visual': 'spectrum'},
            {'title': 'BLUE', 'subtitle': 'Blue scatters.', 'narration': 'Blue light scatters in many directions. Look at the beautiful sky.',
             'duration': 6, 'motion': 'slide', 'visual': 'scatter'}
        ]
    }


class VisualSceneTests(unittest.TestCase):
    def test_each_preset_produces_unique_local_svg(self):
        names = VISUALS - {'abstract'}
        self.assertEqual(len(names), 5)
        bodies = []
        for i, preset in enumerate(sorted(names)):
            result = render_visual(preset,i)
            self.assertIn('<svg ',result)
            self.assertIn('viewBox="0 0 800 600"',result)
            self.assertIn(f'id="visual-{i}"',result)
            self.assertNotIn('http://',result.replace('xmlns="http://www.w3.org/2000/svg"',''))
            self.assertNotIn('<image ',result)
            self.assertNotIn('<script',result)
            bodies.append(result)
        self.assertEqual(len(set(bodies)),5)
    def test_abstract_keeps_existing_rendering(self):
        self.assertEqual(render_visual('abstract',0),'')
    def test_invalid_visual_rejected_before_writing(self):
        plan=sample()
        plan['scenes'][0]['visual']='<script>alert(1)</script>'
        with self.assertRaisesRegex(ValueError,'unknown visual treatment'):
            validate_plan(plan)
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/'project'
            with self.assertRaises(ValueError):
                write_project(plan,target)
            self.assertFalse(target.exists())
    def test_gemini_prompt_describes_valid_visual_enum(self):
        prompt=gemini_prompt('Why is the sky blue?',30)
        self.assertIn('wavelengths',prompt)
        self.assertIn('abstract',prompt)
        self.assertIn('"visual":str',prompt)


class CaptionTests(unittest.TestCase):
    def test_caption_segmentation_and_srt_format(self):
        text='The sunlight passes through the atmosphere and tiny particles scatter it in many different directions.'
        phrases=segments(text)
        self.assertTrue(all(1 <= len(p.split()) <= 7 for p in phrases))
        self.assertEqual(' '.join(phrases),text)
        cues=cues_for_plan(sample(),[('000.wav',5.35),('001.wav',6.35)])
        self.assertEqual(cues[0]['start'],0.0)
        self.assertLess(cues[-1]['end'],11.7)
        self.assertTrue(all(0 <= a['start'] < a['end'] for a in cues))
        self.assertTrue(all(a['end'] <= b['start'] for a,b in zip(cues,cues[1:])))
        srt=to_srt(cues)
        self.assertIn('00:00:00,000 -->',srt)
        self.assertIn('White light enters',srt)
    def test_caption_escaping_and_seekable_animation(self):
        plan=sample()
        plan['scenes'][0]['narration']='<img src=x onerror=alert(1)> is not executable narration.'
        validate_plan(plan)
        html=build_html(plan,'vertical',[(None,5.0),(None,6.0)])
        self.assertIn('&lt;img src=x onerror=alert(1)&gt;',html)
        self.assertNotIn('<img src=x onerror=alert(1)>',html)
        self.assertIn("tl.set('#cap-0-0'",html)
        self.assertIn('visual-rich',html)
        self.assertIn('scene-art-0',html)
        self.assertNotIn('setInterval(',html)
    def test_compilation_generates_srt_and_timing_provenance(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=write_project(sample(),Path(temp)/'render')
            self.assertTrue((folder/'captions.srt').is_file())
            doc=json.loads((folder/'resolved_plan.json').read_text())
            self.assertGreater(doc['captions']['cue_count'],2)
            self.assertFalse(doc['captions']['word_aligned'])
            self.assertIn('planned_scene_duration',doc['captions']['timing_method'])
            for fmt in ('vertical','horizontal'):
                markup=(folder/fmt/'index.html').read_text()
                self.assertIn('visual-rich',markup)
                self.assertIn('caption-window',markup)
                self.assertNotIn('cdn.jsdelivr.net',markup)


if __name__ == '__main__':
    unittest.main()
