# Credits and tool disclosure

**Project:** RECUR / 环生 · **Author:** CHEN Hongfan · SD5913 Assignment 3.

## Included recording

**Technological Messup** by **Centurion_of_war**, CC0 1.0 Universal.

- Source: https://opengameart.org/content/technological-messup
- License: https://creativecommons.org/publicdomain/zero/1.0/
- Original OGG retained in `assets/music/`; full download record in
  `assets/music/CREDITS.md`. The optional browser experiment includes its own copy.
- `docs/demo.mp4` combines output of the project's renderer with this permitted
  demo recording. It is a development preview, not a user-trial recording.

Live voices and the LOCAL score are synthesized by this project's code. User
imports and the independently tested second track are not bundled.

## Reference works — influences, not included assets

- 冷锋过境, *永生 / OUROBOROS* (2022):
  https://www.bilibili.com/video/BV1f3411g7wK/ — repeated metallic modules,
  segmented transformations, closure and unfolding informed structural study.
- Jono Brandel and Lullatone, *Patatap*: https://patatap.com/ — direct
  keyboard-to-sound/visual feedback informed the interaction direction.

Reference frames, meshes, video and soundtrack are not distributed. The local
`.reference/` study folder and original supplied recording are excluded from Git.

## Dependencies

Python dependencies are declared in `pyproject.toml` and pinned by `uv.lock`:
Pygame (https://www.pygame.org/), ModernGL (https://moderngl.readthedocs.io/),
NumPy (https://numpy.org/) and optional OpenCV (https://opencv.org/).
Their respective licenses continue to apply. The browser experiment uses native
WebGL2, Web Audio and Workers without third-party runtime JavaScript packages.

## AI assistance

The continuous structural controller uses standard Lorenz-type differential
equations, modulated by audio. The numerical integration, music mapping and
construction code are project implementations; no simulation code was copied.
The branch hierarchy, damped joint integration, tangent-field spine and pose
texture are implemented in this repository. Reference imagery informed the
desired richness and material direction; its meshes and footage are not assets
in the artwork.

OpenAI Codex assisted with interpretation of the brief, code, geometry and
material implementation, sound synthesis, debugging, automated checks and
documentation. This is substantial assistance; the project is not described as
entirely hand-written. Human direction, the trial account and design corrections
were supplied by the author. See PROCESS for what was kept, changed and rejected.
No AI-generated participant, test result or retrospective commit history is claimed.
