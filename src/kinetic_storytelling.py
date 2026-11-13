"""Safe, seekable multi-beat editorial overlays for narrated animation scenes.

Every visual event is a GSAP timeline operation placed at absolute media time.
No wall-clock animation, freeform JS, external assets or network requests.
"""
import html

MAX_BEATS = 4
MAX_BEAT_CHARS = 66


def validate_beats(beats, scene_index):
    """None or 2–4 concise phrases; reject executable/user-controlled structure."""
    if beats is None:
        return
    if not isinstance(beats, list) or not 2 <= len(beats) <= MAX_BEATS:
        raise ValueError(f"Scene {scene_index}: beats must be 2–4 phrases")
    for phrase in beats:
        if (not isinstance(phrase, str) or not phrase.strip()
                or len(phrase) > MAX_BEAT_CHARS or any(ord(c) < 32 for c in phrase)):
            raise ValueError(f"Scene {scene_index}: invalid beat phrase")


def compile_beats(scene, scene_index, start, duration):
    """Return (HTML, GSAP statements) for 2–4 timed, independently animated cards.

    A beat occupies one equal fraction of the REAL scene duration, which follows
    measured Kokoro speech. This is scene-relative sequencing, NOT word-level
    speech alignment.
    """
    phrases = scene.get("beats")
    if phrases is None:
        return "", ""
    validate_beats(phrases, scene_index)
    n = len(phrases)
    slot = duration / n
    html_cards = []
    motions = []
    for j, phrase in enumerate(phrases):
        identifier = f"beat-{scene_index}-{j}"
        progress = f"beat-progress-{scene_index}-{j}"
        html_cards.append(
            f'<div id="{identifier}" class="beat-card" data-beat-index="{j+1}">'
            f'<span class="beat-number">{j+1:02d} / {n:02d}</span>'
            f'<span class="beat-line">{html.escape(phrase, quote=True)}</span>'
            f'<span class="beat-track"><span id="{progress}" class="beat-fill"></span></span>'
            '</div>')
        t0 = start + j * slot + min(.09, .08 * slot)
        reveal = min(.30, slot * .25)
        hide = min(.23, slot * .20)
        t1 = start + (j + 1) * slot - hide - .04
        if t1 <= t0 + reveal:
            raise ValueError(f"Scene {scene_index}: beat duration too short")
        motions.append(
            f"tl.fromTo('#{identifier}',"
            "{autoAlpha:0,y:42,scale:0.96},"
            f"{{autoAlpha:1,y:0,scale:1,duration:{reveal:.3f},ease:'power3.out'}},"
            f"{t0:.3f});"
        )
        motions.append(
            f"tl.fromTo('#{progress}',"
            "{scaleX:0},"
            f"{{scaleX:1,duration:{max(.10, t1 - t0):.3f},ease:'none'}},"
            f"{t0:.3f});"
        )
        motions.append(
            f"tl.to('#{identifier}',"
            f"{{autoAlpha:0,y:-30,duration:{hide:.3f},ease:'power2.in'}},"
            f"{t1:.3f});"
        )
    return '<div class="beat-stage">' + ''.join(html_cards) + '</div>', '\n'.join(motions)


def visual_follow_through(scene, scene_index, start, duration):
    """Secondary vector motion AFTER each primary scene illustration resolves.

    These are restrained motions that carry animation through the latter part
    of a shot so the picture does not freeze immediately after its entrance.
    """
    config = scene.get("visual")
    if not config:
        return ""
    kind = config["type"]
    start_late = start + duration * .69
    remaining = duration * .22
    tweens = []
    if kind == "spectrum":
        for j in range(6):
            delta = -10 if j % 2 else 10
            tweens.append(
                f"tl.to('#v-{scene_index}-ray-{j}',"
                f"{{y:{delta},opacity:0.85,duration:{remaining:.3f},ease:'sine.inOut'}},"
                f"{start_late:.3f});"
            )
    elif kind == "particles":
        for j in range(21):
            delta = -14 - (j % 4) * 6
            tweens.append(
                f"tl.to('#v-{scene_index}-particle-{j}',"
                f"{{y:{delta},x:{(j%3-1)*9},duration:{duration*.46:.3f},ease:'sine.inOut'}},"
                f"{start + duration*.46:.3f});"
            )
    elif kind == "orbit":
        for j in range(5):
            tweens.append(
                f"tl.to('#v-{scene_index}-dot-{j}',"
                f"{{x:{(j-2)*19},y:{(-1 if j%2 else 1)*27},"
                f"duration:{duration*.37:.3f},ease:'sine.inOut'}},"
                f"{start + duration*.53:.3f});"
            )
    elif kind == "comparison":
        count = len(config.get("labels", ["FIRST", "SECOND", "THIRD"]))
        for j in range(count):
            tweens.append(
                f"tl.to('#v-{scene_index}-bar-{j}',"
                f"{{scaleY:{0.96 + j*.012:.3f},duration:{remaining:.3f},ease:'sine.inOut'}},"
                f"{start_late:.3f});"
            )
    elif kind == "horizon":
        tweens.append(
            f"tl.to('#v-{scene_index}-sun',"
            f"{{scale:1.07,transformOrigin:'center center',duration:{duration*.43:.3f},"
            f"ease:'sine.inOut'}},{start + duration*.54:.3f});"
        )
    return '\n'.join(tweens)


def compile_cut(scene_index, start, duration):
    """Short fade-to-background at each end, without cross-clip overlap."""
    fade_in = min(.18, duration * .07)
    fade_out = min(.24, duration * .09)
    return (
        f"tl.fromTo('#scene-veil-{scene_index}',"
        f"{{opacity:1}},{{opacity:0,duration:{fade_in:.3f},ease:'power1.out'}},"
        f"{start:.3f});\n"
        f"tl.fromTo('#scene-veil-{scene_index}',"
        f"{{opacity:0}},{{opacity:1,duration:{fade_out:.3f},ease:'power1.in'}},"
        f"{start + duration - fade_out:.3f});"
    )
