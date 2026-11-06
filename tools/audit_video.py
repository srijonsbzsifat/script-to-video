"""Generic audit of any rendered video (ideas from the stickman skill's audit.py): python -I tools/audit_video.py FILE.mp4 [--shots shots.json | --cuts 2.1,4.8] [--target -14]
Checks: pops (a sudden jump that is not a known cut), frozen 1 s windows, loudness/peak against a target, silent gaps, and writes <FILE>_contact.jpg (12 frames).
Pop and cut checks need the real cuts (--shots reads shots[].start from a Cinema-2D shots.json); without them every jump is listed as INFO only.
Not covered: determinism (needs the renderer) and rig checks (foot skate, hand reach). Exit code 1 if there are ISSUES."""
import argparse, json, pathlib, re, subprocess, sys
import numpy as np

ap = argparse.ArgumentParser(); ap.add_argument("video"); ap.add_argument("--shots"); ap.add_argument("--cuts")
ap.add_argument("--target", type=float, default=-14.0, help="LUFS target (Cinema-2D mix: -14)")
ap.add_argument("--still", type=float, default=0.2, help="mean frame change per 1 s window below this = frozen")
ap.add_argument("--silence", type=float, default=1.5, help="silent gap length in s that counts as an issue")
o = ap.parse_args(); mp4 = pathlib.Path(o.video).resolve()


def run(*a):
    return subprocess.run(["ffmpeg", "-hide_banner", *a], capture_output=True)


p = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate,nb_frames:format=duration", "-of", "json", str(mp4)], capture_output=True, text=True)
j = json.loads(p.stdout); st = j["streams"][0]; dur = float(j["format"]["duration"]); n_, d_ = map(int, st["r_frame_rate"].split("/")); fps = n_ / d_
print(f"{mp4.name}: {st['width']}x{st['height']}, {fps:g} fps, {dur:.1f} s")
iss, info = [], []

cuts = None
if o.shots:
    cuts = [float(s["start"]) for s in json.load(open(o.shots, encoding="utf-8"))["shots"]]
elif o.cuts:
    cuts = [float(x) for x in o.cuts.split(",")]

raw = run("-v", "error", "-i", str(mp4), "-vf", "scale=320:180,format=gray", "-f", "rawvideo", "-").stdout
fr = np.frombuffer(raw, np.uint8)
fr = fr[: len(fr) // 57600 * 57600].reshape(-1, 180, 320).astype(np.float32)
d = np.abs(np.diff(fr, axis=0)).mean((1, 2))          # d[i] = change into frame i+1
print(f"decoded {len(fr)} frames, brightness {fr.mean((1, 2)).min():.0f}..{fr.mean((1, 2)).max():.0f}")

for i, v in enumerate(d):
    t = (i + 1) / fps
    if v > 6 and 1 / fps < t < dur - 1 / fps:
        near = cuts is not None and any(abs(t - c) < 2.5 / fps for c in cuts)
        if near: continue
        (iss if cuts is not None else info).append(f"{'pop' if cuts is not None else 'jump'} at {t:.2f}s (change {v:.1f})")

lo = 1e9; w = int(round(fps))
for s in range(w, max(w + 1, len(d) - 2 * w), w):
    win = d[s:s + w]
    m, fz = float(win.mean()), float((win < .05).mean()); lo = min(lo, m)
    if m < o.still or fz > .1: iss.append(f"still window at {s / fps:.1f}s (motion {m:.2f}, frozen frames {fz:.0%})")
print(f"lowest 1 s motion {lo:.2f}")

r = run("-i", str(mp4), "-af", "ebur128=peak=true", "-f", "null", "-").stderr.decode(errors="ignore")
tail = r[r.rfind("Summary:"):]
g = lambda pat: (re.findall(pat, tail) or [None])[0]
I, lra, pk = g(r"I:\s+(-?[\d.]+)"), g(r"LRA:\s+([\d.]+)"), g(r"Peak:\s+(-?[\d.]+)")
print(f"sound: {I} LUFS (target {o.target:g}), range {lra} LU, peak {pk} dBFS")
if I is None: iss.append("no audio stream or loudness could not be measured")
else:
    if abs(float(I) - o.target) > 2: iss.append(f"loudness {I} LUFS is more than 2 off the {o.target:g} target")
    if float(pk) > -1: iss.append(f"peak {pk} dBFS is above -1")
    sd = run("-i", str(mp4), "-af", f"silencedetect=noise=-50dB:d={o.silence}", "-f", "null", "-").stderr.decode(errors="ignore")
    for a, b in zip(re.findall(r"silence_start: ([\d.]+)", sd), re.findall(r"silence_end: ([\d.]+)", sd) + [str(dur)]):
        iss.append(f"silent gap {float(a):.1f}-{float(b):.1f}s ({float(b) - float(a):.1f} s)")

sheet = mp4.with_name(mp4.stem + "_contact.jpg")
run("-y", "-v", "error", "-i", str(mp4), "-vf", f"fps=12/{dur:.3f},scale=360:-1,tile=6x2", "-frames:v", "1", "-update", "1", str(sheet))
print(f"contact sheet: {sheet} (look at it before delivering)")

for x in info[:10]: print("INFO", x)
if len(info) > 10: print(f"INFO ... {len(info) - 10} more jumps (no --shots/--cuts given, so cuts are not separated from pops)")
print("ISSUES", len(iss))
for x in iss: print("  " + x)
sys.exit(1 if iss else 0)
