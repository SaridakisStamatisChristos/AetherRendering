"""Create an original, deterministic 10-second ambient soundtrack using stdlib only."""
import math
import pathlib
import struct
import wave

RATE = 24000
DURATION = 10
OUT = pathlib.Path(__file__).resolve().parents[1] / "public" / "soundtrack.wav"
OUT.parent.mkdir(parents=True, exist_ok=True)
with wave.open(str(OUT), "wb") as wav:
    wav.setnchannels(1)
    wav.setsampwidth(2)
    wav.setframerate(RATE)
    buf = bytearray()
    for n in range(RATE * DURATION):
        t = n / RATE
        fade = min(1.0, t / 0.6, (DURATION - t) / 0.7)
        drone = 0.085 * math.sin(2 * math.pi * 74 * t) + 0.045 * math.sin(2 * math.pi * 111 * t)
        hum = 0.025 * math.sin(2 * math.pi * 185 * t) * (0.65 + 0.35 * math.sin(2 * math.pi * 0.35 * t))
        chirp = 0
        for start in (3.75, 4.15, 4.55, 6.9):
            dt = t - start
            if 0 <= dt < 0.32:
                env = (1 - dt / 0.32) ** 1.8
                chirp += 0.18 * env * math.sin(2 * math.pi * (580 * dt + 210 * dt * dt))
        v = max(-1.0, min(1.0, fade * (drone + hum + chirp)))
        buf.extend(struct.pack('<h', int(v * 32767)))
    wav.writeframes(buf)
print(f"Generated {OUT} ({DURATION}s, mono, 24kHz)")
