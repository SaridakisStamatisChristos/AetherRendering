#!/usr/bin/env python3
"""Original, deterministic 15-second score shared unchanged between both renderers."""
from pathlib import Path
import math, struct, wave
RATE=24000
SECONDS=15
OUT=Path(__file__).resolve().parents[1]/"public"/"creative-score.wav"
OUT.parent.mkdir(parents=True, exist_ok=True)
notes=[(9.45,329.63),(10.35,392.0),(11.25,493.88),(12.20,587.33),(13.15,659.25)]
def tone(freq,t):
    return math.sin(2*math.pi*freq*t)
with wave.open(str(OUT),"wb") as file:
    file.setnchannels(1);file.setsampwidth(2);file.setframerate(RATE)
    chunk=bytearray()
    for k in range(SECONDS*RATE):
        t=k/RATE
        fade=min(1.,t/.65,max(0.,(SECONDS-t)/1.0))
        drone=.090*tone(65.41,t)+.052*tone(98.0,t)+.033*tone(130.81,t)
        wind=.022*tone(1.3,t)*tone(173,t)
        heartbeat=0.
        for onset in (4.95,5.6,6.35,7.12,8.04,9.1):
            d=t-onset
            if 0<=d<.22:heartbeat+=.29*math.exp(-28*d)*(tone(87,d)+.26*tone(175,d))
        shimmer=0.
        for onset in (5.3,6.6,7.85,9.15):
            d=t-onset
            if 0<=d<.72:shimmer+=.07*(1-d/.72)**2*tone(480+130*d,d)
        choir=0.
        if t>=9.1: 
            rise=min(1.,(t-9.1)/2.5)
            choir=rise*(.065*tone(196,t)+.04*tone(261.63,t)+.04*tone(392,t))
        melody=0.
        for onset,freq in notes:
            d=t-onset
            if 0<=d<1.7:
                env=(1-math.exp(-25*d))*math.exp(-1.7*d)
                melody+=.085*env*(tone(freq,d)+.17*tone(2*freq,d))
        val=max(-.94,min(.94,fade*(drone+wind+heartbeat+shimmer+choir+melody)))
        chunk+=struct.pack("<h",int(val*32767))
        if len(chunk)>100000:
            file.writeframesraw(chunk);chunk.clear()
    if chunk:file.writeframesraw(chunk)
print(OUT)
