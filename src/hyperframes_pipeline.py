#!/usr/bin/env python3
"""Compile a validated AI shot list into seekable HyperFrames compositions.

Optional Kokoro narration runs via the HyperFrames CLI and uses measured WAV
lengths to establish precise audio/scene timing. The existing FFmpeg renderer is
untouched; HyperFrames is an additional production path.
"""
import argparse
import copy
import html
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys

from ai_director import validate_plan
from captions import cues_for_plan, to_srt
from visual_scenes import render_visual

ROOT = Path(__file__).resolve().parents[1]
HYPERFRAMES_BIN = ROOT / 'node_modules' / '.bin' / 'hyperframes'
GSAP_BUNDLE = ROOT / 'node_modules' / 'gsap' / 'dist' / 'gsap.min.js'


def hyperframes_cli():
    if not HYPERFRAMES_BIN.is_file():
        raise RuntimeError('Pinned HyperFrames is missing: run npm ci in the repository root')
    return str(HYPERFRAMES_BIN)


def bundle_gsap(project):
    """Copy licensed GSAP from the pinned local npm dependency; never fetch a CDN."""
    if not GSAP_BUNDLE.is_file():
        raise RuntimeError('Local GSAP is missing: run npm ci in the repository root')
    target = Path(project) / 'assets' / 'vendor' / 'gsap.min.js'
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(GSAP_BUNDLE, target)
    return target


FORMATS = {'vertical': (1080, 1920), 'horizontal': (1920, 1080)}


def command(args, cwd=None, capture=True):
    print('+', ' '.join(map(str, args)), flush=True)
    return subprocess.run(args, cwd=cwd, check=True,
                          stdout=subprocess.PIPE if capture else None,
                          stderr=subprocess.PIPE if capture else None, text=True)


def wav_duration(path):
    result = command(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                      '-of', 'default=nokey=1:noprint_wrappers=1', str(path)])
    value = float(result.stdout.strip())
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f'Invalid WAV duration: {path}')
    return value


def prepare_audio(plan, assets, voice='af_heart', generate=False):
    audio = []
    if not generate:
        return [(None, float(s['duration'])) for s in plan['scenes']]
    if not re.fullmatch(r'[a-z]{2}_[a-z0-9]+', voice):
        raise ValueError('Invalid Kokoro voice ID')
    cli = hyperframes_cli()
    assets.mkdir(parents=True, exist_ok=True)
    for i, s in enumerate(plan['scenes']):
        path = assets / f'{i:03d}.wav'
        # Use the installed HyperFrames CLI, which performs local Kokoro TTS.
        command([cli, 'tts', s['narration'],
                 '--voice', voice, '--output', str(path)], capture=False)
        seconds = wav_duration(path)
        # Avoid clipping or abrupt cuts; narration determines shot timing.
        audio.append((path.name, max(2.0, round(seconds + 0.35, 3))))
    return audio


def build_html(plan, format_name, voice_files):
    width, height = FORMATS[format_name]
    vertical = format_name == 'vertical'
    scale = 1 if vertical else .73
    total = round(sum(d for _, d in voice_files), 3)
    t = 0.0
    sections, audios, animation = [], [], []
    cues = cues_for_plan(plan, voice_files)
    safe_topic = html.escape(plan['topic'], quote=True)
    for i, (scene, (wav_name, duration)) in enumerate(zip(plan['scenes'], voice_files)):
        start = round(t, 3)
        sid = f'scene-{i}'
        title = html.escape(scene['title'], quote=True)
        subtitle = html.escape(scene['subtitle'], quote=True)
        visual_type = scene.get('visual', 'abstract')
        rich = visual_type != 'abstract'
        art_markup = render_visual(visual_type, i)
        decoration = '' if rich else '<div class="decor"><span></span><span></span><span></span></div>'
        scene_cues = [cue for cue in cues if cue['scene'] == i]
        caption_markup = ''.join(
            f'<div id="cap-{i}-{cue["index"]}" class="caption-window">{html.escape(cue["text"], quote=True)}</div>'
            for cue in scene_cues
        )
        # Optional motion presets become deterministic, seekable GSAP tweens.
        motion = scene.get('motion', 'rise')
        enters = {
            'rise': 'y:90,opacity:0', 'slide': 'x:-130,opacity:0',
            'zoom': 'scale:0.65,opacity:0', 'rotate': 'rotation:-8,scale:0.9,opacity:0',
            'pop': 'scale:0.7,opacity:0',
        }[motion]
        sections.append(f'''<section id="{sid}" class="clip scene{' visual-rich' if rich else ''}" data-start="{start:g}" data-duration="{duration:g}" data-track-index="1">
  {decoration}
  {art_markup}
  <div class="stripe"></div><p class="eyebrow">AETHER VIDEO ENGINE <span>{i+1:02d}/{len(plan['scenes']):02d}</span></p>
  <div class="story"><div class="index">0{i+1}</div><h1 id="title-{i}">{title}</h1>
  <p id="subtitle-{i}" class="subtitle">{subtitle}</p></div>
  <div class="caption-track">{caption_markup}</div>
  <footer><b>{safe_topic}</b><span>EXPLORE THE IDEA</span></footer>
  <div id="progress-{i}" class="progress"></div>
</section>''')
        if wav_name:
            audios.append(f'<audio id="voice-{i}" class="clip" src="assets/voice/{wav_name}" data-start="{start:g}" data-duration="{duration:g}" data-track-index="10" data-volume="1"></audio>')
        anim_length = min(.75, duration / 3)
        # Global positions are explicit, not wall-clock timers or infinite CSS animation.
        animation.append(f'''tl.fromTo('#title-{i}',{{{enters}}},{{x:0,y:0,scale:1,rotation:0,opacity:1,duration:{anim_length:.3f},ease:'power3.out'}},{start + .12:.3f});
tl.fromTo('#subtitle-{i}',{{y:35,opacity:0}},{{y:0,opacity:1,duration:0.55,ease:'power2.out'}},{start + .4:.3f});
tl.fromTo('#progress-{i}',{{scaleX:0}},{{scaleX:1,duration:{duration:.3f},ease:'none'}},{start:.3f});''')
        if rich:
            animation.append(
                f"tl.fromTo('#visual-{i}',{{opacity:0,scale:.92}},{{opacity:1,scale:1,duration:1.05,ease:'power2.out'}},{start+.16:.3f});"
            )
            animation.append(
                f"tl.fromTo('#visual-{i} .ray',{{opacity:.16}},{{opacity:.88,duration:1.30,stagger:.055,ease:'power2.out'}},{start+.48:.3f});"
            )
        for cue in scene_cues:
            cap = f'#cap-{i}-{cue["index"]}'
            animation.append(f"tl.set('{cap}',{{opacity:1}},{cue['start']:.3f});")
            animation.append(f"tl.set('{cap}',{{opacity:0}},{cue['end']:.3f});")
        t += duration
    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AetherRendering – {safe_topic}</title>
<style>
*{{box-sizing:border-box}}html,body{{margin:0;padding:0;width:{width}px;height:{height}px;overflow:hidden;background:#080E19;color:white;font-family:Arial,'DejaVu Sans',sans-serif}}
#root{{width:{width}px;height:{height}px;position:relative;overflow:hidden;background:radial-gradient(ellipse at 50% 23%,#1A3040 0%,#09111C 57%,#070B14 100%)}}
.scene{{position:absolute;inset:0;padding:{110 if vertical else 75}px {100 if vertical else 140}px;display:flex;flex-direction:column;overflow:hidden}}
.eyebrow{{font-size:{25 if vertical else 25}px;letter-spacing:5px;color:{plan.get('accent','#4CE0C1')};font-weight:bold;display:flex;justify-content:space-between;z-index:2}}
.story{{margin:auto 0;position:relative;z-index:2;max-width:{920 if vertical else 1560}px}}
.index{{font-size:{140 if vertical else 110}px;font-weight:900;letter-spacing:-10px;color:rgba(255,255,255,.08);line-height:1}}
h1{{font-size:{103 if vertical else 117}px;line-height:1.01;letter-spacing:-3px;text-transform:uppercase;margin:8px 0 45px;font-weight:900;overflow-wrap:anywhere}}
.subtitle{{font-size:{41 if vertical else 43}px;line-height:1.24;color:#D6E5EB;max-width:1200px}}
.stripe{{position:absolute;left:0;top:0;width:13px;height:100%;background:{plan.get('accent','#4CE0C1')}}}
.decor{{position:absolute;inset:0;opacity:.25;pointer-events:none}}.decor span{{position:absolute;border-radius:50%;border:5px solid {plan.get('accent','#4CE0C1')};width:600px;height:600px;right:-250px;top:10%}}.decor span:nth-child(2){{right:-100px;top:28%;width:370px;height:370px;opacity:.4}}.decor span:nth-child(3){{right:23%;top:75%;width:140px;height:140px;opacity:.6}}
footer{{font-size:23px;letter-spacing:2px;text-transform:uppercase;display:flex;justify-content:space-between;gap:30px;z-index:2;color:#9AADB8;max-width:100%;overflow:hidden;white-space:nowrap}}footer b{{color:#E3EEF2;overflow:hidden;text-overflow:ellipsis}}
.progress{{position:absolute;bottom:0;left:0;height:12px;width:100%;background:{plan.get('accent','#4CE0C1')};transform-origin:left center}}
.visual-stage{{position:absolute;z-index:1;top:{660 if vertical else 150}px;left:{85 if vertical else 900}px;right:{85 if vertical else 70}px;height:{775 if vertical else 720}px;opacity:0;transform-origin:center center;}}
.scene-svg{{width:100%;height:100%;overflow:visible;filter:drop-shadow(0 18px 46px rgba(0,0,0,.28))}}
.visual-label{{position:absolute;bottom:3%;right:6%;font-size:18px;letter-spacing:4px;color:#D5E9F6;opacity:.7}}
.scene.visual-rich .story{{position:absolute;left:{100 if vertical else 125}px;top:{270 if vertical else 225}px;right:{95 if vertical else 1020}px;margin:0;z-index:3;}}
.scene.visual-rich h1{{font-size:{83 if vertical else 82}px;line-height:1.04;max-width:100%;margin:10px 0 24px;}}
.scene.visual-rich .subtitle{{font-size:{35 if vertical else 37}px;line-height:1.3;}}
.scene.visual-rich footer{{position:absolute;left:{100 if vertical else 130}px;right:{100 if vertical else 130}px;bottom:{80 if vertical else 48}px;}}
.caption-track{{position:absolute;bottom:{190 if vertical else 135}px;left:{94 if vertical else 125}px;right:{94 if vertical else 125}px;height:{128 if vertical else 105}px;display:flex;align-items:center;z-index:12;pointer-events:none}}
.caption-window{{position:absolute;left:0;right:0;opacity:0;margin:auto;padding:{26 if vertical else 20}px 36px;border-radius:20px;border-left:8px solid {plan.get('accent','#4CE0C1')};background:rgba(5,14,26,.92);box-shadow:0 12px 42px rgba(0,0,0,.3);color:#F4F9FF;font-size:{39 if vertical else 34}px;font-weight:700;line-height:1.18;text-align:center;text-wrap:balance;text-shadow:0 2px 12px rgba(0,0,0,.45)}}
</style></head>
<body><div id="root" data-composition-id="aether-{format_name}" data-start="0" data-width="{width}" data-height="{height}" data-duration="{total:g}" data-fps="30">
{''.join(sections)}
{''.join(audios)}
</div>
<script src="assets/vendor/gsap.min.js"></script>
<script>window.__timelines=window.__timelines||{{}};
const tl=gsap.timeline({{paused:true}});
{''.join(animation)}
window.__timelines['aether-{format_name}']=tl;</script>
</body></html>
'''


def write_project(plan, destination, with_voice=False, voice='af_heart'):
    # Plan validation occurs before any file, subprocess, or network activity.
    validate_plan(plan)
    destination = Path(destination)
    voice_dir = destination / 'assets' / 'voice'
    voices = prepare_audio(plan, voice_dir, voice=voice, generate=with_voice)
    cues = cues_for_plan(plan, voices)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / 'captions.srt').write_text(to_srt(cues), encoding='utf-8')
    for name in FORMATS:
        dirpath = destination / name
        dirpath.mkdir(parents=True, exist_ok=True)
        (dirpath / 'index.html').write_text(build_html(plan, name, voices), encoding='utf-8')
        # Compilation-only unit tests may run before npm ci; a real render requires this local file.
        if GSAP_BUNDLE.is_file():
            bundle_gsap(dirpath)
        if with_voice:
            target = dirpath / 'assets' / 'voice'
            target.mkdir(parents=True, exist_ok=True)
            for wav_name, _ in voices:
                shutil.copyfile(voice_dir / wav_name, target / wav_name)
        (dirpath / 'hyperframes.json').write_text(json.dumps({
            'registry': 'https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry',
            'paths': {'blocks': 'compositions', 'components': 'compositions/components', 'assets': 'assets'}
        }, indent=2) + '\n')
    (destination / 'resolved_plan.json').write_text(json.dumps({
        **plan, 'resolved_duration_seconds': round(sum(d for _, d in voices), 3),
        'voice': voice if with_voice else 'none',
        'captions': {'timing_method': 'phrase_estimate_from_measured_scene_audio' if with_voice else 'phrase_estimate_from_planned_scene_duration',
                     'cue_count': len(cues), 'word_aligned': False},
        'scenes': [{**s, 'duration': d} for s, (_, d) in zip(plan['scenes'], voices)]
    }, indent=2, ensure_ascii=False) + '\n')
    return destination


def verify_video(path, w, h):
    probe = command(['ffprobe', '-v', 'error', '-show_entries',
                     'stream=codec_name,width,height,codec_type:format=duration', '-of', 'json', str(path)])
    result = json.loads(probe.stdout)
    videos = [x for x in result['streams'] if x['codec_type'] == 'video']
    audios = [x for x in result['streams'] if x['codec_type'] == 'audio']
    if not audios:
        raise RuntimeError(f'Missing narration audio stream: {path}')
    if audios[0].get('codec_name') not in ('aac', 'opus', 'mp3', 'pcm_s16le'):
        raise RuntimeError(f'Unexpected audio codec: {path}')
    duration = float(result['format']['duration'])
    if not math.isfinite(duration) or duration <= 0:
        raise RuntimeError(f'Invalid video duration: {path}')
    if not videos or videos[0]['width'] != w or videos[0]['height'] != h:
        raise RuntimeError(f'Wrong video dimensions: {path}')
    if videos[0]['codec_name'] != 'h264':
        raise RuntimeError(f'Wrong video codec: {path}')
    command(['ffmpeg', '-v', 'error', '-xerror', '-i', str(path), '-f', 'null', '-'])
    level = command(['ffmpeg', '-hide_banner', '-nostats', '-i', str(path),
                     '-map', '0:a:0', '-vn', '-af', 'volumedetect', '-f', 'null', '-'])
    match = re.search(r'mean_volume:\s*(-?\d+(?:\.\d+)?)\s*dB', level.stderr)
    if not match or float(match.group(1)) < -58.0:
        raise RuntimeError(f'Narration audio is silent or below audibility threshold: {path}')
    return {'path': str(path), 'size': path.stat().st_size, 'duration': duration,
            'full_decode': True, 'audio_verified': True,
            'audio_codec': audios[0]['codec_name'], 'mean_volume_db': float(match.group(1))}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan', default='build/video_plan.json')
    p.add_argument('--out-dir', default='build/hyperframes')
    p.add_argument('--voice', default='af_heart')
    p.add_argument('--tts', action='store_true', help='Generate local Kokoro audio via HyperFrames CLI')
    p.add_argument('--render', action='store_true', help='Render actual MP4 files via HyperFrames CLI')
    p.add_argument('--output', default='build/exports')
    p.add_argument('--fps', type=int, default=30)
    args = p.parse_args()
    if args.fps not in (24, 25, 30, 60):
        p.error('FPS must be 24, 25, 30, or 60')
    if args.render and not args.tts:
        p.error('For production rendering, pass --tts to include synchronized Kokoro narration')
    plan = json.loads(Path(args.plan).read_text(encoding='utf-8'))
    out = write_project(plan, args.out_dir, args.tts, args.voice)
    print('HyperFrames compositions created:', out)
    if args.render:
        cli = hyperframes_cli()
        for fmt in FORMATS:
            bundle_gsap(out / fmt)
        exports = Path(args.output)
        exports.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(out / 'captions.srt', exports / 'captions.srt')
        report = {'engine': 'hyperframes', 'voice_engine': 'kokoro-local', 'outputs': []}
        for fmt, (w, h) in FORMATS.items():
            mp4 = (exports / f'{fmt}.mp4').resolve()
            command([cli, 'lint'], cwd=out / fmt, capture=False)
            command([cli, 'render', '--output', str(mp4), '--fps', str(args.fps)], cwd=out / fmt, capture=False)
            report['outputs'].append(verify_video(mp4, w, h))
        (exports / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        print('VERIFIED two HyperFrames videos:', [x['path'] for x in report['outputs']])


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, ValueError, subprocess.CalledProcessError, OSError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        raise SystemExit(1)
