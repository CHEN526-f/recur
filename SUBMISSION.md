# Assignment 3 — Submission

Submit the public source repository for the local Python artwork:
https://github.com/CHEN526-f/recur

The assignment brief is at
https://github.com/sd5913/teaching/blob/main/syllabus/03-interactive-experience.md.
The recorded deadline is 1 November 2026, 23:59 Hong Kong time. The author chose
a source-repository submission; website deployment is not part of this handoff.

## Before submission

1. Open a fresh terminal in the project and follow README's run commands.
2. Play several keys together, try LOOP and DEMO, and import a local recording.
3. Cancel the import chooser; confirm the previous track can resume.
4. Check that source, dependencies, required assets, README, PROCESS and credits
   are present, and that the image/video links open.
5. Read the trial account in PROCESS and confirm it matches the actual observation.
   Do not claim post-change participant approval without another real trial.
6. Confirm the repository is public, then submit its URL on Canvas and check the
   successful submission record.

Required materials include `app.py`, `recur/`, `pyproject.toml`, `uv.lock`, the
licensed demo recording, README, PROCESS, CREDITS and the actual development history.
The preview is renderer output, not a recording of the human trial.

## Updating the repository

The public repository and origin remote have already been created. After further
changes, check the diff and use the project's normal commit/push workflow:

```powershell
git status
git add README.md PROCESS.md CREDITS.md app.py recur tests docs
git commit -m "Describe the actual update"
git push origin main
```

A local edit or commit alone does not upload anything. Pushing updates the same
repository URL. Complete the final push before the course deadline; assessment
version selection remains subject to the course rules.

Do not upload `.venv/`, `.reference/`, `captures/`, private music, reference footage,
credentials or unlicensed recordings. The existing ignore file excludes local
working directories. The bundled CC0 recording and public development previews
are intentional submission assets. The Pages workflow is manual-only.
