# Style card: Data Story

Family: Data. Calm, editorial explainer for stats, "why does X happen", news and money topics. Our own design; the look is a
common editorial pattern (dark ink + one accent per idea), nothing here copies a specific channel.

## Look
- Surface: deep ink `#0f1419`, faint 1px grid at 4% opacity, soft vignette. No film grain. No glow except on the live number.
- One accent per idea, never two in the same scene: coral `#ff6b57`, teal `#2ec4b6`, sand `#e9c46a`. Text `#f4efe6`, muted `#8b95a1`.
- Type: Archivo Black (bundled with HyperFrames, so no download) for headlines, IBM Plex Mono for every number, label and the source line. Headline 84-120 px, labels >= 28 px, key number >= 160 px (1920x1080).
- Safe margins 120 px. Source line (mono, muted) bottom-left on every data scene, always visible.

## Scene types (pick one per scene; one idea per scene)
| Type | What is on screen | Motion |
|---|---|---|
| Claim | one headline, max 8 words, key word in accent | words rise 24 px and fade in, 60 ms apart |
| Big number | number + 1-line label + comparison chip ("3x last year") | counter rolls to value in 1.2 s, ease-out, then holds; chip pops in |
| Bar / column | 3-7 bars, values printed on bars, one accent bar, rest muted | bars grow from zero to scale, 80 ms stagger, labels fade in after |
| Line / trend | one line, end dot, labelled start and end values | line draws left to right in sync with the narration, end dot pulses once |
| Compare | two columns, "A vs B", one number each | columns slide in from opposite sides, winner gets the accent |
| Flow / cause | 3-5 boxes joined by arrows | boxes appear in the order spoken, arrows draw between them |
| Map / share | proportional squares or a single filled bar split into parts | parts fill in order of the script |
| Takeaway | one sentence, accent on the verb | holds 1.5 s, everything else fades to 20% |

## Rules
- Charts are drawn to scale from the real numbers, axes start at zero for bars. Never decorate a value you did not source.
- Every number on screen is in the script's facts list with its source. Illustrative numbers carry an "example" tag.
- A new number or shape appears on the word that names it (use the word times; one beat per script tag).
- Scene change every 6-12 s for long-form (a new idea); inside a scene something moves at least every 3 s.
- Cuts: fade-through-ink 0.3 s, or a slide of the whole board 0.4 s. No glitch, no flash, no shake.
- Captions off by default (the graphics carry the words). If captions are on: bottom third, Archivo 700, 3 words, accent on the spoken word.

## Sound
- Bed: soft pad or low piano loop, -26 dB under voice. No riser, no boom.
- Events: bar grow = soft tick per bar; counter = quiet tick only when the shown digit changes (max 12/s); number lock = one low "thock"; cut = short air whoosh at -18 dB.
- Narration always louder than effects.

## Build notes (HyperFrames)
- Implemented in `styles/data_story.py`. Episode = `script.txt` + narration + `scenes.json` (one spec per scene; `on` = spoken word that triggers it). Sample: `examples/data-story`. Types built: claim, number, bar, line, takeaway.
- One scene = one HTML section with its own GSAP timeline built from the word times (`timings.json`); same pattern as `build.py`'s captions and pops.
- Draw charts as inline SVG so strokes can animate (`stroke-dashoffset`) and text stays sharp; numbers via a GSAP tween on a counter object.
- Vertical (9:16): same scenes, stack columns vertically, 96 px side margins, headline max 6 words per line.
- Test before a full episode: render ONE frame per scene type from sample numbers and review them as the storyboard.

## Forbidden
Real logos, brand marks or screenshots; invented sources; dual accents in one scene; 3D charts; pie charts with more than 4 slices; stock-footage fills.
