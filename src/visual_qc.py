#!/usr/bin/env python3
"""Generate visual contact-sheet evidence and measure within-scene frame changes.

Reuses the actual MP4 rather than evaluating source SVG or simulated animation.
Requires ffmpeg, Pillow and the compiled resolved_plan.json. No model/API calls.
"""
import argparse
import io
import json
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw, ImageFont, ImageStat, ImageChops

FRAME_SIZE = (270, 480)
FRACTIONS = (0.17, 0.51, 0.83)


def sample_frame(path, timestamp):
    command = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-ss',
               f'{timestamp:.4f}', '-i', str(path), '-frames:v', '1',
               '-vf', f'scale={FRAME_SIZE[0]}:{FRAME_SIZE[1]}:flags=bicubic',
               '-f', 'image2pipe', '-vcodec', 'png', '-']
    data = subprocess.run(command, check=True, capture_output=True).stdout
    if not data:
        raise RuntimeError(f'ffmpeg returned no frame at {timestamp:.3f}s')
    with Image.open(io.BytesIO(data)) as image:
        return image.convert('RGB')


def change_score(first, second):
    """Mean channel delta in 0–255 pixel units, not percentage or SSIM."""
    if first.size != second.size:
        raise ValueError('Frame dimensions differ')
    differences = ImageChops.difference(first.convert('RGB'),second.convert('RGB'))
    return round(sum(ImageStat.Stat(differences).mean)/3,3)


def examine(video, resolved_plan, output, min_change=0.40):
    scenes = resolved_plan.get('scenes', [])
    if len(scenes) < 2:
        raise ValueError('At least two scenes required for contact-sheet QA')
    target = Path(output)
    target.mkdir(parents=True, exist_ok=True)
    margin, space, header = 16, 12, 36
    width = margin*2 + len(FRACTIONS)*FRAME_SIZE[0] + (len(FRACTIONS)-1)*space
    row_height = FRAME_SIZE[1] + header + space
    sheet = Image.new('RGB',(width, margin*2 + row_height*len(scenes)), '#0B1425')
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=18)
    offset = 0.0
    changes = []
    for i, scene in enumerate(scenes):
        duration = float(scene['duration'])
        if duration <= 0:
            raise ValueError('Invalid scene duration')
        frames = [sample_frame(video, offset+duration*f) for f in FRACTIONS]
        diffs = [change_score(frames[0],frames[1]),change_score(frames[1],frames[2])]
        entry = {'scene':i+1, 'title':scene['title'], 'duration_seconds':duration,
                 'frames_seconds':[round(offset+duration*f,3) for f in FRACTIONS],
                 'mean_rgb_deltas':diffs,'motion_gate_pass':max(diffs)>=min_change}
        changes.append(entry)
        for j, frame in enumerate(frames):
            x=margin+j*(FRAME_SIZE[0]+space)
            y=margin+i*row_height+header
            sheet.paste(frame,(x,y))
            draw.text((x,y-header+7), f'{i+1:02d} - {int(FRACTIONS[j]*100)}% - {scene["title"][:17]}',
                      fill='#DDEFFD',font=font)
        offset += duration
    contact_sheet = target/'contact_sheet.png'
    sheet.save(contact_sheet)
    report={'input_video':str(video),'sampled_frames':len(scenes)*len(FRACTIONS),
            'min_change_gate_rgb':min_change,'scenes':changes,
            'all_scenes_change':all(item['motion_gate_pass'] for item in changes),
            'contact_sheet':str(contact_sheet)}
    (target/'visual_qc.json').write_text(json.dumps(report,indent=2)+'\n')
    for entry in changes:
        print(f"SCENE {entry['scene']} ({entry['title']}): RGB deltas {entry['mean_rgb_deltas']}")
    if not report['all_scenes_change']:
        raise RuntimeError('At least one scene has almost no frame-to-frame visual change')
    return report


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--video',required=True)
    p.add_argument('--resolved-plan',required=True)
    p.add_argument('--output',required=True)
    p.add_argument('--min-change',type=float,default=0.40)
    args=p.parse_args()
    plan=json.loads(Path(args.resolved_plan).read_text(encoding='utf-8'))
    examine(Path(args.video),plan,args.output,args.min_change)


if __name__=='__main__':
    main()
