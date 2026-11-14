"""Deterministic phrase subtitles based on measured scene speech durations.

Cues are approximate: durations are proportional to phrase word counts within
each Kokoro WAV. Do not describe these timings as forced-aligned or word-accurate.
"""
import re

def segments(text, max_words=7):
    words = re.findall(r'\S+', text)
    if not words:
        raise ValueError('Caption narration must contain words')
    out, current = [], []
    for word in words:
        current.append(word)
        if len(current) >= max_words or (len(current) >= 4 and word[-1:] in '.!?;:'):
            out.append(' '.join(current))
            current = []
    if current:
        out.append(' '.join(current))
    return out

def cues_for_plan(plan, voice_files):
    if len(plan['scenes']) != len(voice_files):
        raise ValueError('Narration scene count mismatch')
    cues, offset = [], 0.
    for i, (scene, (wav_name, scene_duration)) in enumerate(zip(plan['scenes'], voice_files)):
        duration = float(scene_duration)
        if not 0 < duration < 3600:
            raise ValueError('Invalid scene duration')
        # Speech WAV is measured before +0.35s tail; do not place text over the tail.
        speech = max(0.25, duration - 0.35) if wav_name else duration
        phrases = segments(scene['narration'])
        weights = [len(phrase.split()) for phrase in phrases]
        denom = sum(weights)
        used = 0
        for j, (phrase, weight) in enumerate(zip(phrases, weights)):
            start = offset + speech * used / denom
            used += weight
            end = offset + speech * used / denom
            cues.append({'scene': i, 'index': j, 'start': round(start,3),
                         'end': round(end,3), 'text': phrase})
        offset += duration
    return cues

def _srt_timestamp(seconds):
    ms = max(0, round(seconds * 1000))
    hours, ms = divmod(ms, 3_600_000)
    minutes, ms = divmod(ms, 60_000)
    secs, ms = divmod(ms, 1_000)
    return f'{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}'

def to_srt(cues):
    return ''.join(
        f"{index}\n{_srt_timestamp(cue['start'])} --> {_srt_timestamp(cue['end'])}\n{cue['text']}\n\n"
        for index,cue in enumerate(cues,1)
    )
