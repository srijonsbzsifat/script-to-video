"""Hand a script-to-video episode to the cinema-2D studio kit (the aiTrends-style code-drawn 2D/3D engine).

  python -I tools/to_studio.py episodes/NAME [--studio PATH] [--style daylight]
                               [--aspect 16:9|9:16] [--res 1080p] [--title "My Title"]

Uses OUR parts: narration.* (any voice), script.txt (exact wording; {tags} are dropped), our local whisper for word
times (no model download), an optional music.* bed (Flow Music), and our extra light/colour style packs.
Creates <studio>/projects/NAME with timeline + draft shot list. Claude then writes story, sets and shots (see
docs/USER-GUIDE.md, mode C) and renders with the studio's render.mjs / audio/mix.py.
"""
import argparse, json, os, pathlib, subprocess, sys
from shutil import copy as shutil_copy

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import build                                   # parse_script, align, run, WHISPER (no side effects on import)
sys.path.insert(0, str(HERE / "tools"))
import install_cinema_styles
from studio import studio_dir


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("--studio", default=None, help="default: STUDIO_DIR, <repo>/studio, or the original N:/AI install")
    ap.add_argument("--style", default="dusk", help="dusk|midnight|golden|neon|storybook (kit) or daylight|paper|candy (ours)")
    ap.add_argument("--aspect", default="16:9", choices=["16:9", "9:16"])
    ap.add_argument("--res", default="1080p", choices=["720p", "1080p", "1440p", "2160p"])
    ap.add_argument("--title", default="")
    a = ap.parse_args()

    ep, studio = pathlib.Path(a.episode).resolve(), studio_dir(a.studio)
    if not (studio / "render.mjs").exists():
        sys.exit(f"studio not found at {studio} (install it first: python -I tools/setup_studio.py --go)")
    audio = next((p for e in ("wav", "mp3", "m4a", "flac", "ogg") for p in ep.glob(f"narration.{e}")), None)
    if not audio:
        sys.exit(f"no narration.* in {ep}")
    install_cinema_styles.main(str(studio))

    # word times from our local whisper, aligned to the real script words (ASR errors do not matter)
    paras, _ = build.parse_script(ep)
    words = [w for p in paras for w in p]
    tdir = ep / "timings"
    tdir.mkdir(exist_ok=True)
    build.run([sys.executable, "-I", build.WHISPER, audio, "--model", "small.en", "--out", tdir])
    asr = json.load(open(tdir / "words.json", encoding="utf-8"))
    st = build.align(words, asr)
    out = [{"word": w, "start": round(st[i], 3), "end": round(min(st[i + 1] if i + 1 < len(st) else st[i] + 0.6, st[i] + 1.5), 3)} for i, w in enumerate(words)]

    slug = ep.name
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    py = lambda *args: subprocess.run([sys.executable, *map(str, args)], cwd=studio, env=env, check=True)
    proj = studio / "projects" / slug
    if not proj.exists():
        py("tools/new_project.py", "--name", slug, "--voice", audio, "--aspect", a.aspect, "--resolution", a.res,
           "--style", a.style, "--title", a.title or slug.replace("-", " ").title())
    for old_v in (proj / "input").glob("voiceover.*"):  # a changed narration (slower, re-recorded take): use the new file
        if old_v.suffix == audio.suffix and old_v.read_bytes() != audio.read_bytes():
            shutil_copy(audio, old_v)
    tl = proj / "timeline" / "words.json"
    if tl.exists():                                     # keep the previous timing so retime_shots.py can move the shots
        import shutil as _sh
        _sh.copy(tl, proj / "timeline" / "words.prev.json")
    json.dump({"words": out}, open(proj / "input" / "words.json", "w"))
    py("tools/parse_script.py", "--project", f"projects/{slug}", "--script", f"projects/{slug}/input/words.json")
    had_story = (proj / "story" / "bible.md").exists()
    shots_backup = (proj / "story" / "shots.json").read_bytes() if had_story and (proj / "story" / "shots.json").exists() else None
    py("tools/beats.py", "--project", f"projects/{slug}")
    if shots_backup:                                    # beats.py rewrote the draft: put our written shot list back, then re-time it
        (proj / "story" / "shots.json").write_bytes(shots_backup)
        subprocess.run([sys.executable, str(HERE / "tools" / "retime_shots.py"), str(proj)], check=True)

    cfgf = proj / "config.json"
    cfg = json.load(open(cfgf, encoding="utf-8"))
    cfg["style"] = a.style
    cfg["duration"] = round(float(build.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", audio]).strip()), 3)
    music = next((p for e in ("mp3", "wav", "m4a") for p in ep.glob(f"music.{e}")), None)
    if music:
        import shutil
        shutil.copy(music, proj / "input" / f"music{music.suffix}")
        cfg["music"] = {**cfg.get("music", {}), "enabled": True, "file": f"input/music{music.suffix}"}
    json.dump(cfg, open(cfgf, "w"), indent=1)
    (proj / "story").mkdir(exist_ok=True)
    (proj / "story" / "brief.md").write_text(
        f"# Brief for {slug}\n- style: {a.style}  aspect: {a.aspect}  resolution: {a.res}\n- narration: input/voiceover (do NOT change wording)\n"
        f"- music: {'input/music' + music.suffix + ' (own bed, do not generate)' if music else 'generated by the kit'}\n"
        f"- scene breaks of our script: {len(paras)} (one idea each, use as shot-group boundaries)\n"
        "- colours: take EVERY colour from mood()/S()/S().ui; no hard-coded white or black (the style may be light)\n", encoding="utf-8")
    print(f"\nproject ready: {proj}\nnext: ask Claude to do stages 4-8 of the studio's make-2d-video skill for projects/{slug}")
    print(f"then: python tools/lint_style_colors.py {proj}   and render a style grid before the full render")


if __name__ == "__main__":
    main()
