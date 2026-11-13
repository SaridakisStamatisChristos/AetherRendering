"""Reusable deterministic, SVG-based visual shot templates for AetherRendering.

Each visual is ordinary SVG/CSS and a set of paused GSAP timeline tweens.
All animated properties depend on absolute composition time; there are no
wall-clock timers, JavaScript eval, remote media, or user-authored code.
"""
import html
import math

VISUAL_TYPES = frozenset({"spectrum", "particles", "orbit", "comparison", "horizon"})


def _tween(selector, source, dest, at):
    """Build a controlled GSAP tween; callers only pass trusted constants."""
    return f"tl.fromTo('{selector}',{source},{dest},{at:.3f});"


def _svg(body, scene_index):
    return (f'<div id="visual-stage-{scene_index}" class="visual-stage" aria-hidden="true">'
            f'<svg viewBox="0 0 1000 620" role="img" xmlns="http://www.w3.org/2000/svg">'
            f'{body}</svg></div>')


def visual_scene(scene, index, start, seconds):
    """Return HTML stage and absolute GSAP timeline commands for an optional visual.

    The five templates deliberately represent reusable visual metaphors:
    spectrum/prism, floating particles, orbital paths, comparison bars and
    horizon/setting light. No image generation or additional model is required.
    """
    config = scene.get("visual")
    if config is None:
        return "", ""
    mode = config["type"]
    end = start + seconds
    a = lambda factor: start + seconds * factor
    actions = [
        _tween(f"#visual-stage-{index}",
               "{opacity:0,scale:0.94}", "{opacity:1,scale:1,duration:0.60,ease:'power2.out'}", a(0.04)),
        _tween(f"#visual-stage-{index} svg",
               "{x:-14}", f"{{x:18,duration:{seconds:.3f},ease:'none'}}", start),
    ]
    base = (
        f'<defs><linearGradient id="sky-{index}" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#122750"/><stop offset="0.6" stop-color="#2458A1"/>'
        '<stop offset="1" stop-color="#4AADE0"/></linearGradient>'
        f'<linearGradient id="dusk-{index}" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#141739"/><stop offset=".55" stop-color="#D46271"/>'
        '<stop offset="1" stop-color="#F9AC58"/></linearGradient>'
        f'<linearGradient id="prism-{index}" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#EDF7FF" stop-opacity=".85"/>'
        '<stop offset="1" stop-color="#729DC3" stop-opacity=".2"/></linearGradient></defs>'
    )
    if mode == "spectrum":
        rays = []
        for n, color in enumerate(("#ED667A", "#FFB651", "#F8E681", "#69DBBC", "#53A7FF", "#B58BFF")):
            y = 220 + n * 42
            rays.append(f'<line id="v-{index}-ray-{n}" x1="570" y1="310" x2="925" y2="{y}" '
                        f'stroke="{color}" stroke-width="10" stroke-linecap="round" opacity=".95"/>')
            actions.append(_tween(f"#v-{index}-ray-{n}", "{opacity:0,scaleX:0}",
                                  "{opacity:0.95,scaleX:1,transformOrigin:'left center',duration:0.7,ease:'power2.out'}",
                                  a(0.30 + n * 0.06)))
        body = (base + '<circle cx="510" cy="310" r="245" fill="#16305D" opacity=".23"/>'
                f'<line id="v-{index}-incoming" x1="65" y1="308" x2="445" y2="308" '
                'stroke="#F0F6FF" stroke-width="18" stroke-linecap="round"/>'
                f'<polygon points="450,170 630,310 450,450" fill="url(#prism-{index})" '
                'stroke="#C1EAFB" stroke-width="5"/>'
                + "".join(rays)
                + '<text x="95" y="265" fill="#D6EAFF" font-size="29" font-weight="700">WHITE LIGHT</text>'
                '<text x="708" y="528" fill="#D6EAFF" font-size="29" font-weight="700">COLORS</text>')
        actions.append(_tween(f"#v-{index}-incoming", "{opacity:0,scaleX:0}",
                              "{opacity:1,scaleX:1,transformOrigin:'left center',duration:0.65}", a(0.12)))
    elif mode == "particles":
        molecules = []
        for n in range(21):
            x = 170 + (n * 173) % 680
            y = 105 + (n * 109) % 370
            size = 6 + n % 5
            molecules.append(f'<circle id="v-{index}-particle-{n}" cx="{x}" cy="{y}" '
                             f'r="{size}" fill="#93D4F5" opacity=".65"/>')
            actions.append(_tween(f"#v-{index}-particle-{n}", "{opacity:0,scale:0.25}",
                                  f"{{opacity:0.75,scale:1,duration:0.48,ease:'power2.out'}}",
                                  a(0.10 + (n % 8) * 0.035)))
        scatter = []
        for n, angle in enumerate((0, 50, 100, 160, 220, 285, 325)):
            radians = math.radians(angle)
            x2, y2 = 505 + 260 * math.cos(radians), 300 + 210 * math.sin(radians)
            scatter.append(f'<line id="v-{index}-scatter-{n}" x1="505" y1="300" '
                           f'x2="{x2:.1f}" y2="{y2:.1f}" stroke="#68BAFF" stroke-width="8" '
                           'stroke-linecap="round" opacity=".85"/>')
            actions.append(_tween(f"#v-{index}-scatter-{n}", "{opacity:0,scaleX:0,scaleY:0}",
                                  "{opacity:0.85,scaleX:1,scaleY:1,transformOrigin:'center center',duration:0.65}",
                                  a(0.45 + n * 0.03)))
        body = (base + '<rect x="30" y="30" width="940" height="540" rx="42" fill="#142B55" opacity=".55"/>'
                + "".join(molecules)
                + f'<line id="v-{index}-beam" x1="110" y1="300" x2="505" y2="300" '
                  'stroke="#F5F5E3" stroke-width="16" stroke-linecap="round"/>'
                + "".join(scatter)
                + '<text x="110" y="475" fill="#D5E7FF" font-size="29" font-weight="700">LIGHT MEETS AIR</text>')
        actions.append(_tween(f"#v-{index}-beam", "{opacity:0,scaleX:0}",
                              "{opacity:1,scaleX:1,transformOrigin:'left center',duration:0.8}", a(0.19)))
    elif mode == "orbit":
        rings = "".join(f'<ellipse rx="{r}" ry="{int(r*.48)}" cx="500" cy="300" fill="none" '
                        f'stroke="#74C1F6" stroke-width="3" opacity="{0.4 + n*.13:.2f}"/>'
                        for n, r in enumerate((215, 285, 365)))
        dots = []
        for n, color in enumerate(("#59B1FF", "#72D4FF", "#F1F9FF", "#B8DCFF", "#79BFFF")):
            x = 205 + n * 145
            y = 235 + (n % 2) * 140
            dots.append(f'<circle id="v-{index}-dot-{n}" cx="{x}" cy="{y}" r="{19+n%3*7}" '
                        f'fill="{color}"/>')
            actions.append(_tween(f"#v-{index}-dot-{n}", "{opacity:0,scale:0.2}",
                                  "{opacity:1,scale:1,duration:0.5}", a(0.17+n*.10)))
        body = (base + f'<g id="v-{index}-rings">{rings}</g>'
                '<circle cx="500" cy="300" r="132" fill="#1E5B9D" stroke="#79D6FD" stroke-width="6"/>'
                '<path d="M400 300 Q480 205 570 286 Q530 375 421 371" fill="#82D4EF" opacity=".8"/>'
                '<path d="M540 205 Q580 250 610 322 L565 345 526 297Z" fill="#8CC4CD" opacity=".65"/>'
                + "".join(dots)
                + '<text x="340" y="520" fill="#D6EAFF" font-size="30" font-weight="700">IN EVERY DIRECTION</text>')
        actions.append(_tween(f"#v-{index}-rings", "{rotation:-18}",
                              f"{{rotation:18,transformOrigin:'50% 50%',duration:{seconds:.3f},ease:'none'}}", start))
    elif mode == "comparison":
        labels = config.get("labels", ["FIRST", "SECOND", "THIRD"])
        values = config.get("values", [0.5, 0.9, 0.65])
        cols = ("#AB8FFB", "#5CBEFF", "#FEAB73", "#6BD5B9")
        bars = []
        for n, (label, value) in enumerate(zip(labels, values)):
            x = 115 + n * 210
            height = 55 + 325 * value
            y = 475 - height
            bars.append(f'<rect id="v-{index}-bar-{n}" x="{x}" y="{y:.1f}" width="134" '
                        f'height="{height:.1f}" rx="18" fill="{cols[n]}"/>'
                        f'<text x="{x+67}" y="530" text-anchor="middle" font-size="29" '
                        f'fill="#E8F3FF" font-weight="700">{html.escape(label)}</text>')
            actions.append(_tween(f"#v-{index}-bar-{n}", "{scaleY:0,opacity:0}",
                                  "{scaleY:1,opacity:1,transformOrigin:'center bottom',duration:0.9,ease:'power2.out'}",
                                  a(0.18+n*0.18)))
        body = (base + '<line x1="85" y1="478" x2="928" y2="478" stroke="#C5D8ED" '
                'opacity=".5" stroke-width="4"/>'
                + "".join(bars)
                + '<text x="108" y="80" fill="#9EC4EA" font-size="26">ILLUSTRATIVE VALUES</text>')
    else:  # horizon
        hills = ('<path d="M0 490 Q200 420 410 496 T830 480 L1000 515 L1000 620 L0 620Z" '
                 'fill="#283454"/><path d="M0 558 Q230 494 450 566 T1000 534 L1000 620 L0 620Z" '
                 'fill="#192039"/>')
        body = (base + f'<rect x="8" y="15" width="984" height="570" rx="36" fill="url(#dusk-{index})"/>'
                f'<circle id="v-{index}-sun" cx="690" cy="225" r="105" fill="#FFE19E"/>'
                f'<g id="v-{index}-blue" opacity=".85">'
                '<path d="M0 0 L1000 0 L1000 255 Q550 420 0 280Z" fill="#426FB8" opacity=".62"/>'
                '</g>' + hills + '<text x="80" y="120" fill="#FFE3C2" font-size="33" '
                'font-weight="700">THE LONG WAY THROUGH AIR</text>')
        actions.append(_tween(f"#v-{index}-sun", "{y:-85,opacity:0.8}",
                              f"{{y:100,opacity:1,duration:{seconds*.88:.3f},ease:'none'}}", a(0.04)))
        actions.append(_tween(f"#v-{index}-blue", "{opacity:0.9}",
                              f"{{opacity:0.04,duration:{seconds*.84:.3f},ease:'none'}}", a(0.12)))
    return _svg(body, index), "\n".join(actions)
