"""Draw the profile header: a typographic name treatment with a line that draws
itself, a tagline that types out, and a blinking cursor.

Usage: python profile_header.py <output-dir>
Writes header.svg (light) and header-dark.svg (dark). Standard library only.
"""
import os
import sys

NAME = "Yatharth Jha"
TAGLINE = "high impact, low footprint"
PATH = "~/mumbai/yatharth"

THEMES = {
    "light": dict(fg="#1f2328", muted="#59636e", accent="#cf222e", rule="#d1d9e0"),
    "dark": dict(fg="#f0f6fc", muted="#9198a1", accent="#f85149", rule="#3d444d"),
}

SANS = ('-apple-system,BlinkMacSystemFont,&quot;Segoe UI&quot;,&quot;Noto Sans&quot;,'
        'Helvetica,Arial,sans-serif')
MONO = 'ui-monospace,SFMono-Regular,&quot;SF Mono&quot;,Menlo,Consolas,monospace'

W, H = 900, 210


def render(theme):
    t = THEMES[theme]
    tag_w = 292                         # the tagline is forced to this width (textLength)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{NAME} — {TAGLINE}">
<style>
.p{{font:13px {MONO};fill:{t['muted']};letter-spacing:.5px}}
.n{{font:300 60px {SANS};fill:{t['fg']};letter-spacing:-1.5px}}
.t{{font:400 14px {SANS};fill:{t['muted']};letter-spacing:3px;text-transform:uppercase}}
.r{{stroke:{t['accent']};stroke-width:2;stroke-linecap:round;stroke-dasharray:140;stroke-dashoffset:140;animation:draw 1.1s cubic-bezier(.65,0,.35,1) .2s forwards}}
.c{{fill:{t['accent']};animation:blink 1s steps(1) 2.4s infinite;opacity:0}}
.m{{animation:reveal 1.4s steps(26) 1.1s forwards}}
.hair{{stroke:{t['rule']};stroke-width:1}}
.f{{opacity:0;animation:fade .6s ease-out forwards}}
.d1{{animation-delay:.1s}}.d2{{animation-delay:.5s}}
@keyframes draw{{to{{stroke-dashoffset:0}}}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:0}}}}
@keyframes reveal{{from{{width:0}}to{{width:{tag_w:.0f}px}}}}
@keyframes fade{{to{{opacity:1}}}}
</style>
<defs><clipPath id="k"><rect class="m" x="0" y="120" width="0" height="40"/></clipPath></defs>
<text class="p f d1" x="0" y="34">{PATH}</text>
<text class="n f d2" x="-3" y="98">{NAME}</text>
<line class="r" x1="2" y1="118" x2="140" y2="118"/>
<g clip-path="url(#k)"><text class="t" x="0" y="150" textLength="{tag_w}" lengthAdjust="spacing">{TAGLINE}</text></g>
<rect class="c" x="{tag_w + 6:.0f}" y="138" width="7" height="15"/>
<line class="hair" x1="0" y1="{H - 1}" x2="{W}" y2="{H - 1}"/>
</svg>
"""


def main():
    out_dir = sys.argv[1]
    os.makedirs(out_dir, exist_ok=True)
    for theme, name in (("light", "header.svg"), ("dark", "header-dark.svg")):
        with open(os.path.join(out_dir, name), "w", encoding="utf-8") as f:
            f.write(render(theme))
    print(f"header -> {out_dir}")


if __name__ == "__main__":
    main()
