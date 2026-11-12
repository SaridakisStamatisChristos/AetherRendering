#!/usr/bin/env python3
"""Optional quality narration generation; NOT run in the demo environment.

Install in an environment with Python 3.10-3.13 and dependencies:
  pip install kokoro soundfile numpy
  # plus appropriate runtime dependencies / model downloads

Run:
  python src/kokoro_voice.py --voice af_heart
  python src/render.py --voice-dir voice_wavs
"""
import argparse
import json
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline

ROOT=Path(__file__).resolve().parent.parent

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--project',default=str(ROOT/'project.json'))
    p.add_argument('--out-dir',default=str(ROOT/'voice_wavs'))
    p.add_argument('--voice',default='af_heart')
    p.add_argument('--lang-code',default='a')
    p.add_argument('--speed',type=float,default=1.0)
    args=p.parse_args()
    scenes=json.loads(Path(args.project).read_text())['scenes']
    out=Path(args.out_dir)
    out.mkdir(parents=True,exist_ok=True)
    pipeline=KPipeline(lang_code=args.lang_code)
    for i,s in enumerate(scenes):
        chunks=[]
        for result in pipeline(s['narration'],voice=args.voice,speed=args.speed):
            chunks.append(np.asarray(result.audio,dtype=np.float32))
        if not chunks:
            raise RuntimeError(f'No voice generated for scene {i}')
        audio=np.concatenate(chunks)
        sf.write(out/f'{i:03d}.wav',audio,24000,subtype='PCM_16')
        print(f'Wrote {i:03d}.wav ({len(audio)/24000:.2f}s)')

if __name__=='__main__':
    main()
