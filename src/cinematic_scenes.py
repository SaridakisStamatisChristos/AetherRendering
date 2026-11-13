"""Two narrative-first scientific illustration scenes built from local, safe SVG.

These scenes address the v1.2 visual review: a globe is not a sky-scattering
diagram, and an arbitrary numerical bar chart is not evidence about vision.
No outside photos, remote URLs, model inference, JavaScript injection or
nonseekable wall-clock effects are involved.
"""
import math

CINEMATIC_TYPES = frozenset({"sky_dome", "perception"})


def tween(selector, source, dest, position):
    return f"tl.fromTo('{selector}',{source},{dest},{position:.3f});"


def sky_dome(i, start, duration):
    """Illustrate blue photons arriving from multiple parts of the visible sky."""
    at = lambda fraction: start + duration * fraction
    prefix = f"v-{i}"
    elements = [
        f'<defs><linearGradient id="dome-bg-{i}" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#092150"/>'
        '<stop offset=".55" stop-color="#174C9D"/>'
        '<stop offset="1" stop-color="#62BDEA"/></linearGradient>'
        f'<radialGradient id="dome-glow-{i}"><stop offset="0" stop-color="#E1F5FF" '
        'stop-opacity=".8"/><stop offset="1" stop-color="#6EBEFF" stop-opacity="0"/>'
        '</radialGradient></defs>',
        f'<rect x="22" y="20" width="956" height="575" rx="38" fill="url(#dome-bg-{i})"/>',
        '<path d="M55 460 Q480 100 945 460" stroke="#A4EAFF" opacity=".35" '
        'stroke-width="6" fill="none"/>',
        '<path d="M55 460 Q490 290 945 460" stroke="#D0F0FF" opacity=".18" '
        'stroke-width="3" fill="none"/>',
        '<path d="M26 495 Q280 468 500 498 T975 490 L975 593 L26 593Z" fill="#143152"/>',
        f'<circle id="{prefix}-sun" cx="182" cy="125" r="47" fill="#FFE4A3"/>',
        f'<circle cx="182" cy="125" r="105" fill="url(#dome-glow-{i})"/>',
        f'<path id="{prefix}-white" d="M215 148 L468 345" stroke="#FFF2C8" '
        'stroke-width="12" stroke-linecap="round" opacity=".9"/>',
        '<circle cx="500" cy="505" r="50" fill="#0B223F" stroke="#C0EAFF" stroke-width="5"/>',
        '<path d="M454 504 Q500 464 546 504 Q500 543 454 504Z" fill="#C3F1FE"/>',
        '<circle cx="500" cy="504" r="13" fill="#143C7E"/>',
        '<circle cx="503" cy="500" r="5" fill="white"/>',
        '<text x="500" y="577" text-anchor="middle" font-size="26" '
        'font-weight="700" fill="#DAEEFF">YOUR EYES</text>',
        '<text x="295" y="84" font-size="29" fill="#DAEEFF" font-weight="700">'
        'THE ATMOSPHERE</text>',
    ]
    actions = [
        tween(f"#{prefix}-white", "{opacity:0,scaleX:0}",
              "{opacity:.95,scaleX:1,transformOrigin:'left center',duration:.8,ease:'power2.out'}",
              at(.10)),
        tween(f"#{prefix}-sun", "{opacity:0,scale:.7}",
              "{opacity:1,scale:1,transformOrigin:'center center',duration:.55,ease:'power2.out'}",
              at(.06)),
    ]
    arrivals = [
        (290,230,"#84D5FF"), (480,175,"#66C4FF"), (705,225,"#99E1FF"),
        (825,355,"#60B7FF"), (165,390,"#99D5FF")
    ]
    for n, (x,y,color) in enumerate(arrivals):
        ident=f"{prefix}-ray-{n}"
        elements.append(f'<path id="{ident}" d="M{x} {y} Q{(x+500)//2} 380 500 505" '
                        f'fill="none" stroke="{color}" stroke-width="10" '
                        'stroke-linecap="round" opacity=".93"/>')
        elements.append(f'<circle id="{prefix}-point-{n}" cx="{x}" cy="{y}" r="14" '
                        f'fill="{color}" opacity=".9"/>')
        actions.append(tween(f"#{ident}","{opacity:0,scaleX:0,scaleY:0}",
                             "{opacity:.93,scaleX:1,scaleY:1,"
                             "transformOrigin:'center center',duration:.75,ease:'power2.out'}",
                             at(.27+n*.10)))
        actions.append(tween(f"#{prefix}-point-{n}","{opacity:0,scale:.25}",
                             "{opacity:.9,scale:1,duration:.55,ease:'power2.out'}",
                             at(.23+n*.10)))
    actions.append(tween(f"#{prefix}-sun","{scale:1}",
                         f"{{scale:1.06,transformOrigin:'center center',duration:{duration*.45:.3f},ease:'sine.inOut'}}",at(.50)))
    return "".join(elements),"\n".join(actions)


def perception(i, start, duration):
    """Qualitative violet/blue/red viewer illustration, not invented numeric data."""
    at=lambda fraction:start+duration*fraction
    prefix=f"v-{i}"
    elements=[
        '<rect x="24" y="26" width="952" height="561" rx="38" fill="#131D3A"/>',
        '<rect x="55" y="55" width="890" height="508" rx="29" fill="#1A2544" '
        'stroke="#34456E" stroke-width="3"/>',
        '<text x="85" y="122" font-size="31" font-weight="800" fill="#D5EAFF">'
        'LIGHT + THE HUMAN EYE</text>',
        '<path d="M655 309 Q775 203 903 309 Q785 428 655 309Z" fill="#294B6D" '
        'stroke="#8CE4FC" stroke-width="7"/>',
        '<circle cx="782" cy="310" r="75" fill="#B2E5F4"/>',
        '<circle cx="782" cy="310" r="45" fill="#194A89"/>',
        '<circle cx="782" cy="310" r="26" fill="#101E4C"/>',
        '<circle cx="768" cy="294" r="12" fill="#F5FAFF" opacity=".85"/>',
        '<text x="666" y="474" font-size="26" font-weight="800" fill="#E0EFFF">'
        'PERCEIVED COLOR</text>',
    ]
    actions=[]
    beams=[
        ("VIOLET","#BD92FE",180, .36),
        ("BLUE","#4CBBFF",300, 1.00),
        ("RED","#FF9A7F",420, .58),
    ]
    for n,(label,color,y,strength) in enumerate(beams):
        name=f"{prefix}-channel-{n}"
        label_id=f"{prefix}-label-{n}"
        elements.append(f'<line id="{name}" x1="215" y1="{y}" x2="635" y2="310" '
                        f'stroke="{color}" stroke-width="{13 if n==1 else 8}" '
                        'stroke-linecap="round"/>')
        elements.append(f'<circle id="{prefix}-source-{n}" cx="187" cy="{y}" '
                        f'r="{21 if n==1 else 16}" fill="{color}"/>')
        elements.append(f'<text id="{label_id}" x="75" y="{y-22}" '
                        f'font-weight="800" fill="{color}" font-size="26">{label}</text>')
        actions.append(tween(f"#{name}","{opacity:0,scaleX:0}",
                             f"{{opacity:{strength:.2f},scaleX:1,transformOrigin:'left center',"
                             "duration:.85,ease:'power2.out'}}",at(.15+n*.18)))
        actions.append(tween(f"#{label_id}","{opacity:0,x:-22}",
                             f"{{opacity:1,x:0,duration:.5,ease:'power2.out'}}",at(.12+n*.18)))
        actions.append(tween(f"#{prefix}-source-{n}","{opacity:0,scale:.4}",
                             f"{{opacity:{strength:.2f},scale:1,duration:.6,ease:'power2.out'}}",at(.12+n*.18)))
    elements.append(f'<circle id="{prefix}-response" cx="782" cy="310" r="92" '
                    'stroke="#64C7FF" stroke-width="6" fill="none" opacity=".20"/>')
    actions.append(tween(f"#{prefix}-response","{opacity:0,scale:.73}",
                         "{opacity:.65,scale:1,transformOrigin:'center center',duration:.75,ease:'power2.out'}",
                         at(.72)))
    actions.append(tween(f"#{prefix}-response","{opacity:.65,scale:1}",
                         f"{{opacity:.20,scale:1.16,transformOrigin:'center center',duration:{duration*.16:.3f},ease:'none'}}",
                         at(.83)))
    return "".join(elements),"\n".join(actions)


def render_cinematic(mode, index, start, duration):
    if mode=="sky_dome":
        return sky_dome(index,start,duration)
    if mode=="perception":
        return perception(index,start,duration)
    raise ValueError(f"Unknown cinematic scene: {mode}")
