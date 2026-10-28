# Third-party material

- **HyperFrames** (`hyperframes` npm package, pinned in package.json) - HeyGen, Apache-2.0 per its README.
  https://github.com/heygen-com/hyperframes
- `.claude/skills/{hyperframes,hyperframes-cli,hyperframes-registry,media-use}` - HeyGen's agent skills, copied
  unmodified from `npx hyperframes init` (hyperframes@0.8.206) so agents opening this repo have them.
  Refresh with `npx hyperframes skills update`.
- `docs/hyperframes/` - offline snapshot of `hyperframes docs <topic>` and `--help` output (v0.8.206).
- `tools/whisper_words.py` - word-level timestamps from a local whisper ggml model (adapted from the FilmCraft editor skill).
- **GSAP** 3.14.2 (`gsap` npm package, pinned) - copied into each episode's `hf/assets/` at build time, so rendering needs no internet. GSAP's "Standard License" applies: https://gsap.com/standard-license
- **aiTrends 2D Studio** plugin (`plugins/aitrends-2d-studio/`) - by aiTrends, created and distributed free of charge for use, with no licence
  file. Included unmodified at the maintainer's request so the Cinema-2D mode installs from this repo. All rights remain with its author:
  if you are the author and want it changed or removed, open an issue. It bundles three.js (MIT), Playwright (Apache-2.0) and
  @fontsource fonts (Fredoka, Nunito, Playfair Display: SIL OFL), which `npm install` fetches. Our additions around it:
  `tools/to_studio.py`, `tools/setup_studio.py`, `tools/studio.py`, `tools/install_cinema_styles.py`, `tools/lint_style_colors.py`, `styles/cinema2d/`.
