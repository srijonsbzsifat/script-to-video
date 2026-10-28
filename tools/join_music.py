"""Join several Flow Music tracks into one bed of the video's length: loudness-matched, crossfaded, faded in and out.

  python -I tools/join_music.py OUT.mp3 --length 372 track1.mp3 track2.mp3 [track3.m4a ...] [--xfade 4]

Flow Music tracks come out 2-3.5 minutes long whatever length you ask for, so a 5-7 minute video needs 2-3 of them.
Each track is normalised to the same loudness first (raw tracks differed by up to 10 dB), joined with an equal-power-ish
triangle crossfade, trimmed to --length, with a 1.5 s fade-in and a 3 s fade-out. Put the result in the episode as music.mp3.
"""
import argparse, subprocess, sys


def probe(f):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f], capture_output=True, text=True, check=True).stdout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("tracks", nargs="+")
    ap.add_argument("--length", type=float, required=True, help="seconds (video length)")
    ap.add_argument("--xfade", type=float, default=4.0)
    a = ap.parse_args()
    total = sum(probe(t) for t in a.tracks) - a.xfade * (len(a.tracks) - 1)
    if total < a.length:
        sys.exit(f"tracks give {total:.0f}s after crossfades but the video needs {a.length:.0f}s: add another track")
    inputs = [x for t in a.tracks for x in ("-i", t)]
    norm = ";".join(f"[{i}]loudnorm=I=-20:TP=-2:LRA=7,aresample=48000[n{i}]" for i in range(len(a.tracks)))
    chain, last = [], "n0"
    for i in range(1, len(a.tracks)):
        chain.append(f"[{last}][n{i}]acrossfade=d={a.xfade}:c1=tri:c2=tri[x{i}]")
        last = f"x{i}"
    fade_out_at = max(a.length - 3, 0)
    chain.append(f"[{last}]atrim=0:{a.length},afade=t=in:d=1.5,afade=t=out:st={fade_out_at}:d=3[o]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join([norm, *chain]), "-map", "[o]", "-ar", "48000", "-b:a", "192k", a.out], check=True)
    print(f"wrote {a.out}: {probe(a.out):.1f}s from {len(a.tracks)} tracks")


if __name__ == "__main__":
    main()
