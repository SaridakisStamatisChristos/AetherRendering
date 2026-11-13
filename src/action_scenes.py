"""Deterministic, model-free illustrated character and object motion for HyperFrames.

This module deliberately ships bounded, reusable actions and assets, not arbitrary
JavaScript or user-authored SVG. Each motion is absolute-time GSAP, hence seekable
and reproducible by frame-based rendering. No external artwork is required.
"""
import html

ACTION_TYPES = frozenset(("character_stage", "object_chain", "product_focus"))
PROPS = frozenset(("sun", "solar_panel", "battery", "lamp", "gear", "book", "box"))
ACTIONS = frozenset(("introduce", "point", "lift", "operate", "celebrate"))
CAMERAS = frozenset(("wide", "push_in", "pan_left", "pan_right", "detail"))
ALLOWED = {
    "character_stage": {"type", "prop", "action", "camera"},
    "object_chain": {"type", "items", "camera"},
    "product_focus": {"type", "prop", "camera"},
}


def validate_action(config, index):
    if not isinstance(config, dict) or config.get("type") not in ACTION_TYPES:
        raise ValueError(f"Scene {index}: invalid action scene")
    kind = config["type"]
    if set(config) - ALLOWED[kind]:
        raise ValueError(f"Scene {index}: unsupported action attributes")
    if config.get("camera", "wide") not in CAMERAS:
        raise ValueError(f"Scene {index}: unknown camera preset")
    if kind in ("character_stage", "product_focus"):
        if config.get("prop") not in PROPS:
            raise ValueError(f"Scene {index}: unsupported prop")
        if kind == "character_stage" and config.get("action", "introduce") not in ACTIONS:
            raise ValueError(f"Scene {index}: unsupported character action")
    else:
        items = config.get("items")
        if (not isinstance(items, list) or not 2 <= len(items) <= 4
                or any(not isinstance(item, str) or item not in PROPS for item in items)):
            raise ValueError(f"Scene {index}: chain requires 2–4 known objects")


def _tween(target, source, dest, start):
    """All selectors and tween instructions are constructed from fixed templates."""
    return f"tl.fromTo('#{target}',{source},{dest},{start:.3f});"


def _base(index):
    return (
        f'<defs><linearGradient id="a-bg-{index}" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#1A3557"/><stop offset=".6" stop-color="#101F3C"/>'
        '<stop offset="1" stop-color="#0A1731"/></linearGradient>'
        f'<linearGradient id="a-coat-{index}" x1="0" y1="0" x2="1" y2=".8">'
        '<stop offset="0" stop-color="#5EBAE5"/><stop offset=".55" stop-color="#3178AF"/>'
        '<stop offset="1" stop-color="#194878"/></linearGradient>'
        f'<linearGradient id="a-metal-{index}" x1="0" y1="0" x2=".9" y2="1">'
        '<stop offset="0" stop-color="#D9E9F5"/><stop offset=".5" stop-color="#819DBB"/>'
        '<stop offset="1" stop-color="#425A82"/></linearGradient>'
        f'<radialGradient id="a-glow-{index}"><stop offset="0" stop-color="#61CDFF" stop-opacity=".8"/>'
        '<stop offset="1" stop-color="#61CDFF" stop-opacity="0"/></radialGradient></defs>'
        f'<rect x="20" y="20" width="960" height="576" rx="44" fill="url(#a-bg-{index})"/>'
        '<path d="M70 476 H930" stroke="#426181" stroke-width="5" opacity=".75"/>'
        '<path d="M70 483 H930" stroke="#1B2942" stroke-width="3"/>'
        '<rect x="70" y="76" width="250" height="5" rx="2" fill="#4A9BA8" opacity=".3"/>'
        '<rect x="710" y="75" width="210" height="5" rx="2" fill="#79A9E1" opacity=".2"/>'
        '<circle cx="516" cy="318" r="280" fill="url(#a-glow-{index})" opacity=".22"/>'
    )


def _prop(name, index, identifier, x, y, scale=1):
    """Polished compact local SVG icon. Coordinates use local -100..100 space."""
    metal = f"url(#a-metal-{index})"
    art = {
      "sun": (
          '<circle r="65" fill="#FFDA8C" stroke="#FFF0B8" stroke-width="9"/>'
          '<circle r="42" fill="#FFEFBF" opacity=".8"/>'
          + ''.join(f'<path d="M0 -80 L0 -110" stroke="#FFD68D" stroke-width="11" '
                    'stroke-linecap="round" transform="rotate(%d)"/>' % angle
                    for angle in range(0,360,45))),
      "solar_panel": (
          '<path d="M-98 -72 L86 -92 L110 63 L-77 84Z" fill="#0D3267" '
          'stroke="#C8E9F9" stroke-width="9" stroke-linejoin="round"/>'
          '<path d="M-76 -60 L73 -77 L92 53 L-57 65Z" fill="#2D74A7"/>'
          + ''.join(f'<path d="M{x} -70 L{x+18} 61" stroke="#9DDAF8" opacity=".64" '
                    'stroke-width="4"/>' for x in (-47,-8,30,69))
          + ''.join(f'<path d="M-70 {y} L85 {y-14}" stroke="#B7E7FF" '
                    'stroke-width="4" opacity=".65"/>' for y in (-24,13,48))
          + '<path d="M-12 84 L-12 111 M40 81 L40 110" stroke="#9BBED7" stroke-width="11"/>'),
      "battery": (
          f'<rect x="-78" y="-88" width="156" height="180" rx="22" fill="{metal}" '
          'stroke="#C3E2F5" stroke-width="6"/>'
          '<rect x="-31" y="-102" width="62" height="18" rx="7" fill="#CFEBFA"/>'
          '<rect x="-61" y="-66" width="122" height="135" rx="14" fill="#224C72"/>'
          '<path d="M10 -60 L-31 10 H5 L-10 68 L43 -7 H7Z" fill="#F9DD77"/>'
          '<rect x="-49" y="70" width="98" height="8" rx="4" fill="#6AA6C1"/>'),
      "lamp": (
          '<circle r="85" cy="-35" fill="#F7D680" opacity=".25"/>'
          '<path d="M-62 -62 Q-77 -128 -5 -141 Q75 -141 64 -61 '
          'Q54 -33 30 -12 L29 2 H-28 L-28 -14 Q-55 -35 -62 -62Z" '
          'fill="#FFE5A0" stroke="#FFF7C9" stroke-width="8"/>'
          '<path d="M-22 12 H24 M-22 27 H24" stroke="#7995AD" stroke-width="11" '
          'stroke-linecap="round"/>'
          '<rect x="-18" y="34" width="36" height="20" rx="9" fill="#7CA4BA"/>'
          '<path d="M-7 -14 Q-38 -54 -10 -73 Q16 -84 26 -48" stroke="#E1A64E" '
          'stroke-width="9" fill="none"/>'),
      "gear": (
          '<circle r="87" fill="#91B7D5" stroke="#E1F2FB" stroke-width="9"/>'
          + ''.join(f'<rect x="-16" y="-110" width="32" height="44" rx="6" '
                    'fill="#BDE0F2" transform="rotate(%d)"/>'%a for a in range(0,360,45))
          + '<circle r="49" fill="#153A69" stroke="#B8DFF0" stroke-width="7"/>'
          + '<circle r="22" fill="#78B5D7"/>'),
      "book": (
          '<path d="M-95 -86 Q-34 -110 0 -72 Q34 -110 95 -86 V85 '
          'Q40 59 0 94 Q-40 59 -95 85Z" fill="#D6E9F5" stroke="#79BCE1" stroke-width="7"/>'
          '<path d="M0 -72 V92" stroke="#538AB6" stroke-width="7"/>'
          '<path d="M-75 -56 L-17 -49 M-75 -28 L-17 -21 M18 -49 L73 -56 '
          'M18 -21 L73 -28" fill="none" stroke="#8DB3C9" stroke-width="6"/>'),
      "box": (
          '<path d="M-84 -71 L1 -106 L87 -64 L1 -25Z" fill="#DAA975"/>'
          '<path d="M-84 -71 V60 L1 108 V-25Z" fill="#BD8459"/>'
          '<path d="M1 -25 L87 -64 V63 L1 108Z" fill="#E3BB88"/>'
          '<path d="M1 -25 V108" stroke="#F7D9AD" stroke-width="6"/>'),
    }[name]
    return (f'<g id="{identifier}" transform="translate({x} {y}) scale({scale:.3f})">'
            f'{art}</g>')


def _character(index):
    """Illustrated rig (head, two arm groups, body, legs and eyes)."""
    root = f"actor-{index}"
    return (
        f'<g id="{root}" transform="translate(0 0)">'
        f'<ellipse id="{root}-shadow" cx="322" cy="492" rx="141" ry="18" fill="#050E25" opacity=".56"/>'
        f'<g id="{root}-legs">'
        '<path d="M265 381 L258 461 Q265 482 292 478 L322 396Z" fill="#243958"/>'
        '<path d="M326 388 L337 469 Q360 487 376 463 L380 386Z" fill="#2D4668"/>'
        '<path d="M249 462 L295 463 L316 486 Q305 497 252 494 Q243 482 249 462Z" fill="#0B1F38"/>'
        '<path d="M335 465 L382 463 L408 486 Q405 499 349 495 Q334 486 335 465Z" fill="#152C4A"/>'
        '</g>'
        f'<g id="{root}-torso">'
        f'<path d="M278 226 Q315 211 349 225 L389 381 Q318 407 249 380Z" fill="url(#a-coat-{index})" '
        'stroke="#7CC6EF" stroke-width="6"/>'
        '<path d="M307 231 L327 270 L347 230 L338 380 L305 381Z" fill="#D9EEF8" opacity=".94"/>'
        '<path d="M314 278 L330 289 L321 335" fill="none" stroke="#4D9CC3" stroke-width="6"/>'
        '<rect x="352" y="267" width="31" height="36" rx="8" fill="#183F69" stroke="#91D6F0" stroke-width="4"/>'
        '</g>'
        f'<g id="{root}-arm-left" transform="translate(275 247)">'
        '<path d="M0 0 Q-37 17 -37 66 L-22 111 Q-13 130 3 117 L18 109 L5 69 L20 25Z" '
        f'fill="url(#a-coat-{index})" stroke="#80BEE1" stroke-width="5"/>'
        '<ellipse cx="-14" cy="123" rx="20" ry="24" fill="#E7A878"/>'
        '</g>'
        f'<g id="{root}-arm-right" transform="translate(365 245)">'
        '<path d="M0 0 Q26 15 43 48 L66 88 Q79 108 92 87 Q106 70 81 54 L40 10Z" '
        f'fill="url(#a-coat-{index})" stroke="#80BEE1" stroke-width="5"/>'
        '<ellipse cx="94" cy="88" rx="22" ry="24" fill="#E9B184"/>'
        '</g>'
        f'<g id="{root}-head" transform="translate(0 0)">'
        '<path d="M309 205 L310 238 Q327 260 343 238 L343 205Z" fill="#D79A77"/>'
        '<ellipse cx="326" cy="173" rx="65" ry="78" fill="#E9B78D"/>'
        '<ellipse cx="261" cy="181" rx="12" ry="20" fill="#D99F7A"/>'
        '<ellipse cx="390" cy="181" rx="12" ry="20" fill="#D99F7A"/>'
        '<path d="M263 160 Q246 82 311 84 Q384 63 393 151 L380 143 '
        'Q355 119 308 138 L276 151Z" fill="#172945"/>'
        '<path d="M278 123 Q301 103 323 112" fill="none" stroke="#35516C" stroke-width="10" '
        'stroke-linecap="round"/>'
        f'<g id="{root}-eyes">'
        '<ellipse cx="303" cy="178" rx="6" ry="8" fill="#153249"/>'
        '<ellipse cx="353" cy="178" rx="6" ry="8" fill="#153249"/>'
        '</g>'
        '<path d="M311 205 Q329 222 346 204" fill="none" stroke="#935C55" stroke-width="5" '
        'stroke-linecap="round"/>'
        '<path d="M325 188 L322 199" fill="none" stroke="#C6856C" stroke-width="4"/>'
        '</g></g>'
    )


def _camera(index, preset, start, duration):
    target = f"visual-stage-{index}"
    # Small reversible movements retain safe margins across portrait and landscape.
    values = {
        "wide": ("{x:0,scale:1}", f"{{x:0,scale:1,duration:{duration:.3f},ease:'none'}}"),
        "push_in": ("{x:0,scale:1}", f"{{x:-8,scale:1.08,duration:{duration:.3f},ease:'none'}}"),
        "pan_left": ("{x:22,scale:1.03}", f"{{x:-22,scale:1.03,duration:{duration:.3f},ease:'none'}}"),
        "pan_right": ("{x:-22,scale:1.03}", f"{{x:22,scale:1.03,duration:{duration:.3f},ease:'none'}}"),
        "detail": ("{x:12,scale:1.06}", f"{{x:-8,scale:1.11,duration:{duration:.3f},ease:'none'}}"),
    }
    a,b=values[preset]
    return _tween(target, a, b, start)


def character_stage(config, index, start, duration):
    kind = config.get("action", "introduce")
    prop = config["prop"]
    actor = f"actor-{index}"
    prop_id = f"object-{index}-hero"
    body = _base(index) + _character(index)
    body += '<path d="M465 435 H900 V464 H465Z" fill="#37556D" stroke="#80AFC9" stroke-width="5"/>'
    body += '<path d="M525 464 V494 M854 464 V494" stroke="#7798AC" stroke-width="14"/>'
    body += _prop(prop, index, prop_id, 692, 338, .85)
    body += f'<circle id="action-{index}-pulse" cx="692" cy="338" r="128" stroke="#78DAF9" stroke-width="7" fill="none" opacity=".12"/>'
    t=lambda f: start+duration*f
    moves = [
        _tween(actor, "{opacity:0,y:22}", "{opacity:1,y:0,duration:.65,ease:'power2.out'}",t(.03)),
        _tween(prop_id, "{opacity:0,scale:.66}", "{opacity:1,scale:.85,duration:.65,ease:'back.out(1.4)'}",t(.14)),
        _tween(f"{actor}-head","{rotation:-5}","{rotation:5,transformOrigin:'center bottom',duration:.75,ease:'sine.inOut'}",t(.35)),
        _tween(f"{actor}-eyes","{scaleY:1}","{scaleY:.12,transformOrigin:'center center',duration:.09,ease:'none'}",t(.54)),
        _tween(f"{actor}-eyes","{scaleY:.12}","{scaleY:1,duration:.12,ease:'none'}",t(.56)),
    ]
    if kind in ("introduce","point","operate"):
        moves.append(_tween(f"{actor}-arm-right","{rotation:12}",
                            "{rotation:-42,transformOrigin:'0px 0px',duration:.8,ease:'power2.out'}",t(.30)))
        moves.append(_tween(f"{actor}-arm-right","{rotation:-42}",
                            "{rotation:-24,duration:.65,ease:'sine.inOut'}",t(.70)))
    elif kind == "lift":
        moves.append(_tween(prop_id,"{y:0,rotation:-4}",
                            "{y:-81,rotation:3,duration:1.05,ease:'power2.out'}",t(.38)))
        moves.append(_tween(f"{actor}-arm-right","{rotation:18}",
                            "{rotation:-62,transformOrigin:'0px 0px',duration:.9,ease:'power2.out'}",t(.32)))
    elif kind == "celebrate":
        for side,angle in (("left",49),("right",-61)):
            moves.append(_tween(f"{actor}-arm-{side}","{rotation:0}",
                                f"{{rotation:{angle},transformOrigin:'0px 0px',duration:.8,ease:'back.out(1.2)'}}",t(.36)))
    if kind == "operate":
        moves.append(_tween(f"action-{index}-pulse","{opacity:.0,scale:.7}",
                            "{opacity:.65,scale:1.08,transformOrigin:'center center',duration:.85,ease:'sine.out'}",t(.55)))
        moves.append(_tween(f"action-{index}-pulse","{opacity:.65,scale:1.08}",
                            "{opacity:.1,scale:1.3,duration:.65,ease:'sine.in'}",t(.75)))
    return body,"\n".join(moves)


def object_chain(config, index, start, duration):
    items=config["items"]
    n=len(items)
    body=_base(index)
    body+='<text x="100" y="122" font-weight="800" font-size="31" fill="#BFE5F7">FOLLOW THE FLOW</text>'
    commands=[]
    for i, item in enumerate(items):
        x=int(150+i*700/(n-1))
        node=f"chain-{index}-{i}"
        body+=f'<circle cx="{x}" cy="315" r="104" fill="#1D4774" stroke="#4A86B1" stroke-width="4"/>'
        body+=_prop(item,index,node,x,305,.62)
        body+=f'<text x="{x}" y="482" text-anchor="middle" font-size="26" font-weight="800" fill="#D7EEFF">{html.escape(item.replace("_"," ").upper())}</text>'
        commands.append(_tween(node,"{opacity:0,scale:.3,y:42}",
                               "{opacity:1,scale:.62,y:0,duration:.65,ease:'back.out(1.4)'}",
                               start+duration*(.09+i*.19)))
        if i+1<n:
            xe=int(150+(i+1)*700/(n-1))
            line_id=f"link-{index}-{i}"
            body+=f'<path id="{line_id}" d="M{x+98} 315 L{xe-98} 315" fill="none" stroke="#8EDBF4" stroke-width="9" stroke-linecap="round"/>'
            body+=f'<path d="M{xe-118} 299 L{xe-98} 315 L{xe-118} 331" stroke="#8EDBF4" stroke-width="7" fill="none"/>'
            commands.append(_tween(line_id,"{opacity:0,scaleX:0}",
                                   "{opacity:1,scaleX:1,transformOrigin:'left center',duration:.5,ease:'power2.out'}",
                                   start+duration*(.24+i*.19)))
    return body,"\n".join(commands)


def product_focus(config, index, start, duration):
    prop=config["prop"]
    prop_id=f"focus-{index}"
    body=_base(index)
    body+=f'<circle id="focus-ring-{index}" cx="500" cy="317" r="227" fill="none" stroke="#5FBADE" stroke-width="5" opacity=".54"/>'
    body+=f'<circle cx="500" cy="317" r="260" fill="url(#a-glow-{index})" opacity=".45"/>'
    body+=_prop(prop,index,prop_id,500,339,1.70)
    for j,(x,y) in enumerate(((190,150),(805,171),(810,474),(175,450))):
        body+=f'<circle id="focus-dot-{index}-{j}" cx="{x}" cy="{y}" r="17" fill="#90D8F9"/>'
    moves=[
       _tween(prop_id,"{opacity:0,scale:.75,rotation:-7}",
              "{opacity:1,scale:1.70,rotation:0,duration:.85,ease:'back.out(1.2)'}",start+duration*.10),
       _tween(f"focus-ring-{index}","{scale:.72,opacity:0,rotation:-14}",
              f"{{scale:1.02,opacity:.55,rotation:17,transformOrigin:'center center',duration:{duration*.83:.3f},ease:'none'}}",
              start+duration*.10),
       _tween(prop_id,"{y:0}","{y:-12,duration:.85,ease:'sine.inOut'}",start+duration*.63)
    ]
    for j in range(4):
        moves.append(_tween(f"focus-dot-{index}-{j}","{opacity:0,scale:.4}",
                            "{opacity:.85,scale:1,duration:.5,ease:'power2.out'}",start+duration*(.30+j*.11)))
    return body,"\n".join(moves)


def render_action(config, index, start, duration):
    validate_action(config, index)
    kind=config["type"]
    if kind=="character_stage":
        body,events=character_stage(config,index,start,duration)
    elif kind=="object_chain":
        body,events=object_chain(config,index,start,duration)
    else:
        body,events=product_focus(config,index,start,duration)
    enter=_tween(f"visual-stage-{index}","{opacity:0}","{opacity:1,duration:.4,ease:'power1.out'}",start+.02)
    camera=_camera(index,config.get("camera","wide"),start,duration)
    return body,"\n".join((enter,camera,events))
