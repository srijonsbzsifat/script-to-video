# script-to-video

Turn **an idea into a finished narrated video** with Claude, in three modes. You bring a topic; Claude helps with ideas, the script, narration, music, pictures or code-drawn animation, the build and the checks.

| Mode | What you get | Best for |
|---|---|---|
| **A. Images + small animations** | Flow pictures per scene, pops, pose swaps, slow drift, captions | stories, kids, cooking, simple explainers |
| **B. Voice to graphics** (Data Story) | headlines, counters, bar and line charts drawn by code | stats, news, money, "why does X happen" |
| **C. Cinema-2D** | code-drawn stick-figure film: sets, faces, diagrams, 3D shots, camera moves; dark **and** light styles | What If, science, history, documentary-light |

Rendering runs on your own computer. Mode A pictures, Gemini narration and Flow Music use free Google tools; modes B and C draw every frame with code.

---

## 1. What you need

**Claude (required).** [Claude Code](https://claude.com/claude-code) (desktop app or CLI) so Claude can read your files and run commands.
- **Claude Pro is enough to start**; the plan is the real limit, not your PC. Measured on Pro with Sonnet 5.5 (October 2026):
  - **Mode C (Cinema-2D): about 7% of a 5-hour window per 30 seconds of finished video** (about 197k tokens of scene writing). A 6-minute video is roughly 12 times that, so **build it in 60-90 s chapters, one chapter per fresh chat and per 5-hour window**, or choose a Max plan if you make Cinema-2D videos daily. Rendering itself costs no plan usage.
  - Modes A and B use far less (short scripts and a few tool calls). They have not been measured to the percent.
  - Titles, scripts and Mode A/B work are fine on **Sonnet**. For Mode C's story breakdown and the first scene batches of a new series, **Opus** is probably better (untested); later chapters reusing the same sets can go back to Sonnet. Medium or high effort, not max.
- If you hit a limit, nothing is lost: the work lives in files. Wait for the window to reset, open a fresh chat, say "read `episodes/<name>/NOTES.md` and continue".

**Your computer.** Windows, macOS or Linux (tested on Windows 11). Node.js 18+, Python 3.9+, ffmpeg (a recent build; the whisper filter needs ffmpeg 8+ for mode A/B timing), about 3 GB free disk. A GPU is optional but makes Cinema-2D rendering about 3-5 times faster (an RTX 5070 renders 1080p at about 10 fps; a 6-minute video renders in roughly 15-45 minutes).

**Free accounts and tools (only for what you use).**
- **Google Flow** account + the [flow-mcp](https://github.com/srijonsbzsifat/flow-mcp) tool: scene images (mode A, free), Gemini narration voices and **Flow Music** soft music beds (any mode). The Gemini narration key is free (Google AI Studio). Free keys are rate limited, so **add one key per Google account** in Flow Studio (Voice tab, "Add key"): when one is used up or rate limited the next is used automatically, then the next voice model. Keys are saved only on your computer and never go through chat. (ElevenLabs etc. also work: just drop the audio file in.)
- A local whisper model (`ggml-small.en.bin`, about 500 MB) for word timing. `setup.py` tells you the one command to get it. English narration only for now.

---

## 2. Install (let Claude do it)

Open Claude Code in an empty folder and say:

> Clone https://github.com/srijonsbzsifat/script-to-video.git, open it, read its CLAUDE.md and README, then run the setup: first `python -I setup.py` (tell me what is missing before installing anything), then `python -I tools/setup_studio.py` to show the Cinema-2D install plan. Ask me before every download and keep all installs inside the repo folder or on my big drive.

Claude will check Node, Python and ffmpeg, install the pinned packages and the headless browser for modes A and B, and (after you say yes) install the Cinema-2D studio.

**Manual install** (same thing):
```bash
git clone https://github.com/srijonsbzsifat/script-to-video.git && cd script-to-video
python -I setup.py                      # modes A and B: checks what you have, prints commands only for what is missing
python -I tools/setup_studio.py         # mode C: shows the plan (nothing downloaded)
python -I tools/setup_studio.py --go    # mode C: installs into ./studio (about 1 GB: npm packages, headless Chromium, numpy, scipy)
python -I tools/studio.py where         # confirms the studio folder
python -I build.py episodes/test-pops   # sample render of modes A/B
```
Mode C is bundled as a Claude **plugin** in `plugins/aitrends-2d-studio/` (made by aiTrends, free to use, see `THIRD_PARTY.md`). You do not need to install it as a plugin: `setup_studio.py` copies its engine into `studio/` and its instructions into `studio/docs/`, and Claude reads them from there. Everything else (Flow tools): follow the flow-mcp README, then run `flow_status` in Claude.

---

## 3. Make a video, step by step

Use a **fresh chat for each step marked 🆕** (see section 4). Save what each step produces in `episodes/<name>/`.

**Step 1 🆕 Idea.** Open `docs/prompts/01-idea-generator.md`, fill the brackets, paste into a new chat. Get 20 ranked ideas; say "more" or pick one. Ask Claude: "save my pick and why to `episodes/<name>/idea.md`".

**Step 2 🆕 Script.** New chat, paste `docs/prompts/02-script-writer.md` with your pick. Aim for about 150 words per minute (900-1,050 words = 6-7 minutes). Save as `episodes/<name>/script.txt`; **a blank line starts a new scene**, one idea each.

**Step 3 🆕 Fact check.** New chat: "Here is a script and its fact list. For each number and claim say whether it is well established, uncertain or wrong. Do not invent sources." Fix `script.txt`. Never publish a number you did not check.

**Step 4 Narration (hands-off).** In a chat in the repo: "Narrate `episodes/<name>/script.txt` with Gemini, voice Charon, calm explainer pace." Claude uses `flow_narrate_script`: one scene per paragraph, scenes grouped into takes of about 1,800 characters (1.5-2 minutes), every take in the **same voice and delivery**, keys and voice models rotating when one is limited. It saves every take, joins them into `narration.m4a`, loudness-matches them, and **re-records once any take that was read much faster or slower than the rest** (measured: one take came out at 2.52 words per second against 1.82; asking for "slower" brought it to 1.80). It writes `takes.json` (which scenes are in which take). A 6-minute script is 3-4 requests. Copy `narration.m4a` into the episode folder. (Or record yourself, or use ElevenLabs and drop the file in.)

**Step 5 Music (hands-off).** "Make a soft instrumental piano bed with Flow Music for a 6-minute video, save it as `music.mp3` in the episode." Claude uses `flow_music_bed`: it makes a track, asks the Producer in the **same session** for more versions of the same piece until there is enough, matches their loudness, crossfades them and fades in and out, giving one file of exactly the video's length (tested: 360 s from 3 tracks, about 4 minutes of waiting, steady level, no jumps at the joins). It is mixed about 15 dB under the voice.

**Step 6 Pick the mode and look.** Use the table at the top. Ask Claude to "show me the options" for Mode C styles (dark: dusk, midnight, golden, neon, storybook; light: **daylight, paper, candy**) or to design a new one from a screenshot. Details, with copy-paste prompts for each mode: **[docs/USER-GUIDE.md](docs/USER-GUIDE.md)**.

**Step 7 Storyboard (approve before building).** "Show me the storyboard." Mode A/B: `python -I build.py episodes/<name> --storyboard`. Mode C: Claude shows a story summary and a style grid. Change anything now; it is cheap here and expensive later.

**Step 8 Build.**
- A: Claude makes the images in Flow (one batch, looks at each), adds pop tags, runs `build.py`.
- B: Claude writes `scenes.json` from the script and runs `build.py`.
- C: `python -I tools/to_studio.py episodes/<name> --style daylight`, then Claude writes the shots, previews 30 s, you approve, final render, mix. **One chapter (60-90 s) per chat.**

**Step 9 Review before "done".** Ask Claude to: view frames at every scene change, check the audio level in a pause between words (the music should be quiet but present), check numbers on screen against the script, and run the colour lint (mode C). Watch it yourself once at full speed.

**Step 10 Polish and publish.** Join chapters, captions, intro/outro and loudness in any editor (FilmCraft, DaVinci, CapCut). Make the thumbnail from a clean frame. Add "example data" labels where numbers are illustrative.

**Step 11 Changes after you have watched it.** Open a fresh chat and say what you want; everything is kept in files so nothing is redone from scratch. See "Changes after the first cut" in [docs/USER-GUIDE.md](docs/USER-GUIDE.md). Examples:
- "Make the narration 10% slower." (instant, no quota: `tools/slow_narration.py`; or a re-recorded, calmer read with `flow_narrate_redo`)
- "Scene 7 sounds rushed and the text is wrong: here is the new line." (re-records only that take)
- "Replace the picture in scene 4 / make the chart in scene 6 a line chart / give shot 9 a closer face." (rebuilds only that scene's visual)
- "The music is too busy: make it softer." (`flow_music_edit` or a new bed)

---

## 4. Tips: fresh chats and saving your plan

- **Fresh chat per stage.** A long chat keeps re-reading everything above it; that is what burns your plan. Ideas, script, fact check, narration and each Cinema-2D chapter are separate chats.
- **Hand off with files, not memory.** End each stage with: "Write `episodes/<name>/NOTES.md`: decisions made, files created, what is next." Start the next chat with: "Read `episodes/<name>/NOTES.md` and continue with step N."
- **Point, do not paste.** Say "read `episodes/<name>/script.txt`" instead of pasting 1,000 words again.
- **One job per message** and say what "done" looks like ("a 30 s preview I can watch").
- **Look, do not guess.** Make Claude open contact sheets and frames before reporting. Fixing a bad scene early is cheap; re-rendering a finished video is not.
- **Draft at half scale.** Previews at `--scale 0.5` and 30 s ranges cost seconds.
- **Reuse.** In a series keep the same characters, sets, style and narrator; later chapters cost much less because the scenes already exist.
- **Do not stack effects.** No stacked whooshes or quick zooms; music quiet; one idea per scene.
- **Stop at limits.** If Claude says the 5-hour limit is near, ask it to write `NOTES.md` first, then continue after the reset.

---

## 5. Troubleshooting
- `studio not installed`: run `python -I tools/setup_studio.py --go`.
- Light style looks washed out or labels vanish: run `python -I tools/lint_style_colors.py studio/projects/<name>` and have Claude replace hard-coded white/black with style colours.
- Flow image batch is slow: when Flow's agent mode fails it makes images one by one (about 1 minute each). Keep working on narration meanwhile.
- Narration says "limit": the free Gemini tier is about 10 requests a day; split across days or use another voice.
- Windows: use `python`, not `python3`; quote paths with spaces; keep big installs off a nearly full C: drive (set `--dir`).

## 6. What is in the repo
```
README.md                     this page
docs/USER-GUIDE.md            the three modes with copy-paste prompts
docs/prompts/                 idea generator and script writer prompts
docs/build-reference.md       build.py details (episode folder, script tags)
skills/video-workflow/        the guideline Claude follows (rules, lessons, music, engines)
styles/                       style cards (stickman, data story, cinema-2d) + light/colour style packs
tools/                        setup, hand-off, studio runner, colour lint, whisper timing
plugins/aitrends-2d-studio/   the Cinema-2D plugin (by aiTrends, included unmodified, see THIRD_PARTY.md)
examples/                     text-only sample scripts and prompts
episodes/, studio/            your work and the installed studio (not committed)
```
