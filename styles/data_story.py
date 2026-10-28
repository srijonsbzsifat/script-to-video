"""Data Story renderer (see styles/data-story.md). One scene spec -> (html, gsap js lines, event times).

Scene specs live in EPISODE/scenes.json (see episodes/test-data). Types: claim, number, bar, line, takeaway.
"on": a word from the scene's narration; the element appears when that word is spoken (else at scene start).
"""
import re
from html import escape

INK, TEXT, MUTED = "#0f1419", "#f4efe6", "#8b95a1"
ACCENTS = {"coral": "#ff6b57", "teal": "#2ec4b6", "sand": "#e9c46a"}
BAR_MUTED = "#3a4552"
CSS = f"""
html,body{{background:{INK}}}
.sc{{position:absolute;left:0;top:0;width:1920px;height:1080px;background:{INK};overflow:hidden;color:{TEXT};font-family:"Archivo Black",Arial,sans-serif;
 background-image:linear-gradient(rgba(255,255,255,.04) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.04) 1px,transparent 1px);background-size:80px 80px}}
.sc::after{{content:"";position:absolute;inset:0;background:radial-gradient(ellipse at center,transparent 55%,rgba(0,0,0,.45) 100%)}}
.sc .a{{position:absolute}}
.mono{{font-family:"IBM Plex Mono",Consolas,monospace}}
.hl{{font-weight:400;line-height:1.06;letter-spacing:-.01em}}
.hl .w{{display:inline-block;margin-right:.26em}}
.src{{left:120px;bottom:70px;font-size:28px;color:{MUTED}}}
"""


def _norm(w):
    return re.sub(r"[^a-z0-9']", "", w.lower())


def _fmt(v, d):
    return f"{v:,.{d}f}"


def scene(sp, i, a, b, fade, words):
    """sp: spec dict; a,b: visual window; words: [(text, start)] spoken in this scene."""
    kind = sp["type"]
    acc = ACCENTS[sp.get("accent", list(ACCENTS)[i % 3])]
    p = f"s{i}"
    h, js, ev = [], [], []
    t0 = a + fade + 0.1
    seen = [0]

    def when(key):            # time of the spoken word named by sp[key] (searching forward), else scene start
        tok = key if isinstance(key, str) else None
        if not tok:
            return t0
        for k in range(seen[0], len(words)):
            if _norm(words[k][0]) == _norm(tok):
                seen[0] = k
                ev.append(words[k][1])
                return max(words[k][1], t0)
        raise SystemExit(f"scene {i + 1}: word '{tok}' not in its narration")

    def headline(text, size, top, accent_word=None, cls="hl", tid="hl"):
        ws = text.split()
        spans = "".join(f'<span class="w" style="color:{acc if accent_word and _norm(x) == _norm(accent_word) else TEXT}">{escape(x)}</span>' for x in ws)
        h.append(f'<div id="{p}{tid}" class="a {cls}" style="left:120px;top:{top}px;width:1680px;font-size:{size}px">{spans}</div>')
        js.append(f'tl.fromTo("#{p}{tid} .w",{{y:24,opacity:0}},{{y:0,opacity:1,duration:.4,stagger:.06,ease:"power2.out"}},{when(sp.get("on")):.2f});')

    if kind in ("claim", "takeaway"):
        if kind == "takeaway":
            h.append(f'<div class="a mono" style="left:120px;top:300px;font-size:30px;color:{MUTED};letter-spacing:.2em">TAKEAWAY</div>')
        headline(sp["text"], 124, 380 if kind == "takeaway" else 330, sp.get("accent_word"))
    elif kind == "number":
        t = when(sp.get("on"))
        d = sp.get("decimals", 0)
        pre, suf = sp.get("prefix", ""), sp.get("suffix", "")
        h.append(f'<div class="a mono" style="left:120px;top:200px;font-size:40px;color:{MUTED}" id="{p}lb">{escape(sp["label"])}</div>')
        h.append(f'<div id="{p}n" class="a mono" style="left:110px;top:270px;font-size:340px;font-weight:600;color:{acc};line-height:1;text-shadow:0 0 60px {acc}55">{escape(pre)}{_fmt(0, d)}{escape(suf)}</div>')
        js.append(f'tl.fromTo("#{p}lb",{{opacity:0}},{{opacity:1,duration:.4}},{t:.2f});')
        js.append(f'(function(){{var o={{v:0}},el=document.getElementById("{p}n");tl.to(o,{{v:{sp["value"]},duration:1.2,ease:"power2.out",onUpdate:function(){{el.textContent={pre!r}+o.v.toLocaleString("en-US",{{minimumFractionDigits:{d},maximumFractionDigits:{d}}})+{suf!r};}}}},{t:.2f});}})();')
        if sp.get("chip"):
            h.append(f'<div id="{p}chip" class="a mono" style="left:120px;top:680px;font-size:44px;padding:14px 30px;border:3px solid {acc};border-radius:60px;color:{acc}">{escape(sp["chip"])}</div>')
            js.append(f'tl.fromTo("#{p}chip",{{scale:0,opacity:0}},{{scale:1,opacity:1,duration:.3,ease:"back.out(2.4)",transformOrigin:"0% 50%"}},{t + 1.2:.2f});')
    elif kind == "bar":
        items = sp["items"]
        mx, W = max(v for _, v in items), 1150
        hi = sp.get("highlight", 0)
        unit = sp.get("unit", "")
        headline(sp["title"], 76, 100, sp.get("accent_word"), tid="ti")
        ons = sp.get("on") or []
        for k, (lab, v) in enumerate(items):
            y = 290 + k * 118
            w = round(W * v / mx)
            t = when(ons[k]) if k < len(ons) else t0 + 0.4 + 0.15 * k
            col = acc if k == hi else BAR_MUTED
            h.append(f'<div class="a mono" style="left:120px;top:{y + 18}px;width:300px;font-size:36px;color:{MUTED}">{escape(lab)}</div>')
            h.append(f'<div id="{p}b{k}" class="a" style="left:440px;top:{y}px;height:80px;width:{w}px;background:{col};border-radius:6px"></div>')
            h.append(f'<div id="{p}v{k}" class="a mono" style="left:{440 + w + 24}px;top:{y + 12}px;font-size:46px;font-weight:600;color:{acc if k == hi else TEXT}">{_fmt(v, sp.get("decimals", 0))}{escape(unit)}</div>')
            js.append(f'tl.fromTo("#{p}b{k}",{{width:0}},{{width:{w},duration:.9,ease:"power2.out"}},{t:.2f});')
            js.append(f'tl.fromTo("#{p}v{k}",{{opacity:0}},{{opacity:1,duration:.3}},{t + .8:.2f});')
    elif kind == "line":
        pts = sp["points"]
        X0, X1, Y0, Y1 = 90, 1590, 480, 40
        xs, ys = [x for x, _ in pts], [y for _, y in pts]
        lo, hi_ = min(ys), max(ys)
        pad = (hi_ - lo) * 0.1 or 1
        lo, hi_ = lo - pad, hi_ + pad
        px = [(X0 + (x - xs[0]) / (xs[-1] - xs[0]) * (X1 - X0), Y0 - (y - lo) / (hi_ - lo) * (Y0 - Y1)) for x, y in pts]
        L = sum(((px[k + 1][0] - px[k][0]) ** 2 + (px[k + 1][1] - px[k][1]) ** 2) ** .5 for k in range(len(px) - 1))
        unit, d = sp.get("unit", ""), sp.get("decimals", 0)
        headline(sp["title"], 76, 100, sp.get("accent_word"), tid="ti")
        t = when(sp.get("on"))
        draw = sp.get("draw", max(1.5, min(4.0, b - a - 2.5)))
        poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in px)
        lbl = lambda x, y, s, anchor: f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-family="IBM Plex Mono,Consolas,monospace" font-size="34" fill="{MUTED}">{escape(s)}</text>'
        svg = (f'<svg class="a" style="left:120px;top:260px" width="1680" height="620" viewBox="0 0 1680 620">'
               f'<line x1="{X0}" y1="{Y0}" x2="{X1}" y2="{Y0}" stroke="{BAR_MUTED}" stroke-width="3"/>'
               f'<polyline id="{p}ln" points="{poly}" fill="none" stroke="{acc}" stroke-width="9" stroke-linejoin="round" stroke-linecap="round" stroke-dasharray="{L:.0f}" stroke-dashoffset="{L:.0f}"/>'
               f'<circle id="{p}dot" cx="{px[-1][0]:.1f}" cy="{px[-1][1]:.1f}" r="16" fill="{acc}"/>'
               + lbl(px[0][0], Y0 + 50, str(xs[0]), "middle") + lbl(px[-1][0], Y0 + 50, str(xs[-1]), "middle")
               + f'<text id="{p}vs" x="{px[0][0]:.1f}" y="{px[0][1] - 30:.1f}" text-anchor="start" font-family="IBM Plex Mono,Consolas,monospace" font-size="44" font-weight="600" fill="{TEXT}">{_fmt(ys[0], d)}{escape(unit)}</text>'
               f'<text id="{p}ve" x="{px[-1][0]:.1f}" y="{px[-1][1] - 34:.1f}" text-anchor="end" font-family="IBM Plex Mono,Consolas,monospace" font-size="56" font-weight="600" fill="{acc}">{_fmt(ys[-1], d)}{escape(unit)}</text></svg>')
        h.append(svg)
        js.append(f'tl.fromTo("#{p}ln",{{strokeDashoffset:{L:.0f}}},{{strokeDashoffset:0,duration:{draw:.2f},ease:"none"}},{t:.2f});')
        js.append(f'tl.fromTo("#{p}vs",{{opacity:0}},{{opacity:1,duration:.3}},{t:.2f});')
        js.append(f'tl.fromTo("#{p}dot",{{scale:0,opacity:0,transformOrigin:"50% 50%"}},{{scale:1,opacity:1,duration:.3,ease:"back.out(3)"}},{t + draw:.2f});')
        js.append(f'tl.fromTo("#{p}ve",{{opacity:0}},{{opacity:1,duration:.3}},{t + draw:.2f});')
    else:
        raise SystemExit(f"scene {i + 1}: unknown type '{kind}' (claim, number, bar, line, takeaway)")

    if sp.get("source"):
        h.append(f'<div id="{p}src" class="a mono src">Source: {escape(sp["source"])}</div>')
        js.append(f'tl.fromTo("#{p}src",{{opacity:0}},{{opacity:1,duration:.4}},{t0:.2f});')
    html = f'<div id="sc{i}" class="clip sc" data-start="{a:.2f}" data-duration="{b - a:.2f}" data-track-index="1" style="z-index:{i + 1}">{"".join(h)}</div>'
    return html, js, ev + [t0]
