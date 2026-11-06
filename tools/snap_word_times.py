"""Re-time words to the real speech chunks in the narration audio (fixes captions that show before the word is said).

  python -I tools/snap_word_times.py STUDIO_TIMELINE_WORDS_JSON NARRATION_AUDIO [SCRIPT.txt]     rewrites the file (keeps words.orig.json)
  python -I tools/snap_word_times.py --selftest

The ASR stretches or misplaces word starts around pauses (a word is pulled back over the silence, a word it missed gets the
previous word's end). Measured on the titanium-bones narration: starts up to 0.6 s too early after a pause. The audio itself is
clean, so: find the pauses (ffmpeg silencedetect), match each pause to a punctuation mark in the script (order-preserving,
closest to the ASR's idea of where it is), and spread the words of each chunk over the chunk's real voiced span by spoken length.
Then the local whisper is run on each chunk alone (no pause to stretch over), which times the words inside it; chunk starts and ends are exact.
"""
import json, pathlib, re, shutil, subprocess, sys

MIN_PAUSE = 0.25
PUNCT = {".": 0, "?": 0, "!": 0, ",": 0.15, ";": 0.15, ":": 0.15}


def silences(audio, noise=-38, dur=0.18):
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(audio), "-af", f"silencedetect=noise={noise}dB:d={dur}", "-f", "null", "-"], capture_output=True, text=True)
    s = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    e = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    total = re.findall(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr)
    dur_all = int(total[0][0]) * 3600 + int(total[0][1]) * 60 + float(total[0][2]) if total else 1e9
    e += [dur_all] * (len(s) - len(e))                     # a trailing silence has no end line
    out = []
    for a, b in zip(s, e):                                 # a voiced blip under 0.12 s (a click or leftover noise) is not speech
        if out and a - out[-1][1] < 0.12: out[-1] = (out[-1][0], b)
        else: out.append((a, b))
    return out, dur_all


def weight(w):
    t = re.sub(r"[^A-Za-z0-9']", "", w)
    return 14 if t.isdigit() else max(2, len(t)) + 1.5


def chunk_starts(words, starts, pauses, para_ends=()):
    """Index of the first word after each pause (order-preserving DP, cost = ASR start vs the pause end)."""
    n, K = len(words), len(pauses)
    pen = [PUNCT.get(w.strip()[-1:], 2.5) for w in words]
    INF = 1e9
    # boundary after word p; a script paragraph end next to a long pause is the surest anchor
    cost = lambda k, p: abs(starts[p + 1] - pauses[k][1]) + pen[p] - (1.0 if p in para_ends and pauses[k][1] - pauses[k][0] >= 0.6 else 0)
    dp = [[INF] * (n - 1) for _ in range(K)]; back = [[-1] * (n - 1) for _ in range(K)]
    for k in range(K):
        best, arg = INF, -1
        for p in range(n - 1):
            if k == 0: dp[0][p] = cost(0, p)
            else:
                if p >= 1 and dp[k - 1][p - 1] < best: best, arg = dp[k - 1][p - 1], p - 1
                if best < INF: dp[k][p] = best + cost(k, p); back[k][p] = arg
    p = min(range(n - 1), key=lambda q: dp[K - 1][q]); out = [0] * K
    for k in range(K - 1, -1, -1): out[k] = p + 1; p = back[k][p]
    return out


def retime(words, starts, sil, dur_all, para_ends=(), chunk_times=None):
    """-> (starts, ends)."""
    speech_end = dur_all
    pauses = []
    for s, e in sil:
        if e >= dur_all - 0.1: speech_end = s                  # trailing silence
        elif e - s >= MIN_PAUSE and s > 0.3: pauses.append((s, e))
    first = sil[0][1] if sil and sil[0][0] < 0.05 and sil[0][1] < 0.6 else 0.0
    idx = chunk_starts(words, starts, pauses, para_ends)
    bounds = [0] + idx + [len(words)]
    spans = [(first, pauses[0][0] if pauses else speech_end)] + [(pauses[k][1], pauses[k + 1][0] if k + 1 < len(pauses) else speech_end) for k in range(len(pauses))]
    ns, ne = [0.0] * len(words), [0.0] * len(words)
    for c, (a, b) in enumerate(spans):
        ws = list(range(bounds[c], bounds[c + 1])); tot = sum(weight(words[i]) for i in ws); acc = 0.0
        for i in ws:                                                   # fallback: spread by spoken length
            ns[i] = a + (b - a) * acc / tot; acc += weight(words[i]); ne[i] = a + (b - a) * acc / tot
        if chunk_times:
            t = chunk_times(words[bounds[c]:bounds[c + 1]], a, b)
            if t:
                for k, i in enumerate(ws): ns[i] = t[k]
                for k, i in enumerate(ws): ne[i] = t[k + 1] if k + 1 < len(ws) else b
    return ns, ne, [(words[i], spans[c][0], spans[c][1]) for c, i in enumerate(bounds[:-1])]


def whisper_chunk(audio, repo):
    """chunk_times(words, a, b) -> start of each word, from the local whisper run on just that chunk (no pause to stretch over)."""
    import tempfile
    sys.path.insert(0, str(repo)); import build
    def f(words, a, b):
        with tempfile.TemporaryDirectory() as tmp:
            wav = pathlib.Path(tmp) / "c.wav"; lo = max(0.0, a - 0.08)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{lo}", "-t", f"{b - lo + 0.08}", "-i", str(audio), "-ac", "1", "-ar", "16000", str(wav)], check=True)
            subprocess.run([sys.executable, "-I", str(repo / "tools" / "whisper_words.py"), str(wav), "--out", tmp], capture_output=True, check=True)
            asr = json.load(open(pathlib.Path(tmp) / "words.json", encoding="utf-8"))
        t = [lo + x for x in build.align(words, asr)]
        t[0] = a                                                       # the chunk's first word starts when the voice does
        for i in range(1, len(t)): t[i] = min(max(t[i], t[i - 1] + 0.04), b - 0.02 * (len(t) - i))
        return t
    return f


def selftest():
    words = "What if bones? Never break one. You also".split()
    starts = [0.0, 0.3, 0.6, 1.0, 1.9, 2.1, 3.1, 3.4]                 # ASR: "Never" pulled early over the first pause
    ns, ne, _ = retime(words, starts, [(0.9, 1.7), (2.3, 3.0), (3.9, 9.9)], 9.9)
    assert abs(ns[3] - 1.7) < 1e-9 and abs(ns[6] - 3.0) < 1e-9 and ne[2] <= 0.9 + 1e-9 and ne[5] <= 2.3 + 1e-9 and ne[7] <= 3.9 + 1e-9, (ns, ne)
    print("selftest ok")


def main():
    if sys.argv[1:2] == ["--selftest"]: return selftest()
    if len(sys.argv) not in (3, 4): sys.exit(__doc__)
    f, audio = pathlib.Path(sys.argv[1]), sys.argv[2]
    ends, n = set(), 0
    if len(sys.argv) == 4:                                            # script.txt: paragraph ends anchor the long pauses
        for para in re.split(r"\n\s*\n", open(sys.argv[3], encoding="utf-8-sig").read().strip()):
            n += len(para.split()); ends.add(n - 1)
    d = json.load(open(f, encoding="utf-8")); ws = d["words"]
    orig = f.with_name("words.orig.json")
    if not orig.exists(): shutil.copy(f, orig)
    ws = json.load(open(orig, encoding="utf-8"))["words"]            # always re-time from the untouched ASR times
    sil, dur_all = silences(audio)
    wc = whisper_chunk(audio, pathlib.Path(__file__).resolve().parent.parent)
    def chunk_fn(words, a, b):
        # A compressed read leaves sub-second mouth pauses after commas: tiny chunks (2 words, 0.5 s) are mostly a
        # digit/clip that whisper cannot match textually. Their edges are already exact from silencedetect, so the
        # weight-spread fallback is fine for them; whisper only re-times chunks big enough for it to bite.
        return wc(words, a, b) if len(words) >= 3 and (b - a) >= 1.0 else None
    ns, ne, chunks = retime([w["word"] for w in ws], [w["start"] for w in ws], sil, dur_all, ends, chunk_fn)
    for w, a, b in zip(ws, ns, ne): w["start"], w["end"] = round(a, 3), round(b, 3)
    json.dump({**d, "words": ws}, open(f, "w", encoding="utf-8"), indent=1)
    for first, a, b in chunks: print(f"{a:6.2f}-{b:6.2f}  starts with {first!r}")


if __name__ == "__main__":
    main()
