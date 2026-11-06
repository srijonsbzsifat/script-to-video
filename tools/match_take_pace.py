#!/usr/bin/env python3
"""Give every Gemini take the same pace: time-stretch (pitch kept) the takes whose words/second differs from the target.

  python -I tools/match_take_pace.py episodes/NAME [--target 2.82] [--tol 0.02] [--dry]
  python -I tools/match_take_pace.py episodes/NAME --restore

Target = the pace of take 1 (the opening, which sets the viewer's expectation) unless --target is given. Takes within --tol (2%)
of the target are left alone. Also mutes the end-of-take noise bursts (declick_takes.py). The untouched file is kept as
narration.orig.<ext> and takes.json as takes.orig.json. Afterwards the clock has moved: run tools/to_studio.py again (it re-times
every shot with retime_shots.py), then re-render the shots after the first changed take.
"""
import argparse, json, pathlib, shutil, subprocess, sys, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import declick_takes

ap = argparse.ArgumentParser()
ap.add_argument("episode"); ap.add_argument("--target", type=float); ap.add_argument("--tol", type=float, default=0.02)
ap.add_argument("--dry", action="store_true"); ap.add_argument("--restore", action="store_true")
a = ap.parse_args()
ep = pathlib.Path(a.episode)
cur = next((p for e in ("wav", "mp3", "m4a") for p in ep.glob(f"narration.{e}")), None)
orig = next(iter(ep.glob("narration.orig.*")), None)
if a.restore:
    if not orig: sys.exit("no narration.orig.* to restore")
    if cur: cur.unlink()
    shutil.move(orig, ep / orig.name.replace("narration.orig.", "narration."))
    if (ep / "takes.orig.json").exists(): shutil.move(ep / "takes.orig.json", ep / "takes.json")
    sys.exit("restored; re-run to_studio.py")
src = orig or cur
tk = json.load(open(ep / ("takes.orig.json" if (ep / "takes.orig.json").exists() else "takes.json"), encoding="utf-8"))
takes = tk["takes"]
target = a.target or takes[0]["wps"]
plan = [(t, (target / t["wps"]) if abs(t["wps"] / target - 1) > a.tol else 1.0) for t in takes]
for t, f in plan: print(f"take {t['take']}: {t['wps']:.2f} words/s -> factor {f:.3f} ({t['seconds']:.1f} s -> {t['seconds'] / f:.1f} s)")
if a.dry or all(f == 1.0 for _, f in plan): sys.exit(0)

tmp = pathlib.Path(tempfile.mkdtemp())
clean = tmp / "clean.wav"
declick_takes.main(str(src), str(clean))
parts, labels, pos, new_takes = [], [], 0.0, []
for i, (t, f) in enumerate(plan):
    a0, a1 = t["start"], t["start"] + t["seconds"]
    gap = (takes[i + 1]["start"] - a1) if i + 1 < len(takes) else 0.0
    end = f"atrim=start={a0}:end={a1 + (0 if i + 1 < len(takes) else 5)}" # the last take runs to the end of the file
    parts.append(f"[0:a]{end},asetpts=PTS-STARTPTS" + (f",atempo={f:.5f}" if f != 1.0 else "") + f"[t{i}]")
    labels.append(f"[t{i}]")
    if gap > 0:
        parts.append(f"aevalsrc=0:d={gap:.3f}:s=48000:c=stereo[g{i}]"); labels.append(f"[g{i}]")
    ln = t["seconds"] / f
    new_takes.append({**t, "start": round(pos, 3), "seconds": round(ln, 3), "wps": round(t["words"] / ln, 3), "pace_factor": round(f, 4)})
    pos += ln + gap
fc = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(labels)}:v=0:a=1[out]"
out = ep / f"narration{src.suffix.replace('.orig', '')}"
if not orig:
    shutil.move(cur, ep / f"narration.orig{cur.suffix}"); shutil.copy(ep / "takes.json", ep / "takes.orig.json")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(clean), "-filter_complex", fc, "-map", "[out]", "-c:a", "aac", "-b:a", "192k", str(out)], check=True)
json.dump({**tk, "takes": new_takes}, open(ep / "takes.json", "w", encoding="utf-8"), indent=1)
shutil.rmtree(ep / "timings", ignore_errors=True); (ep / "timings.json").unlink(missing_ok=True)
print(f"wrote {out}; next: python -I tools/to_studio.py {ep}")
