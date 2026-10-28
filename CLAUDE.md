# Notes for AI agents working in this repo

- HyperFrames skills are in `.claude/skills/` (read `hyperframes` first before touching compositions); offline docs in `docs/hyperframes/`; CLI is `node_modules/.bin/hyperframes`. First time: `python -I setup.py`.
- One entry point: `python -I build.py EPISODE_DIR` (see README). Do not hand-edit `episodes/*/hf/`; it is regenerated.
- Edit the script tags and `layers/`, rebuild, then LOOK at frames (`ffmpeg ... select='eq(n,N)' ... tile`) before reporting done.
- Verify audio, not just that a stream exists: measure per-second RMS (`astats`); the build already fails on silent narration at the end.
- Do not reuse variable names across the pop, caption and audio sections of `build.py` (an earlier `dur` clash silenced the narration).
- HyperFrames rules that bite: no `visibility` tweens on `.clip`, use `fromTo` not `from`, keep `window.__timelines` registered, asset paths root-relative. `node_modules/.bin/hyperframes check --json` reports violations.
- Keep caches and installs on N: (C: and M: are tight). Ask before downloading models.
- English narration only; whisper models are local, never download or call paid APIs.
- Three modes (images / Data Story / Cinema-2D): read `docs/USER-GUIDE.md` first. Cinema-2D engine: `python -I tools/setup_studio.py --go` once, then `tools/to_studio.py`, `tools/studio.py run ...`, `tools/lint_style_colors.py`; its instructions are in `studio/docs/make-2d-video/`.
- Cinema-2D colours always come from the style (`mood()`, `S()`, `S().ui`); styles are JSON packs in `styles/cinema2d/packs/`.
- Token budget: Cinema-2D costs about 7% of a Claude Pro 5-hour window per 30 s of video. Work in 60-90 s chapters, one per fresh chat, and keep `episodes/<name>/NOTES.md` up to date so a new chat can resume.

