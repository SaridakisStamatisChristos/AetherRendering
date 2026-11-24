#!/usr/bin/env python3
"""A deterministic, seek-safe, native HyperFrames/GSAP version of the Remotion robot test.

Produces the same canvas, 240 frames, drawing geometry, caption timing and WAV as
Remotion's original 10-second test. No Remotion package is imported or used.
"""
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from hyperframes_pipeline import bundle_gsap


def static_scene():
    stars = '\n'.join(
        f'<circle cx="{(i*179+53)%1280}" cy="{(i*79+29)%370}" r="{2 if i%4==0 else 1}" '
        f'fill="#b7ecff" opacity="{.25+((i*7)%6)/12:.4f}"/>'
        for i in range(36)
    )
    distant = []
    for i in range(14):
        x = i*113-80
        h = 150+((i*87)%245)
        windows = ''.join(
            f'<rect x="{x+14+(j%3)*25}" y="{535-h+(j//3)*34}" width="9" height="14" '
            f'fill="#bfeeff" opacity="{.42 if (i+j)%5==0 else .06}"/>'
            for j in range(9)
        )
        distant.append(f'<g><rect x="{x}" y="{525-h}" width="99" height="{h+80}" '
                       f'fill="{("#0a1425" if i%3==0 else "#0c1e2d")}"/>{windows}</g>')
    nearer = []
    for i in range(8):
        x = i*199 - 115
        h = 85+((i*61)%185)
        nearer.append(f'<rect x="{x}" y="{548-h}" width="173" height="{h+65}" fill="#122a37"/>')
    template = (HERE / 'scene.template.html').read_text(encoding='utf-8')
    return (template.replace('__STARS__', stars)
            .replace('__DISTANT__', '\n'.join(distant))
            .replace('__NEARER__', '\n'.join(nearer)))


def main():
    project = ROOT / 'build' / 'compare-aether' / 'composition'
    project.mkdir(parents=True, exist_ok=True)
    audio = HERE / 'public' / 'soundtrack.wav'
    if not audio.is_file():
        raise RuntimeError('Create the matching soundtrack first: python3 experiments/render-compare/scripts/make_audio.py')
    (project / 'index.html').write_text(static_scene(), encoding='utf-8')
    bundle_gsap(project)
    voice = project / 'assets' / 'voice'
    voice.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(audio, voice / 'soundtrack.wav')
    (project / 'hyperframes.json').write_text('''{
  "registry": "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry",
  "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"}
}\n''', encoding='utf-8')
    print('Created seek-safe native HyperFrames composition:', project)
    print('Uses pinned local GSAP + the exact deterministic soundtrack from Remotion.')


if __name__ == '__main__':
    main()
