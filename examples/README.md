# Examples (text only, no media)

Copy a folder into `episodes/` and add what is missing, then build. Media is not committed (narration, images, renders).

- `data-story/`: `script.txt` + `scenes.json` for the Data Story style (`styles/data_story.py`). Needs only `narration.*` (any voice). Build: `python -I build.py episodes/data-story`.
- `stickman-sky/`: stickman explainer "why is the sky blue" (~54 s). `script.txt` (pop tags), `layers/` (4 SVG pops), `image-prompts.md` (the Flow prompts: character + 11 scenes). Needs `narration.*` and `s01..s11.jpg` from Flow.

Narration used for both: Gemini TTS voice Charon, style "calm/friendly explainer" (`flow_narrate`, <= 400 characters per call, chunks joined with a 0.3 s pad).
