# RECUR / 环生 — Start here

The submitted artwork is the local Python application. The public repository is
https://github.com/CHEN526-f/recur. A hosted website is not required for this submission.

## Run

Open the project folder in VS Code, open a new terminal, and run:

```powershell
uv sync --frozen
uv run python app.py
```

Click the artwork window before playing. The first setup downloads dependencies;
normal playback and analysis run locally without an API key.

## Play the ten original shapes

| Key | Visual voice | Sound |
|---|---|---|
| A | Serpent / closed ring | Kick |
| S | Ribbon | Pitched glass melody |
| D | Bloom | Chord |
| J | Crystal | Warm pluck |
| K | Orbit | Bass |
| L | Tide | Percussion |

Each normal key selects a different complete 3D construction, without Shift.
The most recently played key determines the next silhouette. Reassembly takes
about 0.72 seconds and starts from the current pose. Repeating a key does not
restart the transition. Earlier notes retain their accent tails.

Combine keys. A new shape does not cut off earlier accent tails. Every note has
its own smooth attack and release. Holding a key does not generate repeated hits.
Tap the canvas or pads to play; compatible touchscreens can send multiple finger
contacts. Ordinary laptop trackpads may expose only one mouse cursor to SDL.
Releasing one contact leaves the other contacts and animation tails intact.

T plays the bundled CC0 recording. U imports WAV, MP3, OGG or FLAC (up to ten
minutes). Measured attacks orchestrate the same visual voices. Y enables or
disables imported-music visuals; live playing can continue over the recording.
G starts/stops the original 32-bar synthesized score. No pitch or emotion
recognition is claimed. Beat timing depends on the recording and output devices.

## Controls

- H: artwork-only view. F: fullscreen. P: pause. M: mute.
- I / LOOP: open the 16-step editor. Adding a cell auditions and starts the loop.
- R: overdub live notes. The editor displays its playhead, state and deck gain.
- Tab: choose deck A/B. The crossfader controls their sound gains.
- Z/X: lower/raise melody octave. FX controls tone, echo, torsion and spread.
- E / SAVE: save an image and session in `captures/`. O / LOAD: restore it.
- A/S/D/J/K/L or shape buttons: select the six original main constructions.
- Shift + key: select a shape without triggering sound.
- F2 / SCULPT: the preserved earlier interaction study.
- 4/5/6/7: select iris/corona/rosette/facet as the main construction.
- Backspace: reset controls while preserving your loop. Escape: exit.

Application labels, guidance and notices are English. The project title retains
its Chinese name. The native file chooser follows the operating system language.

## Submission

Submit the public repository URL on Canvas. See `SUBMISSION.md` for the checklist,
`PROCESS.md` for the reported trial and development decisions, and `CREDITS.md`
for source attribution and AI assistance. Update and push the final version before
the course deadline. The optional `web/` folder is an earlier browser study.
