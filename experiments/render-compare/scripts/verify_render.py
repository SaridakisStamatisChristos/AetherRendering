#!/usr/bin/env python3
"""Check the real HyperFrames export and produce comparable benchmark metrics."""
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'build' / 'compare-aether' / 'exports'
VIDEO = OUT / 'aether.mp4'
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from hyperframes_pipeline import verify_video


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def main():
    if not VIDEO.is_file():
        raise AssertionError('MP4 missing; native HyperFrames render did not complete')
    checked = verify_video(VIDEO, 1280, 720)
    data = json.loads(run('ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(VIDEO)))
    v = next(s for s in data['streams'] if s['codec_type'] == 'video')
    a = next(s for s in data['streams'] if s['codec_type'] == 'audio')
    duration = float(data['format']['duration'])
    assert v['codec_name'] == 'h264', v
    assert v.get('r_frame_rate') == '24/1', v
    assert a['codec_name'] == 'aac', a
    assert 9.9 <= duration <= 10.1, duration
    # ffprobe's exact frame count should work with H.264 output in mp4 container.
    count = int(run('ffprobe','-v','error','-select_streams','v:0','-count_frames',
                    '-show_entries','stream=nb_read_frames', '-of', 'csv=p=0', str(VIDEO)).strip())
    assert count == 240, f'expected 240 video frames, got {count}'
    start = float((OUT / 'render_start').read_text())
    end = float((OUT / 'render_end').read_text())
    wall = round(end-start, 3)
    assert 0 < wall < 1200
    baseline = json.loads((HERE / 'remotion_baseline.json').read_text())
    measured = {
        'engine': 'AetherRendering / native HyperFrames 0.9.37 + GSAP 3.14.2',
        'ok': True,
        'full_decode': bool(checked['full_decode']),
        'audio_verified': bool(checked['audio_verified']),
        'duration_seconds': duration,
        'resolution': '1280x720',
        'fps': v['r_frame_rate'],
        'frames': count,
        'video_codec': v['codec_name'],
        'audio_codec': a['codec_name'],
        'audio_mean_volume_db': checked['mean_volume_db'],
        'bytes': VIDEO.stat().st_size,
        'wall_seconds': wall,
    }
    (OUT/'metrics.json').write_text(json.dumps(measured, indent=2)+'\n')
    comparison = {
        'same_story': True,
        'same_geometry': True,
        'same_soundtrack': True,
        'same_resolution_fps_duration': True,
        'host': 'GitHub Actions ubuntu-latest (separate runs; actual underlying CPU may differ)',
        'render_timing_excludes_dependency_installation': True,
        'render_engine_baseline': 'Remotion 4.0.546',
        'remotion': baseline,
        'aetherrendering': measured,
        'aether_to_remotion_render_time_ratio': round(wall/baseline['wall_seconds'], 3),
        'aether_to_remotion_file_size_ratio': round(VIDEO.stat().st_size/baseline['bytes'], 3),
        'notes': [
            'Timings are preliminary wall-clock times on separate GitHub Actions runners, not a controlled hardware benchmark.',
            'The comparison scene is a purpose-built native HyperFrames composition, not the general AI Director storyboard output.',
            'The ambient soundtrack is shared verbatim; no voice generation time is included.',
            'Output file size is codec/preset/content dependent and is not a standalone visual-quality score.',
        ]
    }
    (OUT/'comparison.json').write_text(json.dumps(comparison, indent=2)+'\n')
    print(json.dumps(comparison, indent=2))


if __name__ == '__main__':
    main()
