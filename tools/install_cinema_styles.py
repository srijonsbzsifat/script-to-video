"""Add our style packs (styles/cinema2d/packs/*.json) to an installed aiTrends-style 2D studio kit.

  python -I tools/install_cinema_styles.py N:/AI/aitrends-2d-studio

Appends one marked block to <studio>/engine/styles.js (replaced on re-run, the original styles are untouched).
A pack lists the 5 core moods (day golden dusk night storm); the other three are derived:
interiorWarm <- golden walls/floors, interiorCool <- night, void <- pack["void"] (blueprint/diagram background).
"""
import json, pathlib, re, sys

BEGIN, END = "// >>> script-to-video custom styles (generated, do not edit)", "// <<< script-to-video custom styles"


def derive(p):
    m = p["moods"]
    m["interiorWarm"] = {**m["golden"], "sky": m["golden"]["sky"]}
    m["interiorCool"] = {**m["night"]}
    v = p["void"]
    m["void"] = {**m["day"], "sky": [v["bg"], v["bg2"]], "wall": v["bg"], "floor": v["bg2"], "dark": v["line"], "key": "#ffffff", "rim": v["line"], "fog": v["bg2"]}
    return {k: p[k] for k in ("name", "desc", "ink", "inkFar", "feature", "rimWidth", "ui", "grade", "moods")}


def main(studio):
    studio = pathlib.Path(studio)
    f = studio / "engine" / "styles.js"
    if not f.exists():
        sys.exit(f"{f} not found: is this the studio folder?")
    packs = {}
    for pf in sorted((pathlib.Path(__file__).parent.parent / "styles" / "cinema2d" / "packs").glob("*.json")):
        p = json.load(open(pf, encoding="utf-8"))
        packs[p["id"]] = derive(p)
    src = f.read_text(encoding="utf-8")
    src = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n?", "", src, flags=re.S)
    block = f"{BEGIN}\nObject.assign(STYLES, {json.dumps(packs)});\n{END}\n"
    f.write_text(src.rstrip("\n") + "\n" + block, encoding="utf-8")
    print("installed styles:", ", ".join(packs), "->", f)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
