---
name: video-workflow
description: House guideline for making and editing videos (explainers, stories, cooking, shorts, long-form) with our script-to-video pipeline. Use when planning, scripting, storyboarding, styling, building or reviewing any video that is built from narration + images/graphics, in any visual style.
---

# Video workflow guideline

One flow for every channel (explainer, story, cooking, shorts). Style is a swappable layer; the steps stay the same.
Pipeline tooling: `build.py` in this repo (HyperFrames, local whisper). Final cuts and captions: FilmCraft.

## 0. Principles (borrowed and proven)
1. **Storyboard before build.** Show 6-10 still frames (one per beat: time range, exact on-screen words, camera move, how it enters, key sounds) and wait for the user's OK. Cheap to change here, expensive after render.
2. **Style card, not ad-hoc look.** Each look is a saved card (see section 4). New episode = topic + style card.
3. **Every frame is a pure function of time.** No `Math.random` (use seeded rng). That makes renders repeatable and lets us scrub/seek frames to check them.
4. **Sync is everything.** Graphics and sounds read the same timeline (word timestamps). Never time by eye.
5. **Show options, not one answer.** For hooks/intros ask for 3 variations, pick one, re-render only that.
6. **Verify by looking.** Render stills at beat times, view them, measure audio RMS. Do not report done from the build log.
7. **Fix by description.** Changes go in as "scene 8: change X". Keep text/props editable per scene, not baked.

## 1. Pick the path
| Input you have | Path |
|---|---|
| Topic only | write script -> narration -> path B |
| Script | narration (AI Studio / Flow / ElevenLabs) -> path B |
| Narration audio | transcribe (word times) -> path B |
| Own camera footage | transcribe -> graphics layer over footage in FilmCraft (path C) |

- **B. Narration + generated images** (stickman, cartoon, story, cooking illustrations): Flow images -> `build.py` (pops, swaps, punches, captions).
- **B2. Narration + graphics in code** (explainers, data, UI, text-led): graphics are drawn by code (HTML/GSAP/canvas), no image generation. Same word-timing input.
- **C. Footage + overlays**: cut in FilmCraft, overlay code-drawn graphics rendered with alpha or as picture-in-picture, captions last.

## 2. Script and pacing (works for every style)
- Hook lands in under 2 s. Something new on screen every 0.5-1.5 s (short-form) or every 3-4.5 s (long-form; `build.py` warns above 4.5 s still).
- One idea per scene. A scene change = a new idea. Inside a scene, keep things continuous (lines stack, shift, get struck out).
- Emphasis ladder: pop/punch for the hardest word; highlight or circle for the thing that matters; strike/stamp for the wrong idea; counter + boom for the key number.
- Last beat holds about 1.5 s on the takeaway.
- Phone-safe: statement text >= 80 px at 1280x720, labels >= 28 px, key numbers >= 120 px.
- Illustrative figures are labelled as examples. No real logos, brands, people, receipts or messages in invented mockups.

## 3. Long-form (explainers 5-20 min)
- Split the script into chapters of 60-90 s; storyboard and build per chapter, join in FilmCraft. One broken chapter then costs one re-render.
- Open each chapter with a re-hook (question, number, contradiction). Add a pattern interrupt (new layout, cut type, sound) at least every 20-30 s.
- Keep one design system across chapters; vary layout type (big word / diagram / chart / mockup / character scene), not the look.
- Research and facts: a "facts I assumed" list goes under the storyboard; check numbers before build.
- Voice: one narrator voice fixed per channel (voice bible), generated per chapter.

## 4. Style cards (the reusable unit)
A style card is a short file (`styles/<name>.md`, first one: `styles/data-story.md`) holding: name, family, look (palette, fonts, surface), how it explains (appear / emphasis / numbers / proof / transitions), pace rules, sound map, and what is forbidden. Save one per channel look. Starting set (our own, inspired by what works):

| Card | Best for | Core recipe |
|---|---|---|
| Kinetic Caps | hooks, shorts, money/business | huge condensed caps word-by-word, one accent word, punch zoom + shake, strike + stamp, rolling counter + boom, whip/glitch/flash cuts |
| Chalk Talk | teaching, school-style | slate board, chalk strokes, colour chalk emphasis, dust, ghost of old lessons |
| Clean Tech | product/tool explainers | off-white, dot grid, words rise in, white UI cards, one blue accent, green check when done |
| Software Walkthrough | tutorials | app window, cursor + click ripples, camera zoom to target, spotlight, numbered callouts |
| Data Story | stats, news, "why" explainers | dark ink, one warm accent per idea, charts that draw to scale, source always on screen |
| Warm Canvas | talking-head edits | full-frame face, serif captions, then canvas with cards and face in a rounded PiP |
| Pop Info | infographic-style long-form | flat-vector scene, one character with a big feeling, thought bubble, counter, dotted path, iris wipe |
| Stickman (`styles/stickman.md`) | stories, simple explainers | Flow images per scene + `{pop}` `{swap}` tags; no quick zooms, no whooshes by default |

Cloning a look: take 1-3 screenshots of the reference, pick the nearest card, ask for a new card in that look, review ONE test frame, then approve. Copy the look (palette, motion language, layout), never the reference channel's exact art, text or characters.

## 5. Sound
- Always a bed (music/drone) under the body, ducked under booms and under narration.
- Sound map per event: slam (word), pop (card/chip), whoosh/glitch (cut), marker (highlight/draw), strike, stamp, tick (counter, only on value change, max 12/s), boom + shimmer (key number), click/ping/send (UI).
- At most ~3 sounds at once; leave near-silence before the biggest hit.
- Narration always wins: mix effects lighter when a voiceover is present.

## 6. Pipeline steps (every episode)
1. Brief: channel, style card, format (16:9 long / 9:16 short), length, voice.
2. Script (exact narration text, blank line = scene). Facts checked.
3. Narration audio. Transcribe to word times (local whisper only, `tools/whisper_words.py`).
4. Storyboard (`build.py EPISODE --storyboard` -> `storyboard.html`) -> user OK. For footage edits: a cut list instead.
5. Assets: images from Flow (all images before any video), or code graphics.
6. Build (`python -I build.py episodes/<name>`), then LOOK at frames at each beat and measure audio.
7. Iterate by scene description; 3 variations for the hook if unsure.
8. Final: FilmCraft for joins, cuts, loudness; captions last (type chosen first: English/Bangla/both, animated + highlight colour).
9. Vertical version: render again at 9:16 from the same timeline, not a crop.
10. Save any new look as a style card.

## 7. Review checklist (before "done")
- [ ] Hook in < 2 s; no stretch longer than the rhythm limit without a change
- [ ] Every number/fact on screen checked; examples labelled
- [ ] Text readable at phone size; nothing clipped at 9:16 safe areas
- [ ] Audio: narration audible at the end, effects not louder than voice, no silent gaps by accident
- [ ] Style consistent with the card; no stray elements from another style
- [ ] No third-party logos, characters or copied art

## 8. Gaps in our tooling (build order, not yet done)
Done: `styles/data-story.md` (rendered by `styles/data_story.py`; scenes via `scenes.json`, sample `examples/data-story`; types done: claim, number, bar, line, takeaway; still to add: compare, flow, share, sound) and `build.py EPISODE --storyboard`
(writes `storyboard.html`: image, time, narration and tags per scene; works before narration exists, estimated times; flags scenes with no visual change).
Still open:
1. Data Story: compare/flow/share scene types and its sound; then the Clean Tech card.
2. Code-graphic storyboard: `--storyboard` currently shows images only, not rendered stills of code scenes.
3. Small procedural SFX set (slam, whoosh, tick, boom) so code-graphics videos have sound without asset hunting.
4. Chart and diagram components (draw-on bars, lines, flow arrows) as `{chart:...}` tags.
5. 9:16 render flag.
6. Chapter split/join helper for long-form.

## 9. Lessons from the first test episodes (episodes themselves are not committed)
- **Quick zooms and whooshes hurt flow.** Tested on a stickman explainer: 11 punch zooms + whooshes felt busy; even 5 silent zooms were disliked. Default = slow drift only. Rhythm comes from pops, `{swap}` poses or new scenes. `{punch}` / `{zoom}` exist but are off by default.
- **Flow image batches:** `flow_agent_images` can fail ("Reuse prompt" timeout) and fall back to one-by-one (~1 min/image; 11 images ~15 min, 0 credits). Plan for it; do the rest of the prep while it runs.
- **Prop leaks:** an "idea" prop (lightbulb) in one scene prompt leaked into 3 other images. Put props only in the scene that needs them, say "no <prop>" elsewhere, and look at every image.
- **Reserve pop space:** every scene prompt names which part of the frame stays empty for the pop.
- **Gemini narration:** `flow_narrate` takes <= 400 characters per call and the free tier allows ~10 requests/day. Chunk by scenes, join with a 0.3 s pad (`ffmpeg concat`), one voice per channel. Windows SAPI voices are only for throwaway tests.
- **Fonts offline:** HyperFrames bundles Inter, Archivo Black, IBM Plex Mono, Poppins, Space Mono, JetBrains Mono, Oswald and others; any other family fails lint (`font_family_without_font_face`).
- **Captions:** the default yellow highlight is low contrast on pale backgrounds; darken or add a stroke before publishing. Code-graphic styles (Data Story) run with captions off.
- **Storyboard is a gate, not a file:** generate it, show it, wait for the OK.
- **Sample data on screen is labelled** "example data, not real figures".
- **Examples** (text only) live in `examples/`; the test episodes were deleted-by-design.

## 10. Music bed
Optional `music.mp3|wav|m4a` in the episode folder: `build.py` mixes it at `BGM_VOL` (0.18, about 15 dB under narration for a track as loud as the voice; check with a pause between words, it should read about -37 dB against -20 dB voice), 1.5 s fade-in, 2.5 s fade-out. It plays once (no loop), so trim it to the video length with ffmpeg first (`-t <video seconds>`).
Making the track with **Google Flow Music** (flowmusic.app, Lyria 3.5) through the Flow MCP:
1. User signs in to Flow Music by hand on the flowmusic.app tab in the Flow Chrome (never the app's built-in pane).
2. `flow_music_create` with a plain-words prompt: "instrumental, no vocals, no drums, calm solo piano with gentle pads, ~70 BPM, low dynamics, no builds, fades in and out, for under a narrator". It downloads the newest of the two variants straight into the Flow output folder (Downloadslow-mcp-out<project>, under the song title, like Flow images); copy it from there into the episode.
3. Not right? `flow_music_edit` with a follow-up ("softer", "no pads", "slow fade out"), same session. `flow_music_download` fetches any variant by id (mp3, m4a or wav).
4. The Producer ignores length (asked 60 s got 2:37): trim and fade with ffmpeg. Copy the file into the episode as `music.mp3` and rebuild.
Other sources if Flow Music is unavailable: a royalty-free track you pick; Google Lyria through the Gemini key (HyperFrames `media-use` recipe); local MusicGen (about 300 MB download, ask first).

## 11. Engines (modes) and the user guide
Three ways to turn narration into video; the full how-to with copy-paste prompts is `docs/USER-GUIDE.md`.
- **A. Images + small animations**: `build.py` with Flow stills (stickman card).
- **B. Voice to graphics**: `build.py` with `scenes.json` (Data Story card; other Nafay-style looks are specs, not built).
- **C. Cinema-2D**: local studio kit via `tools/to_studio.py` (cinema-2d card). Not only dark: light packs daylight/paper/candy, add more as JSON; scene code must take every colour from the style (`tools/lint_style_colors.py`). Measured cost: 30 s clip about 7% of a Pro 5-hour window, so work in 60-90 s chapters.
