#!/usr/bin/env python3
"""A self-contained FFmpeg/Pillow short-form video renderer.

Demo narration uses local eSpeak only when explicitly enabled in the JSON.
For production pass --voice-dir with one externally generated WAV per scene,
numbered 000.wav, 001.wav, ...; or use --silent.
"""
from __future__ import annotations
import argparse
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import wave

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONT_BOLD = next((p for p in [
    '/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf'] if Path(p).exists()), None)
FONT_REG = next((p for p in [
    '/usr/share/fonts/opentype/inter/Inter-Regular.otf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'] if Path(p).exists()), None)


def run(cmd, *, capture=False):
    p = subprocess.run([str(x) for x in cmd], capture_output=capture, text=capture)
    if p.returncode:
        if capture:
            print(p.stdout, p.stderr, file=sys.stderr)
        raise RuntimeError(f'Command failed ({p.returncode}): {cmd}')
    return p.stdout if capture else None


def ffprobe(path):
    return json.loads(run(['ffprobe', '-v', 'error', '-show_streams',
                           '-show_format', '-of', 'json', path], capture=True))


def font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, max(10, int(size))) if FONT_BOLD else ImageFont.load_default()


def hx(c):
    return tuple(int(c[i:i+2], 16) for i in (1, 3, 5))


def fit_lines(draw, text, f, width):
    lines, line = [], ''
    for word in text.split():
        test = (line + ' ' + word).strip()
        if draw.textbbox((0,0), test, font=f)[2] > width and line:
            lines.append(line)
            line = word
        else:
            line = test
    if line:
        lines.append(line)
    return lines


def rr(d, rect, fill, rad=20, outline=None, width=2):
    d.rounded_rectangle(tuple(map(int, rect)), radius=int(rad), fill=fill, outline=outline, width=width)


def scene_image(s, idx, total, width, height, brand, accent):
    im = Image.new('RGB', (width, height), '#0C131D')
    d = ImageDraw.Draw(im)
    scale = width / (1080 if height > width else 1920)
    portrait = height > width
    aw, ah = width, height
    accent_rgb = hx(accent)
    # Deliberately understated dark editorial palette, no purple gradients/orbs.
    for y in range(0, height, max(2, int(6*scale))):
        t = y / height
        d.rectangle((0,y,width,y+max(2,int(6*scale))), fill=(int(11+7*t), int(18+10*t), int(28+12*t)))
    grid = max(50,int(88*scale))
    for x in range(grid//2,width,grid):
        d.line((x,0,x,height), fill='#182331', width=max(1,int(scale)))
    for y in range(grid//2,height,grid):
        d.line((0,y,width,y), fill='#182331', width=max(1,int(scale)))

    margin = int((82 if portrait else 105) * scale)
    tagf = font(31*scale, True)
    d.text((margin, int(95*scale)), brand, fill=accent_rgb, font=tagf)
    d.text((width-margin-int(185*scale),int(95*scale)), f'{idx+1:02d} / {total:02d}', fill='#D0D8E2', font=font(29*scale, True))
    d.line((margin,int(160*scale),width-margin,int(160*scale)),fill='#40505D',width=max(2,int(2*scale)))

    tx = margin
    ty = int((260 if portrait else 350)*scale)
    titlew = width - 2*margin if portrait else int(860*scale)
    titlesize = (76 if portrait else 86) * scale
    tf = font(titlesize,True)
    lines = fit_lines(d,s['title'],tf,titlew)
    for i,l in enumerate(lines):
        d.text((tx, ty+i*titlesize*1.10),l,fill='#F4FAFF',font=tf)
    st = ty + int((len(lines)*titlesize*1.2+40*scale))
    sf = font(38*scale if portrait else 37*scale)
    for j,line in enumerate(fit_lines(d,s['subtitle'],sf,titlew)):
        d.text((tx,st+j*47*scale), line,fill='#A9C0CE',font=sf)

    if portrait:
        left,right = margin,width-margin
        top,bottom=int(850*scale),int(1550*scale)
    else:
        left,right=int(1110*scale),width-margin
        top,bottom=int(310*scale),int(860*scale)
    rr(d,(left,top,right,bottom),'#142330',int(32*scale),outline='#36505B',width=max(2,int(3*scale)))
    bw = right-left
    bh = bottom-top
    cx = (left+right)//2
    cy = (top+bottom)//2
    minor = max(2,int(3*scale))
    f = font((34 if portrait else 30)*scale,True)
    vis = s.get('visual','script')
    if vis=='script':
        for j,frac in enumerate([.68,.83,.62,.77,.42]):
            y=top+int((.23+j*.13)*bh)
            rr(d,(left+.12*bw,y,left+(.12+frac*.76)*bw,y+max(8,int(21*scale))),accent if j==1 else '#57707D',10)
        d.text((left+.12*bw,top+.08*bh),'SCRIPT.md', fill=accent,font=f)
    elif vis=='storyboard':
        for j in range(3):
            xl=left+int((.10+j*.29)*bw)
            rr(d,(xl,top+.26*bh,xl+.24*bw,top+.68*bh),'#284150',int(16*scale),outline=accent if j==1 else '#48606E',width=minor)
            d.ellipse((xl+.07*bw,top+.35*bh,xl+.17*bw,top+.45*bh),fill=accent if j==1 else '#718997')
            d.text((xl+.06*bw,top+.77*bh),f'0{j+1}',fill='#D4E0EA',font=f)
    elif vis=='frames':
        for j in range(4):
            x=left+int((.08+j*.224)*bw)
            rr(d,(x,top+.30*bh,x+.17*bw,top+.66*bh),'#244353',int(11*scale),outline=accent if j==2 else '#607480',width=minor)
            d.line((x+.03*bw,top+.51*bh,x+.14*bw,top+.39*bh),fill=accent,width=int(5*scale))
        d.text((left+.10*bw,top+.12*bh),'30 FPS  /  H.264',fill=accent,font=f)
    elif vis=='wave':
        n=54
        for j in range(n):
            x=left+int((.07+.86*j/(n-1))*bw)
            a=abs(math.sin(j*.47)*math.sin(j*.18)+.26)
            half=int((.05+.25*a)*bh)
            d.line((x,cy-half,x,cy+half),fill=accent if j%3 else '#A9FFF0',width=max(3,int(6*scale)))
    elif vis=='captions':
        rr(d,(left+.07*bw,top+.30*bh,right-.07*bw,top+.70*bh),'#233947',int(16*scale))
        d.text((left+.13*bw,top+.38*bh),'STAY INSIDE',fill='#F6FBFF',font=font(50*scale,True))
        d.text((left+.13*bw,top+.52*bh),'SAFE ZONES',fill=accent,font=font(50*scale,True))
    elif vis=='aspect':
        rr(d,(left+.13*bw,top+.22*bh,left+.39*bw,top+.77*bh),'#284250',int(9*scale),outline=accent,width=minor)
        rr(d,(left+.49*bw,top+.33*bh,left+.91*bw,top+.62*bh),'#284250',int(9*scale),outline=accent,width=minor)
        d.text((left+.14*bw,top+.82*bh),'9:16',fill='#DDE8EE',font=f)
        d.text((left+.62*bw,top+.70*bh),'16:9',fill='#DDE8EE',font=f)
    elif vis=='export':
        rr(d,(left+.14*bw,top+.29*bh,right-.14*bw,top+.69*bh),'#213E49',int(20*scale))
        d.text((left+.23*bw,top+.40*bh),'FINAL.MP4',fill=accent,font=font(64*scale,True))
        d.text((left+.23*bw,top+.55*bh),'H.264  +  AAC',fill='#C5D8E3',font=f)
    elif vis=='checks':
        labels=['DIMENSIONS','AUDIO STREAM','DECODABLE']
        for j,label in enumerate(labels):
            y=top+(.25+j*.19)*bh
            d.ellipse((left+.11*bw,y,left+.17*bw,y+.075*bh),fill=accent)
            d.text((left+.21*bw,y-.012*bh),label,fill='#E1ECF3',font=f)
    else:
        d.ellipse((cx-.17*bw,cy-.17*bw,cx+.17*bw,cy+.17*bw),outline=accent,width=int(11*scale))
        d.polygon([(cx-.037*bw,cy-.09*bh),(cx-.037*bw,cy+.09*bh),(cx+.12*bw,cy)],fill=accent)
        d.text((left+.20*bw,top+.77*bh),'ACTUAL RENDER',fill='#DCECF3',font=f)
    # Footer and visible timeline progress
    track_y = height-int((125 if portrait else 88)*scale)
    rr(d,(margin,track_y,width-margin,track_y+int(9*scale)),'#2E4654',int(5*scale))
    rr(d,(margin,track_y,margin+(width-2*margin)*(idx+1)/total,track_y+int(9*scale)),accent,int(5*scale))
    d.text((margin,track_y+int(20*scale)),'RENDERED PROOF  •  NO CLOUD API',fill='#97AEBB',font=font(25*scale))
    return im


def make_voice(scene, idx, wav, voice_dir, silent, rate):
    if voice_dir:
        src=Path(voice_dir)/f'{idx:03d}.wav'
        if not src.is_file():
            raise FileNotFoundError(f'Missing {src}')
        shutil.copyfile(src,wav)
    elif not silent:
        if not shutil.which('espeak'):
            raise RuntimeError('espeak is not installed. Provide --voice-dir or --silent.')
        run(['espeak','-v','en-us','-s',str(rate),'-w',wav,scene['narration']])
    else:
        return 2.8
    return float(ffprobe(wav)['format']['duration'])


def concat_waves(wavs, out, durations):
    # Normalize sample rate/channels/format with FFmpeg and concatenate on the
    # decoded timeline. 0.12s pause is added after every scene.
    inputs=[]
    chains=[]
    for i,path in enumerate(wavs):
        inputs += ['-i',path]
        chains.append(f'[{i}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=mono,apad=pad_dur=0.12,atrim=0:{durations[i]:.4f},asetpts=PTS-STARTPTS[a{i}]')
    filt=';'.join(chains)+';' + ''.join(f'[a{i}]' for i in range(len(wavs)))+f'concat=n={len(wavs)}:v=0:a=1[outa]'
    run(['ffmpeg','-hide_banner','-loglevel','error','-y',*inputs,'-filter_complex',filt,'-map','[outa]', '-ar','48000','-ac','1','-c:a','pcm_s16le',out])


def render_clips(images, durations, target, resolution, fps, cache):
    w,h=resolution
    cache.mkdir(parents=True,exist_ok=True)
    clips=[]
    for i,(img,duration) in enumerate(zip(images,durations)):
        clip=cache/f'clip_{i:03d}.mp4'
        frames=int(math.ceil(duration*fps))
        # fade is real motion in addition to scene changes; positional graphic
        # content is generated specifically for each aspect ratio.
        vf=f"scale={w}:{h},format=yuv420p,fade=t=in:st=0:d=0.18,fade=t=out:st={max(.0,duration-.18):.3f}:d=0.18"
        run(['ffmpeg','-hide_banner','-loglevel','error','-y','-loop','1','-framerate',str(fps),'-i',img,
             '-vf',vf,'-frames:v',str(frames),'-r',str(fps),'-an',
             '-c:v','libx264','-preset','ultrafast','-crf','24','-pix_fmt','yuv420p',clip])
        clips.append(clip)
    concat=cache/'clips.txt'
    concat.write_text(''.join("file '"+str(p.resolve()).replace("'","'\\''")+"'\n" for p in clips))
    silent_video=cache/'silent.mp4'
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',concat,'-c','copy',silent_video])
    return silent_video


def verify(path,width,height,expected,need_audio):
    result=ffprobe(path)
    v=next((s for s in result['streams'] if s['codec_type']=='video'),None)
    a=next((s for s in result['streams'] if s['codec_type']=='audio'),None)
    checks={'mp4':result['format']['format_name'].find('mp4') >= 0,
            'h264':bool(v and v['codec_name']=='h264'),
            'dimensions':bool(v and v['width']==width and v['height']==height),
            'audio':not need_audio or bool(a and a['codec_name']=='aac'),
            'duration':abs(float(result['format']['duration'])-expected)<1.5}
    # Decode every frame and every audio packet: a metadata check is not enough.
    try:
        run(['ffmpeg','-hide_banner','-v','error','-xerror','-i',path,'-f','null','-'])
        checks['full_decode']=True
    except Exception:
        checks['full_decode']=False
    return {'file':str(path),'duration_sec':float(result['format']['duration']),
            'video_codec':v['codec_name'] if v else None,'width':v['width'] if v else None,
            'height':v['height'] if v else None,'fps':v['r_frame_rate'] if v else None,
            'audio_codec':a['codec_name'] if a else None,'checks':checks,'passed':all(checks.values())}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--project',default=str(ROOT/'project.json'))
    p.add_argument('--out-dir',default=str(ROOT/'output'))
    p.add_argument('--format',choices=['vertical','horizontal','both'],default='both')
    p.add_argument('--fps',type=int,default=30)
    p.add_argument('--voice-dir',help='Directory with 000.wav, 001.wav, ...')
    p.add_argument('--silent',action='store_true')
    p.add_argument('--preview',action='store_true',help='Half-resolution faster test')
    args=p.parse_args()
    if args.silent and args.voice_dir:
        p.error('--silent and --voice-dir are mutually exclusive')
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        p.error('ffmpeg and ffprobe are required')
    pr=json.loads(Path(args.project).read_text())
    scenes=pr['scenes']
    if not scenes or any(not s.get('title') or not s.get('narration') for s in scenes):
        p.error('Every scene must have title and narration')
    out=Path(args.out_dir).resolve()
    out.mkdir(parents=True,exist_ok=True)
    work=out/'_build'
    work.mkdir(exist_ok=True)
    wavs=[]; durations=[]
    for i,scene in enumerate(scenes):
        wav=work/f'{i:03d}.wav'
        audible=make_voice(scene,i,str(wav),args.voice_dir,args.silent,pr.get('voice',{}).get('rate_wpm',148))
        wavs.append(wav)
        durations.append(audible+0.12)
    audio=out/'voiceover.wav'
    if not args.silent:
        concat_waves(wavs,str(audio),durations)
    total_dur=sum(durations)
    outputs = []
    dims={'vertical':(1080,1920),'horizontal':(1920,1080)}
    if args.format!='both':
        dims={args.format:dims[args.format]}
    report={'project_name':pr.get('project_name'),'render_engine':'FFmpeg + Pillow',
            'voice_engine':'external-WAV' if args.voice_dir else ('none' if args.silent else 'eSpeak DEMO only'),
            'planned_duration_sec':round(total_dur,2),'scenes':len(scenes),'outputs':[]}
    start=0
    subtitles=[]
    def ts(x):
        ms=int(round(x*1000))
        return f'{ms//3600000:02d}:{(ms//60000)%60:02d}:{(ms//1000)%60:02d},{ms%1000:03d}'
    for i,(sc,dur) in enumerate(zip(scenes,durations)):
        subtitles.append(f'{i+1}\n{ts(start)} --> {ts(start+dur)}\n{sc["narration"]}\n')
        start+=dur
    (out/'captions.srt').write_text('\n'.join(subtitles),encoding='utf-8')
    thumb=None
    for kind,(W,H) in dims.items():
        w,h=(W//2,H//2) if args.preview else (W,H)
        frames_dir=work/kind/'stills'
        frames_dir.mkdir(parents=True,exist_ok=True)
        images=[]
        for i,sc in enumerate(scenes):
            im=scene_image(sc,i,len(scenes),w,h,pr.get('brand','VIDEO ENGINE'),pr.get('accent','#4CE0C1'))
            path=frames_dir/f'{i:03d}.png'
            im.save(path,optimize=True)
            images.append(path)
            if i==len(scenes)-1 and kind=='vertical':
                thumb=out/'thumbnail.png'
                im.save(thumb)
        raw=render_clips(images,durations,kind,(w,h),args.fps,work/kind/'clips')
        filename={'vertical':'instagram_1080x1920.mp4','horizontal':'youtube_1920x1080.mp4'}[kind]
        if args.preview: filename='preview_'+filename
        path=out/filename
        if args.silent:
            shutil.copyfile(raw,path)
        else:
            run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',raw,'-i',audio,
                 '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','160k',
                 '-af','loudnorm=I=-16:TP=-1.5:LRA=11','-movflags','+faststart','-shortest',path])
        report['outputs'].append(verify(path,w,h,total_dur,not args.silent))
        outputs.append(path)
    report['all_passed']=all(o['passed'] for o in report['outputs'])
    (out/'delivery_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    if not report['all_passed']:
        raise SystemExit(1)

if __name__=='__main__':
    main()
