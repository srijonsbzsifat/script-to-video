"""Script-to-video builder: episode folder -> final.mp4 via HyperFrames.

  python -I build.py EPISODE_DIR [--no-render]
  python -I build.py EPISODE_DIR --storyboard   storyboard.html: scenes, images, times, tags (no audio needed)
  python -I build.py --new NAME            create episodes/NAME with script.txt + layers/

EPISODE_DIR holds:
  narration.wav|mp3|m4a   the narration (AI Studio or any)
  script.txt              the exact narration text; a BLANK LINE starts a new scene
  s01.png, s02.png, ...   one image per scene, in script order (png/jpg/jpeg/webp/svg)
Output: EPISODE_DIR/final.mp4 (+ EPISODE_DIR/hf/ project, timings.json)
Timing: local whisper -> words aligned to the real script (ASR errors don't matter).
"""
import difflib, json, os, pathlib, re, shutil, subprocess, sys

HERE = pathlib.Path(__file__).parent
WHISPER = HERE / "tools" / "whisper_words.py"
CACHE = HERE / ".cache"
HF = HERE / "node_modules" / ".bin" / ("hyperframes.cmd" if os.name == "nt" else "hyperframes")   # pinned in package.json
GROUP = 3            # words per caption group
HOLD = 1.2           # a group stays up at least this long (bounded by the next group)
FADE = 0.3           # crossfade between scenes
MOTION = ["in", "pan_l", "out", "pan_r"]   # cycled per scene
POP = 0.28           # pop-in seconds (scale 0 -> ~1.1 -> 1, ~8 frames to overshoot)
SFX_VOL = 0.35       # pop / whoosh loudness
MAX_STILL = 4.5      # warn if nothing visual changes for longer than this
WPS = 2.5            # words per second used to estimate scene length in --storyboard
norm = lambda w: re.sub(r"[^a-z0-9']", "", w.lower())


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)
    if r.returncode:
        sys.exit(f"FAILED: {' '.join(map(str, cmd))}\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}")
    return r.stdout


def align(script_words, asr):
    """times[i] = start of script word i; unmatched words are interpolated."""
    a, b = [norm(w) for w in script_words], [norm(w["text"]) for w in asr]
    t = [None] * len(a)
    for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            t[blk.a + k] = asr[blk.b + k]["start"]
    known = [i for i, v in enumerate(t) if v is not None]
    if len(known) < len(a) * 0.5:
        sys.exit(f"Only {len(known)}/{len(a)} script words matched the audio: wrong script or narration?")
    for i in range(len(t)):
        if t[i] is None:
            lo = max((k for k in known if k < i), default=None)
            hi = min((k for k in known if k > i), default=None)
            if lo is None:
                t[i] = 0.1
            elif hi is None:
                t[i] = t[lo] + 0.3 * (i - lo)
            else:
                t[i] = t[lo] + (t[hi] - t[lo]) * (i - lo) / (hi - lo)
    for i in range(1, len(t)):          # monotonic
        t[i] = max(t[i], t[i - 1] + 0.01)
    return t


def parse_script(ep):
    paras, tags = [], []            # tags[scene] = [(index of the word it sits before, "pop:x.png @right")]
    for p in re.split(r"\n\s*\n", (ep / "script.txt").read_text(encoding="utf-8").strip()):
        if not p.strip():
            continue
        ws, ev = [], []
        for m in re.finditer(r"\{([^}]*)\}|([^\s{]+)", p):
            if m.group(1) is not None:
                ev.append((len(ws), m.group(1).strip()))
            else:
                ws.append(m.group(2))
        paras.append(ws); tags.append(ev)
    return paras, tags


def find_images(ep):
    return sorted(p for p in ep.iterdir() if re.fullmatch(r"s\d+\.(png|jpe?g|webp|svg)", p.name, re.I))


def storyboard(ep):
    """Write EPISODE_DIR/storyboard.html: one card per scene (image, time, narration, tags). Needs no audio.
    Review it BEFORE narration/build; times are real if timings.json exists, else estimated at WPS words/s."""
    from html import escape
    ep = pathlib.Path(ep).resolve()
    paras, tags = parse_script(ep)
    imgs = {int(re.search(r"\d+", p.name).group()): p for p in find_images(ep)}
    real = json.load(open(ep / "timings.json", encoding="utf-8")) if (ep / "timings.json").exists() else None
    t, cards = 0.0, []
    for i, ws in enumerate(paras):
        if real:
            sw = [w for w in real if w[3] == i]
            a, b = sw[0][1], sw[-1][2]
        else:
            a, b = t, t + len(ws) / WPS
        t = b
        ev = [f"{{{x}}}" for _, x in tags[i]]
        warn = "" if ev or b - a <= MAX_STILL else f'<b class="w">{b - a:.1f}s with no pop/swap/punch</b>'
        pic = f'<img src="{imgs[i + 1].name}">' if i + 1 in imgs else '<div class="none">no image yet</div>'
        cards.append(f'<div class="c">{pic}<h3>{i + 1:02d} &middot; {a:.1f}-{b:.1f}s</h3><p>{escape(" ".join(ws))}</p>'
                     f'<code>{escape(" ".join(ev))}</code>{warn}</div>')
    css = ("body{font:15px system-ui;background:#16161a;color:#eee;margin:20px}.g{display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:14px}"
           ".c{background:#222228;border-radius:8px;padding:10px}.c img,.none{width:100%;aspect-ratio:16/9;object-fit:cover;border-radius:4px;background:#000;display:grid;place-items:center;color:#777}"
           "h3{margin:8px 0 4px;font-size:14px;color:#ffd24a}p{margin:0 0 6px}code{color:#8cf}.w{display:block;color:#f66;margin-top:4px}")
    (ep / "storyboard.html").write_text(f'<!doctype html><meta charset="utf-8"><title>Storyboard</title><style>{css}</style>'
                                        f'<h2>{ep.name}: {len(paras)} scenes, {"" if real else "~"}{t:.0f}s</h2><div class="g">{"".join(cards)}</div>', encoding="utf-8")
    print("wrote", ep / "storyboard.html", "(real times)" if real else "(estimated times)")


def main(ep, render=True):
    if not HF.exists():
        sys.exit("HyperFrames is not installed: run  python -I setup.py")
    ep = pathlib.Path(ep).resolve()
    audio = next((p for e in ("wav", "mp3", "m4a", "flac", "ogg") for p in ep.glob(f"narration.{e}")), None)
    if not audio:
        sys.exit("no narration.wav/mp3/m4a in " + str(ep))
    paras, tags = parse_script(ep)
    imgs = find_images(ep)
    if len(imgs) != len(paras):
        sys.exit(f"{len(paras)} scenes in script.txt but {len(imgs)} images (s01, s02, ...)")
    dur = float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", audio]).strip())

    tdir = ep / "timings"
    tdir.mkdir(exist_ok=True)
    run([sys.executable, "-I", WHISPER, audio, "--model", "small.en", "--out", tdir])
    asr = json.load(open(tdir / "words.json", encoding="utf-8"))
    words = [w for p in paras for w in p]
    st = align(words, asr)
    end = dur + 0.4
    W = []                                # (text, start, end, scene)
    k = 0
    for si, p in enumerate(paras):
        for w in p:
            W.append([w, st[k], None, si]); k += 1
    for i, w in enumerate(W):
        w[2] = W[i + 1][1] if i + 1 < len(W) else end
    json.dump(W, open(ep / "timings.json", "w"), indent=1)

    scene_start = [0.0] + [next(w[1] for w in W if w[3] == si) for si in range(1, len(paras))]
    scene_end = scene_start[1:] + [end]

    # caption groups: <= GROUP words, never across scenes, break after punctuation
    groups, cur = [], []
    for w in W:
        if cur and (len(cur) == GROUP or cur[0][3] != w[3]):
            groups.append(cur); cur = []
        cur.append(w)
        if re.search(r"[.!?,;:]$", w[0]):
            groups.append(cur); cur = []
    if cur:
        groups.append(cur)

    hf = ep / "hf"
    (hf / "assets").mkdir(parents=True, exist_ok=True)
    for f in ("hyperframes.json", "meta.json", "package.json"):
        shutil.copy(HERE / "template" / f, hf / f)
    shutil.copy(HERE / "node_modules" / "gsap" / "dist" / "gsap.min.js", hf / "assets" / "gsap.min.js")  # vendored: no CDN at render time
    shutil.copy(audio, hf / "assets" / ("narration" + audio.suffix))
    for p in imgs:
        shutil.copy(p, hf / "assets" / p.name)

    # ---- scripted events: pop / swap / punch, placed at the start of the word they precede
    POS = {"left": 160, "center": 680, "right": 1200}
    layers = ep / "layers"
    (hf / "assets" / "layers").mkdir(exist_ok=True)
    for name, flt in (("sfx_pop", "sine=frequency=620:duration=0.14,afade=t=out:st=0.03:d=0.11"),
                      ("sfx_whoosh", "anoisesrc=d=0.3:c=pink:a=0.5,lowpass=f=1800,afade=t=in:d=0.08,afade=t=out:st=0.1:d=0.2")):
        run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", flt, hf / "assets" / f"{name}.wav"])
    ev_html, ev_js, ev_times, n = [], [], [], 0
    off = 0
    for si, p in enumerate(paras):
        for li, tag in tags[si]:
            gi = off + li
            t = W[gi][1] if gi < len(W) and W[gi][3] == si else scene_end[si] - 0.6
            kind, _, rest = tag.partition(":")
            kind, tok = kind.strip(), rest.split()
            n += 1
            sfx = lambda nm, vol: ev_html.append(f'<audio id="sfx{n}" class="clip" src="assets/{nm}.wav" data-start="{t:.2f}" data-duration="0.35" data-track-index="4" data-volume="{vol}"></audio>')
            if kind in ("pop", "swap"):
                f = layers / tok[0]
                if not f.exists():
                    sys.exit(f"{{{tag}}}: {f} not found")
                shutil.copy(f, hf / "assets" / "layers" / f.name)
            if kind == "pop":
                x = POS[next((a[1:] for a in tok if a.startswith("@")), "center")]
                pop_dur = next((float(a[:-1]) for a in tok if re.fullmatch(r"[\d.]+s", a)), None)
                end_t = min(t + pop_dur, scene_end[si] + FADE / 2) if pop_dur else scene_end[si] + FADE / 2
                mult = "mix-blend-mode:multiply;" if "mult" in tok else ""
                ev_html.append(f'<img id="pop{n}" class="clip pop" src="assets/layers/{f.name}" data-start="{t:.2f}" data-duration="{end_t - t:.2f}" data-track-index="3" style="left:{x}px;z-index:{40 + n};{mult}" />')
                ev_js.append(f'tl.fromTo("#pop{n}",{{scale:0,opacity:0}},{{scale:1,opacity:1,duration:{POP},ease:"back.out(2.4)"}},{t:.2f});')
                sfx("sfx_pop", SFX_VOL)
            elif kind == "swap":
                ev_html.append(f'<img id="swap{n}" class="clip" src="assets/layers/{f.name}" data-start="{t:.2f}" data-duration="{scene_end[si] + FADE / 2 - t:.2f}" data-track-index="3" style="z-index:{30 + n}" />')
                ev_js.append(f'tl.fromTo("#swap{n}",{{opacity:0}},{{opacity:1,duration:0.15,ease:"none"}},{t:.2f});')
            elif kind == "punch":
                ev_js.append(f'tl.fromTo("#stage",{{scale:1}},{{scale:1.07,duration:0.12,ease:"power2.out"}},{t:.2f});')
                ev_js.append(f'tl.to("#stage",{{scale:1,duration:0.35,ease:"power2.inOut"}},{t + 0.12:.2f});')
                sfx("sfx_whoosh", SFX_VOL)
            else:
                sys.exit(f"unknown tag {{{tag}}} (use pop:, swap:, punch)")
            ev_times.append(t)
        off += len(p)
    marks = sorted(scene_start + ev_times + [end])
    gaps = [(a, b) for a, b in zip(marks, marks[1:]) if b - a > MAX_STILL]
    for a, b in gaps:
        print(f"RHYTHM: nothing changes visually from {a:.1f}s to {b:.1f}s ({b - a:.1f}s): add a pop/swap/punch")

    img_html, cap_html, js = [], [], []
    for i, p in enumerate(imgs):
        a = scene_start[i] - (FADE / 2 if i else 0)
        b = scene_end[i] + (FADE / 2 if i < len(imgs) - 1 else 0)
        d = b - a
        img_html.append(f'<img id="img{i}" class="clip" src="assets/{p.name}" data-start="{a:.2f}" data-duration="{d:.2f}" data-track-index="1" style="z-index:{i + 1}" />')
        m = MOTION[i % 4]
        s0, s1 = {"in": (1, 1.08), "out": (1.08, 1), "pan_l": (1.06, 1.06), "pan_r": (1.06, 1.06)}[m]
        x0, x1 = {"pan_l": (30, -30), "pan_r": (-30, 30)}.get(m, (0, 0))
        js.append(f'tl.fromTo("#img{i}",{{scale:{s0},x:{x0}}},{{scale:{s1},x:{x1},duration:{d:.2f},ease:"none"}},{a:.2f});')
        if i:  # crossfade over the previous scene (higher z-index); first scene is visible at 0 s
            js.append(f'tl.fromTo("#img{i}",{{opacity:0}},{{opacity:1,duration:{FADE},ease:"none"}},{a:.2f});')
    for gi, g in enumerate(groups):
        gs = max(g[0][1] - 0.05, 0.1)
        nxt = groups[gi + 1][0][1] - 0.04 if gi + 1 < len(groups) else end
        ge = max(g[-1][2], min(nxt, gs + HOLD))
        ge = min(ge, end)
        spans = "".join(f'<span id="g{gi}w{wi}" class="w">{w[0]}</span> ' for wi, w in enumerate(g))
        cap_html.append(f'<div id="g{gi}" class="clip grp" data-start="{gs:.2f}" data-duration="{ge - gs:.2f}" data-track-index="5">{spans}</div>')
        js.append(f'tl.fromTo("#g{gi}",{{opacity:0,y:20}},{{opacity:1,y:0,duration:.15,ease:"power2.out"}},{gs:.2f});')
        for wi, w in enumerate(g):
            js.append(f'tl.to("#g{gi}w{wi}",{{color:"#ffd24a",duration:.05}},{w[1]:.2f});')
        js.append(f'tl.to("#g{gi}",{{opacity:0,duration:.1,ease:"power2.in"}},{ge - 0.1:.2f});')

    html = f"""<!doctype html>
<html lang="en"><head><meta charset="UTF-8" /><meta name="viewport" content="width=1920, height=1080" />
<script src="assets/gsap.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1920px;height:1080px;overflow:hidden;background:#111}}
#root{{position:relative;width:100%;height:100%}}
#stage{{position:absolute;left:0;top:0;width:1920px;height:1080px;transform-origin:50% 50%}}
img.clip.pop{{position:absolute;top:230px;width:560px;height:560px;object-fit:contain}}
img.clip{{position:absolute;left:0;top:0;width:1920px;height:1080px;object-fit:cover}}
.grp{{position:absolute;left:0;width:1920px;bottom:110px;text-align:center;overflow:visible;font-family:Poppins,sans-serif;font-weight:700;font-size:78px;color:#fff;-webkit-text-stroke:3px #111;paint-order:stroke fill;z-index:50}}
</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{end:.2f}" data-width="1920" data-height="1080">
<div id="stage">
{chr(10).join(img_html)}
{chr(10).join(e for e in ev_html if e.startswith("<img"))}
</div>
{chr(10).join(e for e in ev_html if e.startswith("<audio"))}
<audio id="narr" class="clip" src="assets/narration{audio.suffix}" data-start="0" data-duration="{dur:.2f}" data-track-index="2" data-volume="1"></audio>
{chr(10).join(cap_html)}
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(js + ev_js)}
window.__timelines["main"] = tl;
tl.seek(0);
</script></body></html>"""
    (hf / "index.html").write_text(html, encoding="utf-8")

    env = dict(os.environ, npm_config_cache=str(CACHE / "npm"), PUPPETEER_CACHE_DIR=str(CACHE / "puppeteer"),
               XDG_CACHE_HOME=str(CACHE / "xdg"), npm_config_update_notifier="false")
    subprocess.run([HF, "check", "--json"], cwd=hf, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")  # nonzero on warnings; judged from the report below
    rep = max((hf / ".hyperframes/artifacts/checks").glob("*.json"), key=os.path.getmtime)
    d = json.load(open(rep, encoding="utf-8"))
    errs = [x for v in d.values() if isinstance(v, dict) for x in v.get("findings", []) if x["severity"] == "error"]
    for x in errs:
        print("ERROR", x["code"], x["message"][:200])
    if errs:
        sys.exit("check failed")
    print(f"check ok: {len(imgs)} scenes, {len(groups)} caption groups, {end:.1f}s")
    if render:
        run([HF, "render", "--output", str(ep / "final.mp4")], cwd=hf, env=env)
        print("rendered", ep / "final.mp4")
        # guard: narration must still be audible in the last 1.5 s of speech (word starts from whisper can run late)
        r = subprocess.run(["ffmpeg", "-hide_banner", "-ss", f"{max(W[-1][1] - 1.5, 0):.2f}", "-t", "1.5", "-i", str(ep / "final.mp4"),
                            "-vn", "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace")
        m = re.search(r"mean_volume: (-?[\d.]+|-inf) dB", r.stderr)
        if not m or m.group(1) == "-inf" or float(m.group(1)) < -45:
            sys.exit(f"AUDIO CHECK FAILED: narration silent near the end ({m.group(1) if m else 'n/a'} dB)")
        print("audio ok: narration audible at the end")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--new" in sys.argv:
        d = HERE / "episodes" / (args[0] if args else sys.exit("--new NAME"))
        (d / "layers").mkdir(parents=True, exist_ok=True)
        (d / "script.txt").write_text("Opening line of scene one, with a {pop:thing.png @right}pop on a key word.\n\nScene two starts after a blank line.\n", encoding="utf-8")
        sys.exit(f"created {d}\nadd narration.wav, s01.png, s02.png ... then: python -I build.py {d}")
    if not args:
        sys.exit(__doc__)
    if "--storyboard" in sys.argv:
        storyboard(args[0])
    else:
        main(args[0], render="--no-render" not in sys.argv)
