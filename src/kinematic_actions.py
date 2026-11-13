"""Deterministic 2-link character IK, grounded walk cycle, and object contact.

All keyframes are compiled to absolute GSAP timeline positions and SVG attribute
tweens. No arbitrary source code, remote assets, timers or unbounded animation.
The character is procedural 2D; this is not motion capture or 3D skeletal rigging.
"""
import json
import math

from action_scenes import PROPS, CAMERAS, _base, _character, _prop, _camera

KINEMATIC_TYPES = frozenset({"kinematic_stage"})
BEHAVIORS = frozenset({"walk_to", "pick_up", "inspect", "set_down", "operate"})
_ALLOWED = {"type", "prop", "behavior", "camera"}

SHOULDER = (365.0, 245.0)
HIP_LEFT = (288.0, 379.0)
HIP_RIGHT = (354.0, 379.0)
ARM_LENGTHS = (122.0, 122.0)
LEG_LENGTHS = (72.0, 80.0)
HAND_REST = (440.0, 346.0)
HAND_CONTACT = (535.0, 333.0)
HAND_CARRY = (495.0, 258.0)
HAND_INSPECT = (470.0, 249.0)
PROP_HOME = (570, 345)
PROP_LIFT = (-40, -75)
PROP_INSPECT = (-65, -84)


def _tween(selector, source, dest, start):
    """Prevent later GSAP fromTo's from-values changing earlier timeline frames."""
    if not dest.startswith("{") or not dest.endswith("}"):
        raise ValueError("Malformed authored tween")
    end = dest[:-1] + ",immediateRender:false}"
    return f"tl.fromTo('#{selector}',{source},{end},{start:.3f});"


def validate_kinematic(config, index):
    if not isinstance(config, dict) or config.get("type") not in KINEMATIC_TYPES:
        raise ValueError(f"Scene {index}: invalid kinematic type")
    if set(config) - _ALLOWED:
        raise ValueError(f"Scene {index}: unsupported kinematic attributes")
    if config.get("prop") not in PROPS:
        raise ValueError(f"Scene {index}: invalid kinematic prop")
    if config.get("behavior") not in BEHAVIORS:
        raise ValueError(f"Scene {index}: invalid kinematic behavior")
    if config.get("camera", "wide") not in CAMERAS:
        raise ValueError(f"Scene {index}: invalid kinematic camera")


def solve_ik(shoulder, wrist, upper, lower, elbow_side=1):
    """Law-of-cosines 2-link IK; return exact hinge coordinates.

    A raised ValueError rather than silent clamping detects impossible poses.
    The elbow is the selected positive or negative perpendicular solution.
    """
    dx = wrist[0] - shoulder[0]
    dy = wrist[1] - shoulder[1]
    reach = math.hypot(dx, dy)
    if (not math.isfinite(reach) or reach <= 0 or
            reach >= upper + lower or reach <= abs(upper - lower)):
        raise ValueError("Unreachable two-bone target")
    along = (upper * upper - lower * lower + reach * reach) / (2 * reach)
    normal = math.sqrt(max(0.0, upper * upper - along * along))
    return (shoulder[0] + along * dx / reach - elbow_side * normal * dy / reach,
            shoulder[1] + along * dy / reach + elbow_side * normal * dx / reach)


def _position(start, finish):
    return {"x1": round(start[0], 3), "y1": round(start[1], 3),
            "x2": round(finish[0], 3), "y2": round(finish[1], 3)}


def _circle(position):
    return {"cx": round(position[0], 3), "cy": round(position[1], 3)}


def _attr(selector, initial, final, t, duration, ease="sine.inOut"):
    """Compose GSAP AttrPlugin tweens with only numeric properties."""
    if duration <= 0:
        raise ValueError("Nonpositive tween duration")
    s = json.dumps({"attr": initial}, separators=(",", ":"))
    e = json.dumps({"attr": final, "duration": round(duration, 3),
                    "ease": ease, "immediateRender": False}, separators=(",", ":"))
    return f"tl.fromTo('#{selector}',{s},{e},{t:.3f});"


def _limb_geometry(shoulder, wrist, lengths):
    elbow = solve_ik(shoulder, wrist, *lengths)
    return {"upper": _position(shoulder, elbow),
            "lower": _position(elbow, wrist),
            "elbow": _circle(elbow), "hand": _circle(wrist)}


def _limb_svg(prefix, geom, arm):
    color = "#57ADE2" if arm else "#284A76"
    contour = "#B4E6FC" if arm else "#5687B4"
    segments = []
    for name in ("upper", "lower"):
        val = geom[name]
        segments.append(
            f'<line id="{prefix}-{name}" x1="{val["x1"]}" y1="{val["y1"]}" '
            f'x2="{val["x2"]}" y2="{val["y2"]}" stroke="{color}" '
            f'stroke-width="{31 if arm else 29}" stroke-linecap="round"/>'
        )
    elbow = geom["elbow"]
    segments.append(
        f'<circle id="{prefix}-elbow" cx="{elbow["cx"]}" cy="{elbow["cy"]}" '
        f'r="{18 if arm else 15}" fill="{color}" stroke="{contour}" stroke-width="4"/>'
    )
    hand = geom["hand"]
    segments.append(
        f'<circle id="{prefix}-hand" cx="{hand["cx"]}" cy="{hand["cy"]}" '
        f'r="{22 if arm else 18}" fill="{"#E4AB85" if arm else "#102843"}" '
        f'stroke="{contour}" stroke-width="4"/>'
    )
    return "".join(segments)


def _move_limb(prefix, origin, from_wrist, to_wrist, lengths, t, dur):
    old = _limb_geometry(origin, from_wrist, lengths)
    new = _limb_geometry(origin, to_wrist, lengths)
    return "\n".join(_attr(f"{prefix}-{name}", old[name], new[name], t, dur)
                     for name in ("upper", "lower", "elbow", "hand"))


def _rigged_actor(index, initial_hand, walking):
    root = f"actor-{index}"
    actor_markup = _character(index)
    for part in ("arm-right", "legs"):
        original = f'<g id="{root}-{part}"'
        changed = f'<g id="{root}-{part}" opacity="0"'
        if actor_markup.count(original) != 1:
            raise RuntimeError(f"Missing legacy character component: {part}")
        actor_markup = actor_markup.replace(original, changed)
    arm = _limb_svg(f"ik-arm-{index}",
                    _limb_geometry(SHOULDER, initial_hand, ARM_LENGTHS), True)
    left = _limb_svg(f"ik-leg-{index}-left",
                     _limb_geometry(HIP_LEFT, (274, 477), LEG_LENGTHS), False)
    right = _limb_svg(f"ik-leg-{index}-right",
                      _limb_geometry(HIP_RIGHT, (367, 477), LEG_LENGTHS), False)
    return (f'<g id="walking-actor-{index}">'
            f'{left}{right}{actor_markup}{arm}</g>')


def _object(index, prop):
    # Static x/y anchor is nested below the independently animated 'mover'.
    return (f'<g id="prop-mover-{index}">'
            + _prop(prop, index, f"kin-prop-{index}", *PROP_HOME, .66)
            + '</g>')


def _move_prop(index, before, after, t, duration):
    return _tween(f"prop-mover-{index}",
                  f"{{x:{before[0]:.3f},y:{before[1]:.3f}}}",
                  f"{{x:{after[0]:.3f},y:{after[1]:.3f},"
                  f"duration:{duration:.3f},ease:'sine.inOut'}}", t)


def _walk(index, start, duration):
    """Four grounded, alternating foot targets synchronized with actor travel."""
    schedule = [
        (.02, .11, (308, 442), (345, 476)),
        (.13, .10, (277, 476), (400, 441)),
        (.24, .095, (287, 467), (367, 477)),
    ]
    prev_l = (274, 477)
    prev_r = (367, 477)
    events = [
        _tween(f"walking-actor-{index}", "{x:-112}",
               f"{{x:0,duration:{duration*.33:.3f},ease:'power1.inOut'}}", start + duration*.03)
    ]
    for frac, length, left, right in schedule:
        for side, hip, old, new in (("left", HIP_LEFT, prev_l, left),
                                    ("right", HIP_RIGHT, prev_r, right)):
            events.append(_move_limb(f"ik-leg-{index}-{side}", hip, old, new,
                                     LEG_LENGTHS, start + duration*frac,
                                     duration*length))
        prev_l, prev_r = left, right
    return "\n".join(events)


def render_kinematic(config, index, start, duration):
    validate_kinematic(config, index)
    behavior = config["behavior"]
    walking = behavior == "walk_to"
    starts_held = behavior in ("inspect", "set_down")
    first_hand = HAND_CARRY if starts_held else HAND_REST
    root = f"ik-arm-{index}"
    base = _base(index)
    body = (base +
            '<path d="M466 419 H900 V445 H466Z" fill="#3E5D76" '
            'stroke="#92BDDD" stroke-width="5"/>'
            '<path d="M520 445 V483 M850 445 V483" fill="none" '
            'stroke="#587A98" stroke-width="13"/>'
            + _rigged_actor(index, first_hand, walking)
            + _object(index, config["prop"])
            + f'<circle id="effect-{index}" cx="{PROP_HOME[0]}" cy="{PROP_HOME[1]}" '
            'r="135" fill="none" stroke="#7DE2FA" stroke-width="8" opacity="0"/>'
    )
    # Set exact initial properties for held objects at the beginning of a shot.
    events = [
        _tween(f"visual-stage-{index}", "{opacity:0}",
               "{opacity:1,duration:.35,ease:'power1.out'}", start + .02),
        _camera(index, config.get("camera","wide"), start, duration)
    ]
    if starts_held:
        events.append(_move_prop(index, PROP_LIFT, PROP_LIFT,
                                 start, max(.12, duration*.03)))
    else:
        events.append(_move_prop(index, (0, 0), (0, 0),
                                 start, max(.12, duration*.03)))
    if walking:
        events.append(_walk(index, start, duration))
        start_reach, end_reach = (.39, .61)
    else:
        start_reach, end_reach = (.18, .42)
    reach_duration = duration*(end_reach - start_reach)
    if behavior in ("walk_to", "pick_up", "operate"):
        events.append(_move_limb(root, SHOULDER, HAND_REST, HAND_CONTACT,
                                 ARM_LENGTHS, start+duration*start_reach,
                                 reach_duration))
    if behavior == "pick_up":
        events.append(_move_limb(root, SHOULDER, HAND_CONTACT, HAND_CARRY,
                                 ARM_LENGTHS, start+duration*.52, duration*.19))
        events.append(_move_prop(index, (0, 0), PROP_LIFT,
                                 start+duration*.52, duration*.19))
    elif behavior == "inspect":
        events.append(_move_limb(root, SHOULDER, HAND_CARRY, HAND_INSPECT,
                                 ARM_LENGTHS, start+duration*.35, duration*.20))
        events.append(_move_prop(index, PROP_LIFT, PROP_INSPECT,
                                 start+duration*.35, duration*.20))
        events.append(_move_limb(root, SHOULDER, HAND_INSPECT, HAND_CARRY,
                                 ARM_LENGTHS, start+duration*.69, duration*.18))
        events.append(_move_prop(index, PROP_INSPECT, PROP_LIFT,
                                 start+duration*.69, duration*.18))
    elif behavior == "set_down":
        events.append(_move_limb(root, SHOULDER, HAND_CARRY, HAND_CONTACT,
                                 ARM_LENGTHS, start+duration*.31, duration*.24))
        events.append(_move_prop(index, PROP_LIFT, (0, 0),
                                 start+duration*.31, duration*.24))
        events.append(_move_limb(root, SHOULDER, HAND_CONTACT, HAND_REST,
                                 ARM_LENGTHS, start+duration*.68, duration*.16))
    elif behavior == "operate":
        events.append(_tween(f"effect-{index}", "{opacity:0,scale:.8}",
                             "{opacity:.7,scale:1.13,transformOrigin:'center center',"
                             f"duration:{duration*.16:.3f},ease:'power1.out'}}",
                             start+duration*.57))
        events.append(_tween(f"effect-{index}", "{opacity:.7,scale:1.13}",
                             "{opacity:0,scale:1.34,"
                             f"duration:{duration*.17:.3f},ease:'power1.in'}}",
                             start+duration*.77))
    # Head and eyelids are reused from the original character. Timings
    # deliberately avoid conflicting with the IK endpoints.
    events.append(_tween(f"actor-{index}-head", "{rotation:-3}",
                         "{rotation:6,transformOrigin:'center bottom',duration:.75,"
                         "ease:'sine.inOut'}", start+duration*.36))
    events.append(_tween(f"actor-{index}-eyes", "{scaleY:1}",
                         "{scaleY:.12,transformOrigin:'center center',duration:.08}",
                         start+duration*.76))
    events.append(_tween(f"actor-{index}-eyes", "{scaleY:.12}",
                         "{scaleY:1,duration:.1}", start+duration*.78))
    return body, "\n".join(events)
