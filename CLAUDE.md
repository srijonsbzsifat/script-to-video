# Notes for AI agents working in this repo

- HyperFrames skills are in `.claude/skills/` (read `hyperframes` first before touching compositions); offline docs in `docs/hyperframes/`; CLI is `node_modules/.bin/hyperframes`. First time: `python -I setup.py`.
- One entry point: `python -I build.py EPISODE_DIR` (see README). Do not hand-edit `episodes/*/hf/`; it is regenerated.
- Edit the script tags and `layers/`, rebuild, then LOOK at frames (`ffmpeg ... select='eq(n,N)' ... tile`) before reporting done.
- Verify audio, not just that a stream exists: measure per-second RMS (`astats`); the build already fails on silent narration at the end.
- Do not reuse variable names across the pop, caption and audio sections of `build.py` (an earlier `dur` clash silenced the narration).
- HyperFrames rules that bite: no `visibility` tweens on `.clip`, use `fromTo` not `from`, keep `window.__timelines` registered, asset paths root-relative. `node_modules/.bin/hyperframes check --json` reports violations.
- Keep caches and installs on N: (C: and M: are tight). Ask before downloading models.
- English narration only; whisper models are local, never download or call paid APIs.
