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
from visual_scenes import visual_scene
from kinetic_storytelling import compile_beats, visual_follow_through, compile_cut

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


def build_html(plan, format_name, voice_files, fps=30):
    width, height = FORMATS[format_name]
    vertical = format_name == 'vertical'
    scale = 1 if vertical else .73
    total = round(sum(d for _, d in voice_files), 3)
    t = 0.0
    sections, audios, animation = [], [], []
    safe_topic = html.escape(plan['topic'], quote=True)
    for i, (scene, (wav_name, duration)) in enumerate(zip(plan['scenes'], voice_files)):
        start = round(t, 3)
        sid = f'scene-{i}'
        title = html.escape(scene['title'], quote=True)
        subtitle = html.escape(scene['subtitle'], quote=True)
        visual_html, visual_tweens = visual_scene(scene, i, start, duration)
        beats_html, beats_tweens = compile_beats(scene, i, start, duration)
        secondary_tweens = visual_follow_through(scene, i, start, duration)
        cut_html = f'<div class="scene-veil" id="scene-veil-{i}"></div>' if beats_html else ''
        cut_tweens = compile_cut(i, start, duration) if beats_html else ''
        scene_class = 'scene rich' if visual_html else 'scene'
        # Optional motion presets become deterministic, seekable GSAP tweens.
        motion = scene.get('motion', 'rise')
        enters = {
            'rise': 'y:90,opacity:0', 'slide': 'x:-130,opacity:0',
            'zoom': 'scale:0.65,opacity:0', 'rotate': 'rotation:-8,scale:0.9,opacity:0',
            'pop': 'scale:0.7,opacity:0',
        }[motion]
        sections.append(f'''<section id="{sid}" class="clip {scene_class}" data-start="{start:g}" data-duration="{duration:g}" data-track-index="1">
  <div class="decor"><span></span><span></span><span></span></div>
  {visual_html}
  {beats_html}
  <div class="stripe"></div><p class="eyebrow">AETHER VIDEO ENGINE <span>{i+1:02d}/{len(plan['scenes']):02d}</span></p>
  <div class="story"><div class="index">0{i+1}</div><h1 id="title-{i}">{title}</h1>
  <p id="subtitle-{i}" class="subtitle">{subtitle}</p></div>
  <footer><b>{safe_topic}</b><span>EXPLORE THE IDEA</span></footer>
  <div id="progress-{i}" class="progress"></div>
  {cut_html}
</section>''')
        if wav_name:
            audios.append(f'<audio id="voice-{i}" class="clip" src="assets/voice/{wav_name}" data-start="{start:g}" data-duration="{duration:g}" data-track-index="10" data-volume="1"></audio>')
        anim_length = min(.75, duration / 3)
        # Global positions are explicit, not wall-clock timers or infinite CSS animation.
        animation.append(f'''tl.fromTo('#title-{i}',{{{enters}}},{{x:0,y:0,scale:1,rotation:0,opacity:1,duration:{anim_length:.3f},ease:'power3.out'}},{start + .12:.3f});
tl.fromTo('#subtitle-{i}',{{y:35,opacity:0}},{{y:0,opacity:1,duration:0.55,ease:'power2.out'}},{start + .4:.3f});
tl.fromTo('#progress-{i}',{{scaleX:0}},{{scaleX:1,duration:{duration:.3f},ease:'none'}},{start:.3f});
{visual_tweens}
{secondary_tweens}
{beats_tweens}
{cut_tweens}''')
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
/* Rich scenes retain the original JSON/text pipeline while dedicating
   substantially more screen area and keyframed motion to illustrations. */
.scene.rich .visual-stage{{position:absolute;left:{65 if vertical else 165}px;right:{65 if vertical else 165}px;top:{345 if vertical else 145}px;height:{850 if vertical else 615}px;pointer-events:none;z-index:1}}
.scene.rich .visual-stage svg{{display:block;width:100%;height:100%;overflow:visible}}
.scene.rich .decor{{opacity:.10}}
.scene.rich .story{{position:absolute;left:{95 if vertical else 165}px;right:{95 if vertical else 165}px;bottom:{280 if vertical else 145}px;margin:0;max-width:none}}
.scene.rich .index{{display:none}}
.scene.rich h1{{font-size:{77 if vertical else 72}px;letter-spacing:-1px;margin:0 0 14px;line-height:1.04;text-shadow:0 3px 20px #071423}}
.scene.rich .subtitle{{font-size:{30 if vertical else 32}px;margin:0;line-height:1.25;text-shadow:0 2px 8px #071423}}
.scene.rich footer{{margin-top:auto}}
/* Beat strips appear only for new storyboards that explicitly request them.
   Each phrase has its own seekable GSAP enter/hold/exit timeline. */
.beat-stage{{position:absolute;z-index:5;left:{100 if vertical else 170}px;right:{100 if vertical else 170}px;top:{1240 if vertical else 640}px;height:{145 if vertical else 100}px;pointer-events:none}}
.beat-card{{position:absolute;inset:0;padding:{20 if vertical else 11}px {30 if vertical else 24}px;background:rgba(8,20,40,.92);border:2px solid rgba(107,206,246,.53);border-radius:20px;box-shadow:0 22px 55px rgba(0,0,0,.22);color:#F2F9FF;display:flex;align-items:center;gap:25px;opacity:0;visibility:hidden}}
.beat-number{{flex:none;font-size:{25 if vertical else 22}px;font-weight:800;color:#6BD9FF;letter-spacing:2px}}
.beat-line{{font-size:{39 if vertical else 31}px;font-weight:800;line-height:1.1;letter-spacing:.2px;overflow-wrap:anywhere}}
.beat-track{{position:absolute;bottom:0;left:18px;right:18px;height:6px;background:rgba(115,220,255,.17);border-radius:5px;overflow:hidden}}
.beat-fill{{display:block;width:100%;height:100%;background:#72D9FD;transform-origin:left center;transform:scaleX(0)}}
.scene-veil{{position:absolute;inset:0;background:#080E19;z-index:9;pointer-events:none;opacity:0}}

</style></head>
<body><div id="root" data-composition-id="aether-{format_name}" data-start="0" data-width="{width}" data-height="{height}" data-duration="{total:g}" data-fps="{fps}">
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


def write_project(plan, destination, with_voice=False, voice='af_heart', fps=30):
    # Plan validation occurs before any file, subprocess, or network activity.
    validate_plan(plan)
    destination = Path(destination)
    voice_dir = destination / 'assets' / 'voice'
    voices = prepare_audio(plan, voice_dir, voice=voice, generate=with_voice)
    for name in FORMATS:
        dirpath = destination / name
        dirpath.mkdir(parents=True, exist_ok=True)
        (dirpath / 'index.html').write_text(build_html(plan, name, voices, fps=fps), encoding='utf-8')
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
    out = write_project(plan, args.out_dir, args.tts, args.voice, fps=args.fps)
    print('HyperFrames compositions created:', out)
    if args.render:
        cli = hyperframes_cli()
        for fmt in FORMATS:
            bundle_gsap(out / fmt)
        exports = Path(args.output)
        exports.mkdir(parents=True, exist_ok=True)
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
