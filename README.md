# script-to-video

Turn **narration + script + images** into a finished 1080p30 video (explainers, stories, tutorials, shorts-style
long-form...), with word-timed captions, springy "pop" elements, scene swaps, camera punches and sound effects. Built on [HyperFrames](https://hyperframes.heygen.com)
(HTML + GSAP rendered to MP4). Style-agnostic: stickman, cartoon, whiteboard, illustration, photos or slides. The pipeline only sees images.

```
narration (AI Studio, etc.) -> script.txt -> images (Flow/Imagen) -> build.py -> final.mp4
```

Process and style guideline for any video (explainers, stories, long-form): [`skills/video-workflow/SKILL.md`](skills/video-workflow/SKILL.md).

## Setup (check first, install only what is missing)
Your machine may already have the tools. **Run the check first, before installing anything:**
```bash
python3 -I setup.py        # `python` on Windows
```
It looks for what you already have and reuses it:

| Needed | How it is checked | If present | If missing |
|---|---|---|---|
| Python 3.11+, Node 22+ | version check | left alone | prints an install command |
| ffmpeg + ffprobe | on PATH | reused as is | prints an install command |
| ffmpeg `whisper` filter | `ffmpeg -filters` | reused (this is the only whisper component; no separate whisper app or Python package) | tells you to get ffmpeg 8+ with it |
| whisper model `ggml-small.en.bin` | searched in `WHISPER_MODELS`, `~/whisper-models`, `~/.cache/whisper*`, `~/whisper.cpp/models`, the FilmCraft folder | reused from wherever it is | prints the one `curl` command |
| `hyperframes` + `gsap` (npm, pinned) | `node_modules` version check | skipped if already at the pinned versions | `npm ci` |
| HyperFrames headless Chrome | `hyperframes browser ensure` | reused if cached | downloaded once (~270 MB, outside this repo) |

`setup.py` never installs or downloads ffmpeg, Node or whisper models itself: it only tells you what to run for
the items marked MISSING, and re-running it after that is safe. English narration only. To keep a model in a
custom folder, set `WHISPER_MODELS=/that/folder`. No pip packages are needed.

## Everything HyperFrames, in the repo
- `package.json` / `package-lock.json`: pinned `hyperframes@0.8.206` and `gsap@3.14.2` (local, no CDN, no npx-on-demand)
- `.claude/skills/`: HeyGen's agent skills (`hyperframes`, `hyperframes-cli`, `hyperframes-registry`, `media-use`), so an agent opening this repo knows the framework
- `docs/hyperframes/`: offline snapshot of the CLI docs (data attributes, GSAP, compositions, rendering, troubleshooting, `--help`)
- Use the CLI directly: `node_modules/.bin/hyperframes <command>` (`preview`, `check`, `snapshot`, `catalog`, `doctor`, ...); open any episode's `hf/` project with `preview`

## Setting up on another machine (macOS / Linux / Windows)
```bash
git clone https://github.com/srijonsbzsifat/script-to-video.git && cd script-to-video
python3 -I setup.py                      # 1. check what you already have; it prints commands ONLY for what is missing
#   ...run just those commands (e.g. brew install ffmpeg, or the model curl), then re-run setup.py until it says "ready"
python3 -I build.py episodes/test-pops   # 2. sample render
```
Use `python3` instead of `python` on macOS/Linux. Do not run `brew install` or download a model up front: if ffmpeg
(with the `whisper` filter) and a `ggml-small.en.bin` model are already there, they are used as they are.

## Quick start
```bash
python -I build.py --new my-episode              # creates episodes/my-episode/{script.txt,layers/}
# add narration.wav (or mp3/m4a) and s01.png, s02.png ... (one image per scene)
python -I build.py episodes/my-episode           # -> episodes/my-episode/final.mp4
python -I build.py episodes/my-episode --no-render   # build + lint only
python -I build.py episodes/my-episode --storyboard  # storyboard.html: scenes, images, times, tags (no audio needed)
```
Try it first on the bundled sample: `python -I build.py episodes/test-pops`.

## Episode folder
| File | Purpose |
|---|---|
| `narration.wav` (or `.mp3`, `.m4a`) | the voiceover |
| `script.txt` | the exact narration text. A **blank line starts a new scene** (= one image) |
| `s01.png, s02.png, ...` | one background per scene, in script order (png/jpg/webp/svg, 16:9) |
| `layers/` | pop and swap assets |

Output: `final.mp4`, plus `hf/` (the generated HyperFrames project, open it with `npx hyperframes preview`)
and `timings.json` (aligned word times).

## Script tags (the editing layer)
Place a tag right before the word it should land on, with a space before the tag:

```
Sam checks his {pop:phone.png @right}phone.
```
| Tag | Effect |
|---|---|
| `{pop:file @left\|@center\|@right [2s] [mult]}` | object springs in (scale 0 -> ~1.1 -> 1 in 0.28 s) with a pop sound. `2s` = show for 2 s (default: until the scene ends). `mult` = multiply blend, so a white background on line art disappears |
| `{swap:file}` | crossfade the scene image to another image (pose change) |
| `{punch}` | quick 7% camera zoom with a whoosh |

The build prints `RHYTHM:` warnings when nothing visual changes for more than 4.5 s: add a tag there.

## How it works
1. Local whisper gives word times; they are aligned to `script.txt` (difflib), so ASR mistakes do not matter.
2. Scenes start at their first spoken word, crossfade 0.3 s, and get a slow zoom/pan (cycling 4 motions).
3. 3-word captions, spoken word turns yellow. Tags become timed layers and sound effects.
4. `hyperframes check` lints the project (errors abort), then it renders, and a guard fails the build if
   the narration is silent near the end.

Tune the constants at the top of `build.py`: `GROUP`, `HOLD`, `FADE`, `MOTION`, `POP`, `SFX_VOL`, `MAX_STILL`,
and the CSS for pops (`img.clip.pop`, 560 px box).

## Layout
```
build.py             the whole pipeline
setup.py             one-time dependency setup and checks
package.json         pinned hyperframes + gsap
.claude/skills/      HyperFrames agent skills
docs/hyperframes/    offline CLI docs
tools/whisper_words.py   word-level timestamps from a local ggml whisper model
template/            HyperFrames project files copied into every episode's hf/
episodes/            your episodes (git-ignored, except the sample)
.cache/              npm / puppeteer caches (git-ignored)
```

## Known limits
- English narration only (Bangla would need another timing method, e.g. silence detection per scene).
- Real transparency from image generators is unreliable: generate objects on plain white and use `mult`,
  or remove backgrounds first (`npx hyperframes remove-background`, downloads a 168 MB model).
- Sample images are placeholder SVGs; judge pop size/position on real assets.
