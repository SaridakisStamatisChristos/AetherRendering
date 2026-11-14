"""Reusable deterministic SVG scene treatments, with no third-party images or runtime URLs.

Only enum-selected templates reach HTML; narration or Gemini never supplies SVG code.
All elements are seek-safe: motion is driven by the main GSAP timeline.
"""
import html
import math

VISUALS = frozenset({'abstract', 'spectrum', 'scatter', 'atmosphere', 'wavelengths', 'sunset'})
DESCRIPTIONS = {
    'spectrum': 'White light separating into a rainbow in a glass prism',
    'scatter': 'Blue rays scattered in all directions by air molecules',
    'atmosphere': 'Blue atmosphere above a curved Earth',
    'wavelengths': 'Blue and violet light waves with different wavelengths',
    'sunset': 'Orange-red sunlight crossing the horizon',
}

def _spectrum(prefix):
    colors = ('#FD6F72', '#FFA75E', '#F8DC74', '#70DCA7', '#5AC5FF', '#9182F4', '#CC8AFB')
    rays = ''.join(
        f'<path class="ray" d="M415 294 Q550 {272+(k-3)*13} 753 {160+k*47}" '
        f'stroke="{color}" stroke-width="11" stroke-linecap="round" fill="none" opacity=".94"/>'
        for k, color in enumerate(colors)
    )
    return f"""
  <path class="beam" d="M50 304 L325 294" stroke="#F8FBFF" stroke-width="16" stroke-linecap="round"/>
  <path d="M50 304 L325 294" stroke="#B8F2FF" stroke-width="38" opacity=".13"/>
  <polygon points="322,175 468,436 176,436" fill="#7CD8E8" fill-opacity=".15"
    stroke="#B7F0FF" stroke-width="6" stroke-linejoin="round"/>
  <path d="M322 175 L323 436" stroke="#E8F9FF" stroke-width="3" opacity=".5"/>
  {rays}
  <text x="53" y="264" fill="#E9F2FB" font-size="27" letter-spacing="3">WHITE LIGHT</text>
  <text x="526" y="541" fill="#C1D7E9" font-size="27" letter-spacing="3">VISIBLE COLORS</text>"""

def _scatter(prefix):
    molecule = ''.join(
        f'<circle cx="{100+(n*137)%620}" cy="{90+(n*79)%430}" r="{5+(n%3)*2}" '
        f'fill="#B4E8FF" opacity="{.3+(n%4)*.14:.2f}"/>'
        for n in range(38)
    )
    blue = ''.join(
        f'<path class="ray" d="M380 292 L{380+int(260*math.cos(n*math.pi/6))} '
        f'{292+int(220*math.sin(n*math.pi/6))}" fill="none" '
        f'stroke="#59BBFF" opacity=".62" stroke-width="5" stroke-linecap="round"/>'
        for n in range(12)
    )
    return f"""
  <path class="beam" d="M30 296 L378 296" stroke="#FFCA7C" stroke-width="12" stroke-linecap="round"/>
  <path d="M30 296 L378 296" stroke="#FFD499" stroke-width="40" opacity=".13"/>
  {molecule}
  {blue}
  <circle cx="380" cy="292" r="25" fill="#D9F2FF" opacity=".9"/>
  <circle cx="380" cy="292" r="55" fill="#6BC9FF" opacity=".18"/>
  <text x="54" y="85" fill="#E4F0F9" font-size="28" letter-spacing="3">SUNLIGHT</text>
  <text x="457" y="540" fill="#98D6FF" font-size="28" letter-spacing="3">BLUE SCATTERS</text>"""

def _atmosphere(prefix):
    stars = ''.join(
        f'<circle cx="{60+(n*173)%680}" cy="{55+(n*59)%230}" r="{2+n%3}" fill="white" opacity=".5"/>'
        for n in range(22)
    )
    return f"""
  {stars}
  <path d="M-40 570 A450 450 0 0 1 840 570" fill="none" stroke="#5EC9FF" stroke-width="80" opacity=".12"/>
  <path d="M-40 570 A450 450 0 0 1 840 570" fill="none" stroke="#64D7FF" stroke-width="9" opacity=".8"/>
  <path d="M-40 590 A450 450 0 0 1 840 590 L840 660 L-40 660 Z" fill="url(#{prefix}-ocean)"/>
  <path d="M0 520 Q390 410 800 520" fill="none" stroke="#91E2FF" stroke-width="4" opacity=".5"/>
  <path class="ray" d="M85 125 L300 300" stroke="#FFF1B3" stroke-width="11" stroke-linecap="round"/>
  <circle cx="92" cy="121" r="45" fill="#FFD386" opacity=".96"/>
  <circle cx="92" cy="121" r="80" fill="#FFD386" opacity=".14"/>
  <path class="ray" d="M300 300 L552 180" stroke="#68CAFF" stroke-width="8" opacity=".9"/>
  <path class="ray" d="M300 300 L660 312" stroke="#68CAFF" stroke-width="8" opacity=".78"/>
  <path class="ray" d="M300 300 L350 92" stroke="#68CAFF" stroke-width="8" opacity=".7"/>
  <text x="410" y="95" fill="#DBEDFB" font-size="29" letter-spacing="3">ATMOSPHERE</text>
  <text x="375" y="540" fill="#C0ECFF" font-size="29" letter-spacing="3">EARTH</text>"""

def _wavelengths(prefix):
    def wave(y, period, color, label):
        pts = ' '.join(
            f'{x},{y+28*math.sin(x*2*math.pi/period):.2f}'
            for x in range(68,748,8)
        )
        return (
            f'<polyline class="ray" points="{pts}" fill="none" stroke="{color}" '
            f'stroke-width="9" stroke-linejoin="round" stroke-linecap="round"/>'
            f'<text x="65" y="{y-60}" fill="{color}" font-size="31" letter-spacing="3">{label}</text>'
        )
    return f"""
  <rect x="46" y="110" width="710" height="360" rx="32" fill="#172A4A" fill-opacity=".7" stroke="#51769B" stroke-width="2"/>
  <path d="M60 277 H740" stroke="#8AA8C4" opacity=".24" stroke-width="3" stroke-dasharray="7 13"/>
  {wave(240, 160, '#57C6FF', 'BLUE LIGHT')}
  {wave(395, 87, '#B58BFF', 'VIOLET LIGHT')}
  <text x="95" y="525" fill="#E1E8F9" font-size="26" letter-spacing="3">SHORTER WAVES SCATTER MORE</text>"""

def _sunset(prefix):
    return f"""
  <rect x="0" y="0" width="800" height="600" fill="url(#{prefix}-sunset)" rx="28"/>
  <circle cx="410" cy="280" r="130" fill="#FFE0A0" opacity=".16"/>
  <circle cx="410" cy="280" r="100" fill="#FFCF88" opacity=".23"/>
  <circle cx="410" cy="280" r="75" fill="#FFE8AD"/>
  <path class="ray" d="M120 120 Q320 170 570 250" stroke="#FFE4AB" opacity=".45" stroke-width="9" fill="none"/>
  <path class="ray" d="M70 220 Q360 200 730 250" stroke="#FFC47C" opacity=".48" stroke-width="7" fill="none"/>
  <path d="M0 365 Q170 346 350 369 T800 360 L800 600 L0 600Z" fill="#392954" opacity=".8"/>
  <path d="M0 418 Q240 377 450 422 T800 400 L800 600 L0 600Z" fill="#1F345D"/>
  <path d="M0 500 Q200 460 450 496 T800 475 L800 600 L0 600Z" fill="#111E39"/>
  <path d="M0 360 H800" stroke="#FFCA91" opacity=".6" stroke-width="4"/>
  <text x="68" y="94" fill="#FFF0DB" font-size="32" letter-spacing="3">THE LONGER PATH</text>
  <text x="66" y="557" fill="#FFE4B4" font-size="27" letter-spacing="3">RED AND ORANGE REMAIN</text>"""

DRAWERS = {
    'spectrum': _spectrum,
    'scatter': _scatter,
    'atmosphere': _atmosphere,
    'wavelengths': _wavelengths,
    'sunset': _sunset,
}

def render_visual(kind, scene_index):
    """Return fully local visual markup; abstract is the backward-compatible default."""
    if kind not in VISUALS:
        raise ValueError(f'Unknown visual treatment: {kind!r}')
    if kind == 'abstract':
        return ''
    if type(scene_index) is not int or scene_index < 0:
        raise ValueError('Invalid scene index')
    prefix = f'scene-art-{scene_index}'
    body = DRAWERS[kind](prefix)
    desc = html.escape(DESCRIPTIONS[kind], quote=True)
    return f"""<div class="visual-stage" id="visual-{scene_index}" aria-label="{desc}">
<svg class="scene-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" role="img" aria-label="{desc}" preserveAspectRatio="xMidYMid meet">
<defs>
 <linearGradient id="{prefix}-ocean" x1="0" y1="0" x2="1" y2="1">
 <stop offset="0" stop-color="#2B7DAB"/><stop offset="1" stop-color="#10283F"/></linearGradient>
 <linearGradient id="{prefix}-sunset" x1="0" y1="0" x2="0" y2="1">
 <stop offset="0" stop-color="#29315C"/><stop offset=".46" stop-color="#F08B6B"/>
 <stop offset=".67" stop-color="#FFA36B"/><stop offset="1" stop-color="#4A3863"/></linearGradient>
</defs>
{body}
</svg>
<div class="visual-label">{kind.upper()}</div>
</div>"""
