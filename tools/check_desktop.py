"""Repeatable local desktop checks; all test windows are hidden and muted."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--gallery',action='store_true')
parser.add_argument('--export',action='store_true');args=parser.parse_args()
os.chdir(ROOT)
commands=[['tools/preview_polyphony.py']]
if not args.gallery:
    commands.extend([['app.py','--polyphony-test','--mute'],
                     ['app.py','--interaction-test','--mute'],
                     ['app.py','--music',str(ROOT/'assets/music/technological-messup.ogg'),'--music-test','--mute'],
                     ['app.py','--rhythm-test','--mute'],
                     ['app.py','--smoke-test','--mute']])
if args.export:commands.append(['tools/preview_track.py','--output','captures/polyphonic-demo.mp4','--seconds','60'])
for command in commands:
    print('CHECK',' '.join(command),flush=True)
    subprocess.run([sys.executable,*command],check=True)
