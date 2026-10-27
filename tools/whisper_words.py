#!/usr/bin/env python3
"""Word-level transcript from the local ggml whisper model, no download, no paid API.

  whisper_words.py MEDIA [--model small.en|tiny.en] [--out DIR]

Writes DIR/words.json  [{"text","start","end"}] seconds   -> timeline_view.py --words
       DIR/transcript.json {"language","speakers","words":[{text,start,end} in ticks]}
                                                          -> FilmCraft `transcript.set {item, transcript}`
Why: FilmCraft's own transcript.generate wants a model in %APPDATA%\\FilmCraft\\models (empty here);
the ggml models already live in %LOCALAPPDATA%\\app.concat.editor\\whisper-models.
ffmpeg's whisper filter gives either whole segments (real spaces) or sub-word tokens (no spaces), so we
run both and align tokens to the segment words by character count.
"""
import argparse, json, os, re, subprocess, sys, tempfile

TICKS = 254016000000
MODELS = os.environ.get("WHISPER_MODELS") or os.path.expandvars(r"%LOCALAPPDATA%\app.concat.editor\whisper-models")  # folder holding ggml-small.en.bin


def run(media, model, maxlen, dest):
    m = model.replace("\\", "/").replace(":", r"\:")
    af = f"whisper=model='{m}':language=en:format=json:destination={os.path.basename(dest)}" + (f":max_len={maxlen}" if maxlen else "")
    env = dict(os.environ, MSYS_NO_PATHCONV="1")
    r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", media, "-vn", "-af", af, "-f", "null", "-"],
                       capture_output=True, text=True, env=env, cwd=os.path.dirname(dest))  # relative destination: no drive-colon escaping
    if r.returncode:
        sys.exit(r.stderr)
    return [json.loads(l) for l in open(dest, encoding="utf-8") if l.strip()]


def main():
    a = argparse.ArgumentParser()
    a.add_argument("media")
    a.add_argument("--model", default="small.en")
    a.add_argument("--out", default=".")
    o = a.parse_args()
    model = os.path.join(MODELS, f"ggml-{o.model}.bin")
    if not os.path.exists(model):
        sys.exit(f"missing {model}")
    os.makedirs(o.out, exist_ok=True)
    media = os.path.abspath(o.media)
    tmp = tempfile.mkdtemp()
    segs = run(media, model, 0, os.path.join(tmp, "seg.json").replace("\\", "/"))
    toks = run(media, model, 1, os.path.join(tmp, "tok.json").replace("\\", "/"))

    words, i = [], 0
    for w in " ".join(s["text"].strip() for s in segs).split():
        first = i
        have = ""
        while i < len(toks) and len(have) < len(w):
            have += toks[i]["text"].strip()
            i += 1
        if i == first:  # ran out of tokens; keep text, reuse the last end
            t = toks[-1]["end"]
            words.append({"text": w, "start": t / 1000, "end": t / 1000})
            continue
        words.append({"text": w, "start": toks[first]["start"] / 1000, "end": toks[i - 1]["end"] / 1000})
    for a_, b_ in zip(words, words[1:]):  # whisper token times can overlap by a few ms
        a_["end"] = min(a_["end"], b_["start"]) if b_["start"] >= a_["start"] else a_["end"]

    json.dump(words, open(os.path.join(o.out, "words.json"), "w", encoding="utf-8"), indent=1)
    tr = {"language": "en", "speakers": [{"name": "Speaker 1"}],
          "words": [{"text": w["text"], "start": round(w["start"] * TICKS), "end": round(w["end"] * TICKS), "speaker": 0} for w in words]}
    json.dump(tr, open(os.path.join(o.out, "transcript.json"), "w", encoding="utf-8"))
    print(len(words), "words;", " ".join(w["text"] for w in words)[:300])


if __name__ == "__main__":
    main()
