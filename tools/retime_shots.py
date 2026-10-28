"""Re-time a Cinema-2D shot list after the narration changed (slower read, one re-recorded take, a edited scene).

  python -I tools/retime_shots.py <studio>/projects/NAME

Needs timeline/words.prev.json (saved by to_studio.py before it re-timed) and the new timeline/words.json. The script words are
the same, so word k is the same word before and after: every time in story/shots.json (shot start/end, music sections, global
sfx cues) is moved with a piecewise-linear map old-time -> new-time through all the word start times. Shots keep their length
in words, scenes keep their sets and code; only the clock changes. Then re-render: node render.mjs --project ... (free).
"""
import bisect, json, pathlib, sys


def load(p):
    d = json.load(open(p, encoding="utf-8"))
    return d["words"] if isinstance(d, dict) else d


def main(proj):
    proj = pathlib.Path(proj)
    old, new = load(proj / "timeline" / "words.prev.json"), load(proj / "timeline" / "words.json")
    if len(old) != len(new):
        sys.exit(f"the script changed ({len(old)} words before, {len(new)} now): re-time by hand, or re-plan the affected shots")
    xs = [0.0] + [w["start"] for w in old] + [old[-1]["end"]]
    ys = [0.0] + [w["start"] for w in new] + [new[-1]["end"]]
    for i in range(1, len(xs)):                       # strictly increasing
        xs[i] = max(xs[i], xs[i - 1] + 1e-6); ys[i] = max(ys[i], ys[i - 1] + 1e-6)

    def f(t):
        if t <= 0: return 0.0
        if t >= xs[-1]: return round(t + (ys[-1] - xs[-1]), 3)
        i = bisect.bisect_right(xs, t) - 1
        return round(ys[i] + (t - xs[i]) * (ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]), 3)

    sf = proj / "story" / "shots.json"
    s = json.load(open(sf, encoding="utf-8"))
    old_dur = s["duration"]
    for sh in s["shots"]:
        sh["start"], sh["end"] = f(sh["start"]), f(sh["end"])
    for m in s.get("music", []):
        m["start"], m["end"] = f(m["start"]), f(m["end"])
    for c in s.get("sfx", []):
        c["t"] = f(c["t"])
    s["duration"] = s["shots"][-1]["end"]
    for a, b in zip(s["shots"], s["shots"][1:]):      # contiguous
        b["start"] = a["end"]
    json.dump(s, open(sf, "w", encoding="utf-8"), indent=1)
    print(f"re-timed {len(s['shots'])} shots: {old_dur:.1f}s -> {s['duration']:.1f}s. Now render again (render.mjs, then audio/mix.py).")


if __name__ == "__main__":
    main(sys.argv[1]) if len(sys.argv) == 2 else print(__doc__)
