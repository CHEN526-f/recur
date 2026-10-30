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

## Play independent visual voices

| Key | Visual voice | Sound |
|---|---|---|
| A | Local aperture opening | Kick |
| S | Travelling fold | Pitched glass melody |
| D | Petal opening | Chord |
| J | Fin/facet turning | Warm pluck |
| K | Layer depth opening | Bass |
| L | Travelling ripple | Percussion |

The screen contains one ordered main construction. Every hit captures a different
region, width and local variation. Openness, fold, petals, turning, depth and
ripple fields add together with bounded amplitudes. Layer and angular order are
preserved to keep the silhouette readable. Existing notes keep their own timing.

Combine keys. A new voice does not replace an existing animation. Every note has
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
- Base buttons or Shift + A/S/D/J/K/L: select the six original main constructions.
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
