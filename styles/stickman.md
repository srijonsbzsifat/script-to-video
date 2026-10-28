# Style card: Stickman

Family: Illustrated. Friendly stickman explainer for science, how-it-works and story topics. Images from Flow, assembled by `build.py`
(images + word-timed pops + captions). First episode: `examples/stickman-sky` ("why is the sky blue").

## Look
- One character per episode, made once in Flow (`flow_character`, with a voice) and attached to every image batch: round white head, thick black outline, dot eyes, small round glasses, thick black stick limbs. Same size and line weight in every scene.
- Flat 2D, thick black outlines, soft pastel backgrounds, lots of empty space. No text, letters, numbers or logos inside images.
- Palette: pastel sky/grey-blue backgrounds, one strong colour per idea (red = long/hot/wrong, blue = short/cool, orange = sunset/energy). Pops use the same flat style, thick dark outline.
- 16:9, 1376x768 stills are fine (cover-fit to 1080p).

## Image rules (Flow)
- One batch, all scenes, before any video: `flow_agent_images` with the character attached. If agent mode fails Flow redoes scenes one by one (about 1 min each; 11 images took ~15 min).
- Every scene prompt names where the character stands and which part of the frame stays EMPTY for a pop (left / centre / right).
- Do not leave "idea" props in the style note (a lightbulb in one scene leaked into three others). Put props only in the scene that needs them, and say "no lightbulb" elsewhere.
- Look at every image before building. Regenerate the bad ones; do not patch with prompt notes.

## Motion and effects (what works, what does not)
- Default motion is the slow cross-fade plus gentle zoom/pan that `build.py` already applies per scene. That is enough.
- NO quick zoom-ins / zoom-outs (`{zoom}`, `{punch}`) in this style: tested on stickman-sky, the user found them jarring and they break the flow. Keep both tags for other styles only.
- NO whooshes by default. Sound is narration + a soft pop on each `{pop}` and nothing else, unless a moment truly needs more.
- Hold rhythm with content instead of camera moves: a `{pop}` object on the key word, or `{swap:pose.png}` for a new pose or expression in the same scene.
- A scene can run 4.5-8 s with only the slow drift; a still longer than ~8 s needs a pop or swap.

## Pops
- Transparent SVG/PNG, one object, readable at 560 px, placed `@left|@center|@right` on an area the image keeps empty.
- Pop on the word that names the object, never earlier. Max one pop per sentence; at least one per 2 scenes.

## Narration and captions
- Gemini TTS (Charon works for explainers; calm, steady style note), chunks of up to 400 characters joined with a short pad. Free tier: 10 requests/day, so batch.
- ~140-150 words per minute of video. One idea per scene; a blank line in `script.txt` starts a new scene (= one image).
- Captions: 3 words, spoken word highlighted. Known problem: the yellow highlight is low contrast on pale backgrounds; use a dark stroke or darker highlight before publishing.

## Sound (to build)
- Soft music bed: drop `music.mp3` in the episode folder (see the skill, section 10); `build.py` mixes it at -18 dB. No risers, booms or stingers in this style.

## Forbidden
Real logos, brands or people; text baked into images; a second main character that changes between scenes; quick zooms and stacked whooshes.
