#!/usr/bin/env python3
"""Build the animated SVG assets for the GitHub profile README.

    python tools/build_assets.py            # writes ./assets/*.svg
    python tools/build_assets.py some_dir   # writes some_dir/*.svg

Edit the CONTENT block below, re-run, commit the four SVGs.
Why a script: the typing effect is ~150 individually timed glyphs, which is
tedious and error-prone to edit by hand. Python 3 standard library only.

Motion design (all CSS, so prefers-reduced-motion freezes it):
  * header: the typed line (one glyph at a time, caret follows) and a very
    slow grid drift. Nothing else moves.
  * divider: one lime tab that slides once per 24 s and rests the rest of
    the time.
Fonts are system stacks on purpose: SVGs shown through <img> cannot load web
fonts. Every glyph of the typed line is placed at an absolute x, so the layout
does not depend on which monospace font the viewer has.
"""
import pathlib
import sys
from xml.sax.saxutils import escape

# --- CONTENT (edit these) ----------------------------------------------------
NAME = "Prathamesh Pal"
POSITION = "Backend and applied AI. Engineer in progress."
PHRASES = [  # keep each under ~36 characters
    "Learning backend architecture",
    "Adding small apps to Project Hub",
    "Studying databases and algorithms",
    "Exploring applied machine learning",
]
# -----------------------------------------------------------------------------

LIME, VIOLET, AMBER = "#C6FF3D", "#8B7CFF", "#FF9F5A"
OBSIDIAN, IVORY = "#101014", "#F0EEE6"

W, H = 860, 300   # header viewBox
PAD = 48          # left margin shared by every element

FONT_SANS = ("'Helvetica Neue',Helvetica,'Nimbus Sans','Liberation Sans',"
             "Arial,sans-serif")
FONT_MONO = ("'JetBrains Mono','SF Mono','IBM Plex Mono',Menlo,Consolas,"
             "'DejaVu Sans Mono','Liberation Mono',monospace")

THEMES = {
    "dark": dict(plate=OBSIDIAN, border="#2A2A31", ink=IVORY, sub="#B4B2AA",
                 grid=IVORY, grid_op=0.06, rule=IVORY, rule_op=0.30,
                 lime_stroke=None, hair="#2F2F37"),
    "light": dict(plate=IVORY, border="#CFCBBB", ink=OBSIDIAN, sub="#4C4B46",
                  grid=OBSIDIAN, grid_op=0.07, rule=OBSIDIAN, rule_op=0.40,
                  lime_stroke=OBSIDIAN, hair="#CFCBBB"),
}

# Typing timeline (seconds). Each phrase owns PHRASE_T of the loop.
PHRASE_T = 6.5    # slot per phrase
LEAD = 0.5        # caret idles (blinking) before typing starts
DT = 0.055        # seconds per character
HOLD_END = 6.0    # phrase stays fully visible until this offset in its slot
FADE = 0.3        # then fades out
VISIBLE = 6.0     # how long each glyph stays lit after it appears
T = PHRASE_T * len(PHRASES)   # full loop length
FONT_PX = 28
CHAR_W = 0.6 * FONT_PX        # monospace advance used for absolute placement


def pct(t):
    """Seconds -> keyframe percentage of the loop."""
    return f"{t / T * 100:.3f}".rstrip("0").rstrip(".")


def lime_paint(c):
    s = f'fill="{LIME}"'
    if c["lime_stroke"]:
        s += f' stroke="{c["lime_stroke"]}" stroke-width="1.2"'
    return s


def header(theme):
    c = THEMES[theme]
    x0, base = PAD + 28, 246           # typed line start and baseline
    css, typed = [], []

    css += [
        f".nm{{font-family:{FONT_SANS};font-weight:800;font-size:76px;"
        f"letter-spacing:-1.5px}}",
        f".ps{{font-family:{FONT_SANS};font-weight:400;font-size:24px}}",
        f".ch{{font-family:{FONT_MONO};font-weight:500;font-size:{FONT_PX}px;"
        f"animation:pop {T:g}s linear infinite backwards}}",
        ".grid{animation:drift 64s linear infinite}",
        ".cr{animation:bl 1.1s steps(1,end) infinite}",
        "@keyframes drift{to{transform:translate(40px,40px)}}",
        "@keyframes bl{0%{opacity:1}50%{opacity:0}}",
        # a glyph is lit for VISIBLE seconds after its own delay
        f"@keyframes pop{{0%{{opacity:0}}.01%{{opacity:1}}"
        f"{pct(VISIBLE)}%{{opacity:1}}{pct(VISIBLE + 0.01)}%{{opacity:0}}"
        f"100%{{opacity:0}}}}",
    ]

    for k, text in enumerate(PHRASES):
        n = len(text)
        slot = k * PHRASE_T
        start = slot + LEAD
        end = start + n * DT
        assert end < slot + HOLD_END - 1, f"phrase too long: {text!r}"
        dist = n * CHAR_W

        # phrase visibility window
        if k == 0:
            g = (f"0%{{opacity:1}}{pct(slot + HOLD_END)}%{{opacity:1}}"
                 f"{pct(slot + HOLD_END + FADE)}%{{opacity:0}}100%{{opacity:0}}")
        else:
            g = (f"0%{{opacity:0}}{pct(slot)}%{{opacity:0}}"
                 f"{pct(slot + 0.01)}%{{opacity:1}}"
                 f"{pct(slot + HOLD_END)}%{{opacity:1}}"
                 f"{pct(slot + HOLD_END + FADE)}%{{opacity:0}}100%{{opacity:0}}")
        css.append(f"@keyframes g{k}{{{g}}}")
        css.append(f".g{k}{{animation:g{k} {T:g}s linear infinite}}")

        # caret: jumps one cell per character, in lockstep with the glyph delays
        css.append(
            f"@keyframes c{k}{{0%{{transform:translateX(0px)}}"
            f"{pct(start)}%{{transform:translateX(0px);"
            f"animation-timing-function:steps({n},end)}}"
            f"{pct(end)}%{{transform:translateX({dist:.1f}px)}}"
            f"100%{{transform:translateX({dist:.1f}px)}}}}")
        css.append(f".cg{k}{{animation:c{k} {T:g}s linear infinite}}")

        glyphs = []
        for i, ch in enumerate(text):
            if ch == " ":
                continue
            delay = start + (i + 1) * DT
            glyphs.append(
                f'<text class="ch" x="{x0 + i * CHAR_W:.1f}" y="{base}" '
                f'style="animation-delay:{delay:.3f}s">{escape(ch)}</text>')

        # static attributes = the reduced-motion / no-CSS fallback:
        # phrase 0 fully typed, caret at its end, other phrases hidden.
        shown = ' opacity="0"' if k else ""
        caret_x = dist if k == 0 else 0
        typed.append(
            f'<g class="g{k}"{shown}>' + "".join(glyphs) +
            f'<g class="cg{k}" transform="translate({caret_x:.1f} 0)">'
            f'<rect class="cr" x="{x0}" y="{base - 23}" width="11" height="29" '
            f'{lime_paint(c)}/></g></g>')

    css.append("@media (prefers-reduced-motion:reduce)"
               "{.ch,.grid,.cr,[class^=g],[class^=cg]{animation:none!important}}")

    grid_d = ("".join(f"M{x} -40V340" for x in range(-40, W + 41, 40)) +
              "".join(f"M-40 {y}H{W + 40}" for y in range(-40, H + 41, 40)))
    ticks = "".join(f"M{x + .5} 186V194" for x in range(PAD, W - PAD + 1, 40))
    alt_phrases = "; ".join(PHRASES)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
<title id="t">{escape(NAME)}</title>
<desc id="d">{escape(POSITION)} Currently: {escape(alt_phrases)}.</desc>
<defs>
<linearGradient id="fade" x1="0" y1="0" x2="1" y2="0">
<stop offset="0" stop-color="{c['plate']}"/>
<stop offset=".55" stop-color="{c['plate']}" stop-opacity=".88"/>
<stop offset="1" stop-color="{c['plate']}" stop-opacity="0"/>
</linearGradient>
<clipPath id="clip"><rect width="{W}" height="{H}"/></clipPath>
</defs>
<style>{"".join(css)}</style>
<rect width="{W}" height="{H}" fill="{c['plate']}"/>
<g clip-path="url(#clip)"><g class="grid"><path d="{grid_d}" fill="none" stroke="{c['grid']}" stroke-opacity="{c['grid_op']}"/></g></g>
<rect width="{W}" height="{H}" fill="url(#fade)"/>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" fill="none" stroke="{c['border']}"/>
<rect x="{PAD}" y="30" width="32" height="5" {lime_paint(c)}/>
<text class="nm" x="{PAD}" y="118" fill="{c['ink']}">{escape(NAME)}</text>
<text class="ps" x="{PAD}" y="158" fill="{c['sub']}">{escape(POSITION)}</text>
<path d="M{PAD} 190.5H{W - PAD}{ticks}" fill="none" stroke="{c['rule']}" stroke-opacity="{c['rule_op']}" shape-rendering="crispEdges"/>
<g fill="none" stroke="{VIOLET}" stroke-width="1.4"><circle cx="772" cy="84" r="11"/><path d="M748 84H796M772 60V108"/></g>
<rect x="{PAD}" y="233" width="9" height="9" fill="{AMBER}"/>
<g fill="{c['ink']}">{"".join(typed)}</g>
</svg>
'''


def divider(theme):
    c = THEMES[theme]
    w, h = 860, 20
    ticks = "".join(f"M{x + .5} 7V13" for x in range(0, w + 1, 40))
    css = (
        ".gl{animation:gl 24s cubic-bezier(.45,0,.2,1) infinite}"
        "@keyframes gl{0%{transform:translateX(0px);opacity:1}"
        "40%{transform:translateX(796px);opacity:1}"
        "43%{transform:translateX(796px);opacity:0}"
        "43.01%{transform:translateX(0px);opacity:0}"
        "48%{transform:translateX(0px);opacity:1}"
        "100%{transform:translateX(0px);opacity:1}}"
        "@media (prefers-reduced-motion:reduce){.gl{animation:none}}")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="presentation" aria-hidden="true">
<style>{css}</style>
<path d="M0 10.5H{w}{ticks}" fill="none" stroke="{c['hair']}" shape-rendering="crispEdges"/>
<rect x="{w - 4}" y="8" width="4" height="4" fill="{VIOLET}"/>
<rect class="gl" x="0" y="8" width="64" height="4" {lime_paint(c)}/>
</svg>
'''


def main():
    out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "assets")
    out.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        for name, fn in (("header", header), ("divider", divider)):
            path = out / f"{name}-{theme}.svg"
            path.write_text(fn(theme), encoding="utf-8")
            print(f"{path}  {path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
