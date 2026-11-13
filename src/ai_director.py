#!/usr/bin/env python3
"""Create an original, validated video plan. Demo requires no API key; Gemini does.

The model produces DATA (a constrained shot list), never executable JS/HTML.
The deterministic HyperFrames compiler transforms this data into real animation code.
"""
import argparse
import json
import math
import os
from pathlib import Path
import re
import sys
from gemini_router import route_plan, discover_models, RouterError
from visual_scenes import VISUAL_TYPES
from kinetic_storytelling import validate_beats
from action_scenes import ACTION_TYPES, validate_action

SCENE_KEYS = {'title', 'subtitle', 'narration', 'duration', 'motion', 'visual', 'beats'}
MOTIONS = {'rise', 'slide', 'zoom', 'rotate', 'pop'}


def validate_plan(plan):
    if not isinstance(plan, dict):
        raise ValueError('Plan must be a JSON object')
    scenes = plan.get('scenes')
    if not isinstance(scenes, list) or not (2 <= len(scenes) <= 30):
        raise ValueError('Expected 2–30 scenes')
    if not isinstance(plan.get('topic'), str) or not (3 <= len(plan['topic']) <= 180):
        raise ValueError('Invalid topic')
    accent = plan.get('accent', '#4CE0C1')
    if not isinstance(accent, str) or not re.fullmatch(r'#[0-9A-Fa-f]{6}', accent):
        raise ValueError('accent must be a #RRGGBB colour')
    for i, scene in enumerate(scenes):
        if not isinstance(scene, dict) or set(scene) - SCENE_KEYS:
            raise ValueError(f'Scene {i}: unsupported keys')
        for field, max_chars in [('title', 75), ('subtitle', 160), ('narration', 380)]:
            value = scene.get(field)
            if not isinstance(value, str) or not value.strip() or len(value) > max_chars:
                raise ValueError(f'Scene {i}: invalid {field}')
        duration = scene.get('duration')
        if not isinstance(duration, (int, float)) or isinstance(duration, bool) or not (2 <= duration <= 15):
            raise ValueError(f'Scene {i}: duration must be 2–15 seconds')
        if scene.get('motion', 'rise') not in MOTIONS:
            raise ValueError(f'Scene {i}: unknown motion preset')
        # Backwards compatible: old storyboards omit 'visual' entirely.
        validate_beats(scene.get('beats'), i)
        visual = scene.get('visual')
        if visual is not None:
            if not isinstance(visual, dict) or visual.get('type') not in VISUAL_TYPES:
                raise ValueError(f'Scene {i}: invalid visual type')
            if visual['type'] in ACTION_TYPES:
                validate_action(visual, i)
                continue
            permitted = {'type', 'labels', 'values'} if visual['type'] == 'comparison' else {'type'}
            if set(visual) - permitted:
                raise ValueError(f'Scene {i}: unsupported visual configuration')
            if visual['type'] == 'comparison':
                labels, values = visual.get('labels'), visual.get('values')
                if (labels is None) != (values is None):
                    raise ValueError(f'Scene {i}: comparison labels and values must appear together')
                if labels is not None:
                    if not isinstance(labels, list) or not 2 <= len(labels) <= 4 or not all(
                            isinstance(x, str) and 1 <= len(x) <= 28 and x.strip() for x in labels):
                        raise ValueError(f'Scene {i}: comparison labels must be 2–4 short strings')
                    if not isinstance(values, list) or len(values) != len(labels) or not all(
                            isinstance(x, (int, float)) and not isinstance(x, bool)
                            and math.isfinite(x) and 0 <= x <= 1 for x in values):
                        raise ValueError(f'Scene {i}: comparison values must be numbers between 0 and 1')
    if sum(s['duration'] for s in scenes) > 180:
        raise ValueError('Video must be 180 seconds or shorter')
    return plan


def demo_plan(topic, duration):
    heads = [
        ('THE BIG QUESTION', f'What if we understood {topic} differently?', 'rise'),
        ('THE COMMON ASSUMPTION', 'Most explanations skip the mechanism.', 'slide'),
        ('WHAT ACTUALLY MATTERS', 'Break the problem into one measurable step.', 'zoom'),
        ('PUT IT TO WORK', 'Test the idea, observe results, then improve.', 'pop'),
        ('THE TAKEAWAY', 'Use evidence instead of just following the hype.', 'rotate'),
    ]
    # Demonstration wording is intentionally generic, not fabricated factual content.
    count = 3 if duration <= 18 else 5
    per = max(2.0, min(15.0, duration / count))
    return validate_plan({
        'topic': topic, 'accent': '#4CE0C1',
        'scenes': [
            {'title': title, 'subtitle': subtitle, 'narration': narration,
             'duration': round(per, 3), 'motion': motion}
            for title, narration, motion in heads[:count]
            for subtitle in [narration]
        ],
    })


def gemini_prompt(topic, duration):
    n = max(3, min(15, round(duration / 5)))
    return (f'Create an ORIGINAL short educational social video about: {topic!r}. '
            f'Target approximately {duration} seconds split into {n} scenes. '
            'Return ONLY JSON: {"topic":str,"accent":"#4CE0C1","scenes":'
            '[{"title":str,"subtitle":str,"narration":str,"duration":number,'
            '"motion":str,"visual":{"type":str},"beats":[str,str,str]}]}. '
            'Add 2 or 3 concise visual beat labels per scene, each 2–8 words. '
            'Beat labels must explain successive stages of the visual and be factually accurate. '
            'For visuals, choose an optional object type from spectrum,particles,orbit,comparison,horizon,sky_dome,perception. '
            'Use each only when it helps explain the content; varied visual styles are preferred. Prefer sky_dome to explain atmospheric scattering and perception for qualitative color vision; do not fabricate numeric values for scientific comparisons. For action scenes, support character_stage (requires prop and optionally action: introduce,point,lift,operate,celebrate), object_chain (requires items array of 2–4 named props), product_focus (requires prop); allowed props are sun,solar_panel,battery,lamp,gear,book,box; optional camera is wide,push_in,pan_left,pan_right,detail. Use actions to SHOW what the narration describes rather than writing another static slide. '
            'For comparison only, optional equal-length arrays labels (2-4 short strings) and values (0-1 numbers) are supported. '
            'Each scene lasts 2–15 seconds. Motion must be one of rise,slide,zoom,rotate,pop. '
            'Use a persuasive opening, logically developed explanation, useful takeaway. '
            'Do not fabricate research, statistics, product pricing, quotations, or factual claims. '
            'Keep title under 75 characters, subtitle under 160, narration under 380. '
            'Ensure narration fits the time at a normal speaking rate. '
            'No markdown, no JavaScript, no URLs, no external assets. '
            'Use clear readable language; vary scene motions meaningfully.')


def gemini_plan(topic, duration, model='auto', complexity='auto',
                router_config='config/gemini_router.json',
                usage_state='state/gemini_usage.json',
                router_audit='build/gemini_router_audit.json'):
    prompt = gemini_prompt(topic, duration)
    plan, _ = route_plan(prompt, router_config, usage_state, router_audit,
                         model, complexity, topic, duration, validate_plan)
    return plan


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--topic', required=True)
    ap.add_argument('--duration', type=int, default=25)
    ap.add_argument('--provider', choices=['demo', 'gemini'], default='demo')
    ap.add_argument('--model', default=os.environ.get('GEMINI_MODEL', 'auto'), help='auto or configured Gemini model ID')
    ap.add_argument('--complexity', choices=['auto', 'simple', 'standard', 'complex'], default='auto')
    ap.add_argument('--router-config', default='config/gemini_router.json')
    ap.add_argument('--usage-state', default='state/gemini_usage.json')
    ap.add_argument('--router-audit', default='build/gemini_router_audit.json')
    ap.add_argument('--list-models', action='store_true', help='Discover supported Gemini models without generating a video')
    ap.add_argument('--out', default='build/video_plan.json')
    args = ap.parse_args()
    if args.list_models:
        models = sorted(discover_models(os.environ.get('GEMINI_API_KEY', '')))
        print(json.dumps({'generateContent_models': models}, indent=2))
        return
    if not (6 <= args.duration <= 120):
        ap.error('Duration must be between 6 and 120 seconds')
    plan = (gemini_plan(args.topic, args.duration, args.model, args.complexity,
                        args.router_config, args.usage_state, args.router_audit)
            if args.provider == 'gemini' else demo_plan(args.topic, args.duration))
    dest = Path(args.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'Plan written: {dest} ({len(plan["scenes"])} scenes, {sum(s["duration"] for s in plan["scenes"]):g}s planned)')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, ValueError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        raise SystemExit(1)
