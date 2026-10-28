# User guide: three ways to make a video with Claude

Every mode starts the same way: a **script** and a **narration**. Pick the mode by the kind of video, then tell Claude what is in the box under "Say this to Claude".

| | A. Images + small animations | B. Voice to graphics (Data Story / Nafay-style) | C. Cinema-2D (code-drawn stick-figure film) |
|---|---|---|---|
| Look | Flow pictures per scene: stickman, cartoon, story, cooking illustrations | Clean motion graphics: headlines, counters, bar and line charts, takeaways | Characters in 2.5D sets, giant faces, blueprint diagrams, 3D shots, camera moves |
| Best for | Stories, simple explainers, cooking, kids | Stats, news, "why does X happen", money, tool explainers | What If, science, physics, history, documentary-light |
| Length that works | 1-10 min | 1-10 min | 30-90 s chapters, joined into 5-7 min |
| Plan cost (Claude Pro) | Low | Low | **High**: about 7% of a 5-hour window per 30 s (measured) |
| Needs Flow | Yes (images, free) | No | No |
| Engine | `build.py` | `build.py` + `scenes.json` | studio kit + `tools/to_studio.py` |
| Looks | any picture style | Data Story card (dark ink, 1 accent) | 5 dark kit styles + our 3 light ones |

Shared parts, any mode: narration with Gemini (`flow_narrate`), a soft music bed from Flow Music (`flow_music_create`), local word timing (whisper), and the rules in `skills/video-workflow/SKILL.md`.

---

## Before anything: the common inputs
1. **Script** in `episodes/<name>/script.txt`. A blank line starts a new scene (one idea each). About 150 words per minute.
2. **Narration** as `episodes/<name>/narration.wav|mp3|m4a`. Say: "Narrate it with Gemini, voice Charon, calm explainer." (Free tier: 10 requests a day, 400 characters each, so a long script needs several days or a bigger cap.)
3. **Optional music**: say "make a soft piano bed with Flow Music, instrumental, no drums". Claude trims it and saves `music.mp3` in the episode folder.
4. Create the folder: `python -I build.py --new my-episode` (or ask Claude).

---

## Mode A: images + small animations (build.py)
Pictures from Flow, one per scene, with pops, pose swaps, slow drift, 3-word captions and a pop sound.

**Say this to Claude**
> Make a stickman video in episode `my-episode`. Script is done and narration is in the folder. Use the stickman card. Create the character in a new Flow project, generate all scene images in one batch (look at each), then build.

**What Claude does:** reads `styles/stickman.md`, makes the character and one image per scene in Flow (0 credits, about 1 min per image when Flow falls back to one-by-one), adds `{pop:thing.svg @right}` or `{swap:pose.png}` tags to the script, runs `python -I build.py episodes/my-episode`, looks at frames, delivers `final.mp4`.

**Tags you can ask for:** `{pop:file @left|@center|@right [2s]}` an object pops in on a word; `{swap:file}` a new pose; `{zoom}` and `{punch}` exist but are off by default (quick zooms and whooshes hurt the flow). **Storyboard first:** "Show me the storyboard" runs `build.py --storyboard` (works before narration).
**Look change:** pick another picture style in the Flow prompts (pastel, whiteboard, photo, watercolour); the pipeline only sees images.

---

## Mode B: voice to graphics, no pictures (Data Story, Nafay-style)
Everything is drawn by code from `scenes.json`: headline, big counter, bar chart, line chart, takeaway. Elements appear on the spoken word.

**Say this to Claude**
> Make a Data Story video for episode `my-episode`. Narration is in the folder. Write `scenes.json` from the script: one scene per paragraph, real numbers only (label examples as examples), source line on every data scene. Build and show me the frames.

**What Claude does:** reads `styles/data-story.md` and `examples/data-story/`, writes `scenes.json` (types: claim, number, bar, line, takeaway; `on` = the spoken word that triggers each element), runs `build.py`, checks frames. Captions are off by default.
**Not built yet:** compare, flow and share scene types; sound effects; the other Nafay looks (Kinetic Caps, Clean Tech, Software Walkthrough, Warm Canvas, Pop Info) exist only as ideas in the skill. Ask for them one at a time and Claude will add a renderer, or "clone this look" from 1-3 screenshots.
**Look change:** Data Story colours live in `styles/data_story.py`; ask for "a light version" or "paper colours" and Claude edits the palette.

---

## Mode C: Cinema-2D (code-drawn film)
Characters, sets, faces, diagrams and 3D shots drawn frame by frame. Free to render (about 10 fps at 1080p on your PC), but Claude has to write every shot, so it uses a lot of your plan.

**One-time setup:** `python -I tools/setup_studio.py --go` installs the studio into `./studio` (about 1 GB, everything inside that folder). Check it with `python -I tools/studio.py where`. Run any studio command through `python -I tools/studio.py run node render.mjs ...` so the browser and libraries are found. The engine comes from the aiTrends plugin in `plugins/` (see THIRD_PARTY.md).

**Say this to Claude**
> Make a Cinema-2D video from episode `my-episode`, chapter 1 (first 60 seconds), style `daylight`. Run the hand-off, then do stages 4 to 8 of the studio's make-2d-video skill. Take all colours from the style, run the colour lint and a style grid before the full render.

**What Claude does**
1. `python -I tools/to_studio.py episodes/my-episode --style daylight` creates `projects/my-episode` in the studio: voiceover, word times from our local whisper, a draft shot list, your music bed, and a brief.
2. Writes the story notes and shots (about 15-25 shots per minute), sets and scenes, one batch of 8-12 at a time, looking at contact sheets.
3. Runs `lint_style_colors.py`, then `render.mjs --styles ...` to compare looks, shows you the grid.
4. Previews 30 s, you approve, final render, `audio/mix.py` mixes the kit's sound effects with your music, output in `projects/my-episode/out/`.
Docs Claude reads: `N:\AI\aitrends-2d-studio\docs\make-2d-video\` (a local copy, not in git).

**Long videos:** split the script into 60-90 s chapters (`my-episode-ch1`, `-ch2`...), build one per Claude Pro window, join in FilmCraft. Reusing the same sets and cast makes later chapters cheaper, because most of the cost is writing new scenes.

### Styles (not only black)
| id | Look | Tone |
|---|---|---|
| dusk, midnight, golden, neon, storybook | kit styles, mostly dark and cinematic (storybook is softer) | drama, mystery, thrillers |
| **daylight** | bright blue sky, white and cream, charcoal figures | clean explainers, science |
| **paper** | warm off-white, earthy, soft | history, documentary, editorial |
| **candy** | saturated cyan, pink, orange, purple figures | kids, fun what-ifs |

**Make your own:** copy `styles/cinema2d/packs/daylight.json` to `mystyle.json`, change the id, name, `ink` (figure colour), 5 moods (day, golden, dusk, night, storm: sky gradient, wall, floor, grass...), `ui` and `grade`, run the installer, and compare it on a style grid. Or tell Claude: "make a Cinema-2D style that looks like this screenshot" and give it 1-3 images.
**The rule that makes any style work:** every colour in a scene comes from `mood()`, `S()` or `S().ui`. Hard-coded white or black breaks light styles; the lint finds them. In the 30 s test clip it found 25 lines, mostly in the 3D shot and a title.

---

## Choosing a mode
- Story, cooking, kids, "needs real-looking objects" -> **A**.
- Numbers, comparisons, news, tool explainers -> **B**.
- A scenario with a character acting it out, or a diagram-heavy science explainer -> **C**, in chapters.
- Mixed: use B for the data chapter and C for the story chapters and join them.

## Which Claude model
- Titles, scripts, scenes.json, Mode A: Sonnet is enough.
- Mode C story breakdown and the first scene batches of a series: Opus is probably better (untested). Later chapters reusing sets: try Sonnet and compare on the same contact sheets. Medium or high effort, not max.

## Rules of thumb
- No quick zooms or stacked whooshes. Music at about 15 dB under the voice.
- Look at frames and a pause between words in the final audio before saying "done".
- Never state a number you did not source. Examples are labelled "example data".
- Test episodes stay local (gitignored). Text-only examples live in `examples/`.

---

## Changes after the first cut
Everything is in files (`script.txt`, `takes.json`, `scenes.json`, the studio project), so a change redoes only what it touches. Start a **fresh chat**, say "read `episodes/<name>/NOTES.md`", then ask.

| You say | What Claude does | Cost |
|---|---|---|
| "Slower narration, 10%" | `python -I tools/slow_narration.py episodes/<name> --factor 0.9`, then rebuild | no quota; instant |
| "A calmer, slower read of scene 5" | `flow_narrate_redo` on the take that holds scene 5 (see `takes.json`), same voice, then rejoin | 1 Gemini request |
| "Scene 8 wording changed" | edit `script.txt`, `flow_narrate_redo` that take with the new text | 1 request |
| "Different voice for everything" | `flow_narrate_script` again with the new voice | 3-4 requests |
| "Music softer / different" | `flow_music_edit` in the same session, or a new `flow_music_bed` | about 1.5 min per track, no limit found |
| Mode A: "new picture for scene 4" | regenerate that one image in Flow, rebuild | free |
| Mode B: "make scene 6 a line chart" | edit scene 6 in `scenes.json`, rebuild | small |
| Mode C: "closer face in shot 9" | edit that shot's file, preview `--from --to` at half scale, then re-render | tokens for one shot |

**After any audio change the clock moves.** Modes A and B re-time everything on the next `build.py` run by themselves (local whisper, aligned to your script). Mode C: run `python -I tools/to_studio.py episodes/<name>` again (it keeps your written shots, saves the old timing, re-times) and it moves every shot, music section and sound cue with `tools/retime_shots.py` (tested: a 10% slower read scaled all 12 shots by exactly 1.1 and kept them contiguous). Then re-render (free, about 15 minutes for 6 minutes of video).

## Limits, measured
| Thing | Limit |
|---|---|
| Gemini voice, one request | 8,192 input tokens and 16,384 output tokens, so a take could be about 8-10 minutes; we use 1,800-character takes (about 100 s) for steady quality; 1,608 characters in one take was complete (97% word match) |
| Gemini free tier | rate limited per key and per model (earlier measured on the 2.5 model: 3 requests a minute, about 10 a day). Several keys + 4 voice models rotate automatically; with keys from several Google accounts a long video per day is no problem |
| Flow Music track | 1:54 to 4:55 per track, whatever length is asked; no generation limit found (the number beside the diamond is progress points, not credits); about 1.5 minutes per track |
| Cinema-2D | about 7% of a Claude Pro 5-hour window per 30 s of video; work in 60-90 s chapters |
