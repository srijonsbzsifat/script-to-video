# Foley (real recordings, CC0)

122 short WAVs (44.1 kHz) converted from the stickman skill's `sfx/` (Kenney "RPG Audio" and "Impact Sounds", CC0, see `CREDITS.txt`). Real recordings for footsteps, doors and impacts; our synthesized `audio/sfx.py` library has no equivalents.

Groups (files are `<group>-000.wav` ... `-004.wav` unless noted): `footstep-carpet|concrete|grass|wood` x5, `impactbell-heavy`, `impactglass-light|medium|heavy`, `impactmetal-light|medium|heavy`, `impactplank-medium`, `impactplate-light|medium`, `impactpunch-medium|heavy`, `impactsoft-medium|heavy`, `impacttin-medium`, `impactwood-medium|heavy` (all x5, vary the number so repeats do not sound identical), plus `dooropen-1|2`, `doorclose-1|2`, `cloth1-4`, `creak1-3`, `bookplace1`, `chop`, `drawknife1`, `dropleather`, `metalclick`, `metallatch`.

## Use in a Cinema-2D project
`studio/audio/mix.py` takes a file path as the cue name, and an absolute path works:

```json
"sfx": [{"at": 0.4, "name": "<repo>/assets/foley/impactpunch-heavy-002.wav", "gain": -8}]
```

Tested: the studio's own decoder (`load_audio`) reads these files. Limits: file cues ignore `pitch` and `dur`, so a "dark" version means picking the heavy variants or pitching the WAV beforehand with ffmpeg (`-af asetrate=44100*0.7,aresample=44100`). Levels are relative to the voice like every other cue (normal -6 to -10).
Not wired into `to_studio.py` or any build step.
