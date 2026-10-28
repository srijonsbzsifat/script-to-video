# Style card: Cinema-2D (code-drawn stick-figure film)

Family: Illustrated + diagrams. Engine: the local studio kit (Node + Chromium + three.js), NOT in this repo (no licence file). We own the hand-off
(`tools/to_studio.py`), the extra styles (`styles/cinema2d/packs/*.json`, `tools/install_cinema_styles.py`) and the colour lint
(`tools/lint_style_colors.py`). Full instructions for Claude: `docs/USER-GUIDE.md`, Mode C.

## Look (fixed by the engine, re-coloured by the style)
Stick figures with round heads and one signature-colour item per recurring character, expressions on the beat of the words, giant face close-ups, freeze-frames, blueprint diagrams, one 3D shot per minute, a camera move in every shot, atmosphere (dust, rain, glows), 15-25 shots per minute.

## Style is a palette, not a mood
- Dark kit styles (dusk, midnight, golden, neon, storybook) for drama. Our light packs: **daylight** (clean blue/white), **paper** (warm editorial), **candy** (saturated, playful). Add more as JSON packs.
- A pack = figure ink, 5 core moods (day golden dusk night storm), ui tokens, grade. The installer derives interiorWarm, interiorCool and void.
- `ui.cream` is the high-emphasis text/glyph colour: LIGHT in dark styles, DARK in light styles. `ui.gold` is the accent label.

## Rules for scene code (so any style works)
1. Every colour from `mood()`, `S()` or `S().ui`. No hard-coded white, black or grey. Data hues (a red wave, a blue wave) may be literal.
2. Run `lint_style_colors.py` and a `--styles` grid with one dark and one light style before the full render.
3. Narration is never changed; a shot illustrates the words spoken while it is on screen.
4. No quick zoom/whoosh stacking; camera moves are slow pushes and drifts.

## Cost (measured, Sonnet 5.5, 30 s clip)
About 197k tokens and 7 points of a Claude Pro 5-hour window; render 10 fps at 1080p (free). Build 60-90 s chapters, reuse sets and cast, and join in FilmCraft.

## Sound
The kit synthesizes 36 sound effects and a basic music bed. Prefer our Flow Music bed (`music.mp3` in the episode folder, copied by the hand-off); keep the kit's SFX sparse.

## Forbidden
Real logos or people; invented sources; a new character look mid-video; hard-coded neutrals; committing the kit.
