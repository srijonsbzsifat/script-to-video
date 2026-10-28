"""Flag hard-coded neutrals in studio scene files that break light/colour styles.

  python -I tools/lint_style_colors.py N:/AI/aitrends-2d-studio/projects/NAME

Scenes must take colours from mood()/S()/S().ui so a style switch re-themes the video. Data hues (a red wave, a
blue wave) are fine; white, black and near-neutral greys/navy hard-coded in a scene are not. Exit code 1 if any.
"""
import pathlib, re, sys

HEX = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
NAMED = re.compile(r"""['"](white|black)['"]""")
RGBA = re.compile(r"rgba?\(\s*(?:255\s*,\s*255\s*,\s*255|0\s*,\s*0\s*,\s*0)")


def neutral(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return (max(r, g, b) - min(r, g, b)) < 28 or max(r, g, b) < 40 or min(r, g, b) > 232   # grey, near-black, near-white


def main(proj):
    bad = 0
    for f in sorted(pathlib.Path(proj, "scenes").rglob("*.js")):
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            hits = [m.group(0) for m in HEX.finditer(line) if neutral(m.group(0))] + NAMED.findall(line) + RGBA.findall(line)
            if hits:
                bad += 1
                print(f"{f.name}:{n}: {', '.join(map(str, hits))}  <- use S().ui / mood() instead")
    print(f"{bad} line(s) with hard-coded neutrals" if bad else "ok: no hard-coded neutrals")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]) if len(sys.argv) == 2 else print(__doc__) or 2)
