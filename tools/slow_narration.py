"""Slow down (or speed up) an episode's narration without re-recording: instant, no Gemini quota, pitch kept.

  python -I tools/slow_narration.py episodes/NAME --factor 0.9      # 0.9 = 10% slower (useful range 0.8-1.2)
  python -I tools/slow_narration.py episodes/NAME --restore          # back to the original

The first run keeps the untouched file as narration.orig.<ext>. Old timings are deleted so the next build re-times every scene.
For a different delivery (not just slower) re-record a take with flow_narrate_redo instead, then rebuild.
"""
import argparse, pathlib, shutil, subprocess, sys

ap = argparse.ArgumentParser()
ap.add_argument("episode")
ap.add_argument("--factor", type=float)
ap.add_argument("--restore", action="store_true")
a = ap.parse_args()
ep = pathlib.Path(a.episode)
cur = next((p for e in ("wav", "mp3", "m4a") for p in ep.glob(f"narration.{e}")), None)
orig = next(iter(ep.glob("narration.orig.*")), None)
if a.restore:
    if not orig:
        sys.exit("no narration.orig.* to restore")
    if cur: cur.unlink()
    shutil.move(orig, ep / orig.name.replace("narration.orig.", "narration."))
elif a.factor:
    if not 0.5 <= a.factor <= 2:
        sys.exit("--factor must be between 0.5 and 2")
    if not cur and not orig:
        sys.exit(f"no narration.* in {ep}")
    src = orig or cur
    if not orig:
        orig = ep / f"narration.orig{cur.suffix}"; shutil.move(cur, orig); src = orig
    out = ep / f"narration{src.suffix.replace('.orig', '')}"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter:a", f"atempo={a.factor}", out], check=True)
else:
    sys.exit(__doc__)
shutil.rmtree(ep / "timings", ignore_errors=True)
(ep / "timings.json").unlink(missing_ok=True)
print("narration updated; rebuild: build.py (modes A/B re-time automatically) or to_studio.py + retime_shots.py (Cinema-2D)")
