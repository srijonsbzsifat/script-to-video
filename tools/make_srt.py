#!/usr/bin/env python3
"""SRT captions for YouTube and Facebook from the real script and the final audio/video.

  make_srt.py EPISODE_DIR MEDIA [--name NAME]
  make_srt.py --selftest

MEDIA is the file whose clock the captions must match: the FINAL video (or narration.* if the video starts with the narration).
Writes EPISODE_DIR/NAME.en.srt (YouTube) and NAME.en_US.srt (Facebook asks for the locale in the file name).
Text is the exact script (ASR errors do not matter); timing is local whisper aligned to it, via build.align.
"""
import argparse, json, pathlib, re, subprocess, sys, tempfile, textwrap

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import build  # parse_script, align

LINE = 42        # characters per caption line (2 lines per cue)
MAXC = 80        # characters per cue
MINC = 25        # a sentence end only closes a cue once it holds this many characters (merges "Pale. Soft.")
MAXS = 6.0       # seconds per cue
TAIL = 0.6       # a cue stays up this long after its last word starts (bounded by the next cue)


def cues(words, times):
    """[(start, end, text)] from script words and their start times."""
    groups, cur = [], []
    for i, w in enumerate(words):
        cur.append(i)
        txt = " ".join(words[j] for j in cur)
        last = i == len(words) - 1
        nxt = len(txt) + 1 + len(words[i + 1]) if not last else 0
        forced = not last and (nxt > MAXC or times[i + 1] - times[cur[0]] > MAXS)
        if last or (w[-1] in ".?!" and len(txt) >= MINC) or forced:
            if forced:      # too long: close the cue at its last comma or sentence end instead of mid-phrase
                ks = [k for k, j in enumerate(cur[:-1]) if words[j][-1] in ",;:.?!" and len(" ".join(words[x] for x in cur[:k + 1])) >= MINC]
                if ks:
                    groups.append(cur[:ks[-1] + 1]); cur = cur[ks[-1] + 1:]
                    continue
            groups.append(cur); cur = []
    out = []
    for n, g in enumerate(groups):
        a = times[g[0]]
        nxt = times[groups[n + 1][0]] - 0.04 if n + 1 < len(groups) else 1e9
        b = min(nxt, max(times[g[-1]] + TAIL, a + 1.0))
        out.append((a, b, "\n".join(textwrap.wrap(" ".join(words[j] for j in g), LINE))))
    return out


def ts(t):
    ms = round(t * 1000)
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def srt(cs):
    return "".join(f"{i}\n{ts(a)} --> {ts(b)}\n{t}\n\n" for i, (a, b, t) in enumerate(cs, 1))


def selftest():
    words = ("You are sealed inside a steel ball, sinking toward the bottom of the Mariana Trench. It is about two meters wide. "
             "Not hard. Not yet. But in three hours, the water outside will press on every square centimeter with more than a tonne.").split()
    cs = cues(words, [0.5 + 0.4 * i for i in range(len(words))])
    assert len(cs) >= 3 and " ".join(" ".join(c[2].split()) for c in cs) == " ".join(words)
    for k, (a, b, t) in enumerate(cs):
        assert b > a and all(len(x) <= LINE for x in t.split("\n")) and len(t.split("\n")) <= 2, (k, t)
        assert k == 0 or a >= cs[k - 1][1], "overlap"
    assert any(c[2].startswith("Not hard. Not yet.") for c in cs), "short sentences should merge"
    assert ts(3723.456) == "01:02:03,456"
    print("selftest ok:", len(cs), "cues")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("episode", nargs="?")
    p.add_argument("media", nargs="?")
    p.add_argument("--name")
    p.add_argument("--times", help="studio timeline/words.json already re-timed to the audio (tools/snap_word_times.py); skips the whisper pass")
    p.add_argument("--selftest", action="store_true")
    o = p.parse_args()
    if o.selftest:
        return selftest()
    if not (o.episode and o.media):
        p.error("EPISODE_DIR and MEDIA are required")
    ep = pathlib.Path(o.episode).resolve()
    paras, _ = build.parse_script(ep)
    words = [w.lstrip("﻿") for ws in paras for w in ws]
    if o.times:
        tw = json.load(open(o.times, encoding="utf-8"))["words"]
        assert len(tw) == len(words), f"{len(tw)} timed words vs {len(words)} script words"
        times = [w["start"] for w in tw]
    else:
        with tempfile.TemporaryDirectory() as tmp:
            build.run([sys.executable, "-I", str(HERE / "whisper_words.py"), o.media, "--out", tmp])
            asr = json.load(open(pathlib.Path(tmp) / "words.json", encoding="utf-8"))
        times = build.align(words, asr)
    cs = cues(words, times)
    name = o.name or ep.name
    for suffix in ("en", "en_US"):
        (ep / f"{name}.{suffix}.srt").write_text(srt(cs), encoding="utf-8")
    print(f"wrote {len(cs)} cues to {ep / (name + '.en.srt')} and {name}.en_US.srt, last cue ends {ts(cs[-1][1])}")


if __name__ == "__main__":
    main()
