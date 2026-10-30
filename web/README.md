# RECUR / 环生 — browser edition

The recommended entry for reviewing this interactive artwork is `dist/index.html`
served over HTTP. WebGL2 renders the same original metallic rib constructions;
Web Audio decodes and plays files; an independent Worker locates transients.
There are no npm runtime dependencies, CDN imports, API keys or Python backend.

## Preview locally

From the repository root:

```powershell
uv run python -m http.server 8000 --directory web/dist
```

Open **http://localhost:8000** in Chrome, Edge or Firefox. `uv` is only hosting
the development files here; it is not required by visitors to a published site.
Do not double-click index.html: ES modules and Workers need an HTTP origin.

Click **DEMO** or **IMPORT**. Browser audio starts after a deliberate click.
Imported files are decoded and analysed locally, never uploaded. The existing
track continues when an invalid import fails. Cancelling the chooser leaves it
alone. A second load is rejected while analysis is in progress.

## Continuous evolution

Automatic mode does not follow the desktop app's fixed preset route. Low/mid/high
profiles, contrast and cumulative musical activity update a continuous parameter
space: aperture, curling, layer distance, sector hinges, elongation, roll and
depth. Open constructions bend around an axis; radial sectors share hinge points.
Parameter targets are smoothed over time, and the structural family is held for
a longer passage. Drum recoil is separate and follows measured audio attacks.
Different recordings seed different development. This remains a procedural
interpretation; it does not reproduce the reference video's animation or assets.

The original ten shapes remain selectable. Keyboard A/S/D/J/K/L and 4/5/6/7 take
over manually; Y returns to automatic evolution. Space holds/releases tension,
pointer drag orbits, wheel zooms, H hides UI and F enters fullscreen. Two decks,
crossfader, tone/echo pad, six synthesized roles, 16-step loop, overdub and local
session save/restore are included. Save also downloads a PNG. P pauses all timing,
V pauses the imported track and M mutes. Camera input remains in the Python edition.

## Publish with GitHub Pages

This is optional. The chosen assignment handoff is the Python artwork's public
source repository; pushing it does not deploy this website. To publish later:

1. Create a **public** repository under your own GitHub account and push this
   project's source, including `web/`, `.github/workflows/pages.yml`, README and
   PROCESS. Exclude `.venv/`, `.reference/` and `captures/` (already ignored).
2. In repository **Settings → Pages**, select **GitHub Actions** as the source.
3. Manually run **Optional manual website publication** from Actions.
4. Open the deployment's returned URL while signed out. Add that actual URL to
   README; do not substitute it for the public repository URL required by Canvas.

The workflow publishes **only `web/dist`**, which includes all required JS, CSS,
geometry and the licensed demo OGG. Relative URLs support project subpaths.
No public repository or deployed URL has been created by merely adding this file.

## Development checks

```powershell
cd web
npm run check
npm test
```

Node is needed only for these developer checks. To regenerate the shared mesh and
GLSL after editing Python geometry: `uv run python tools/export_web_geometry.py`
from the project root. `dist/geometry.js` is committed output; publishing does not
require Python or a build step.

## Limits and credits

Mobile performance depends on WebGL2 hardware; pixel ratio is capped. Glass is
screen-space refraction and metal uses procedural studio reflections. Beat/tempo
inference may be ambiguous; device/display latency is not measured by the
transient tests. Spectral change is not emotion or pitch recognition. Settings
are local to the browser; imported audio is not saved in the session. Browser
Web Audio synthesis differs from the desktop NumPy patches. The Python camera
path has not been ported. The author has supplied a real keyboard/slider trial
account in PROCESS; a post-change retest has not been confirmed.

See `dist/credits.html` and `dist/assets/music/CREDITS.md` for the CC0 recording,
visual references and AI-use disclosure.
