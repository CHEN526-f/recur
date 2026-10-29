# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = ["pygame>=2.6.1,<3", "moderngl>=5.12,<6", "numpy>=2.1,<3"]
# ///
"""Run: uv run python app.py. Optional camera: uv sync --extra camera."""
import argparse
import json
import math
import os
from pathlib import Path
import time

os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
import pygame
from recur.model import Instrument, KEYS, FORM_COUNT
from recur.audio import Synth
from recur.renderer import SculptureRenderer
from recur.ui import Interface
from recur.camera import MotionCamera

HERE=Path(__file__).resolve().parent
CAPTURES=HERE/'captures'


def save_session(model,renderer):
    CAPTURES.mkdir(exist_ok=True)
    stamp=time.strftime('%Y%m%d-%H%M%S')
    png=CAPTURES/f'recur-{stamp}.png'
    pygame.image.save(renderer.capture(),str(png))
    data={'version':3,'bpm':model.bpm,'loop':model.loop,'loop_b':model.loop_b,'target':model.target,'target_b':model.target_b,'palette':renderer.palette,'crossfade':model.crossfade_target,'fx':model.fx_target}
    (CAPTURES/'latest-session.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    return png.name


def restore_session(model,renderer):
    data=json.loads((CAPTURES/'latest-session.json').read_text(encoding='utf-8'))
    loop=data.get('loop')
    if not isinstance(loop,list) or len(loop)!=6 or any(not isinstance(row,list) or len(row)!=16 or any(type(v) is not bool for v in row) for row in loop):
        raise ValueError('Expected six rows of sixteen boolean notes')
    bpm=data.get('bpm',108)
    if type(bpm) is not int or not 60<=bpm<=160:raise ValueError('Invalid tempo')
    target=data.get('target',0);palette=data.get('palette',0)
    if type(target) is not int or not 0<=target<FORM_COUNT or type(palette) is not int or not 0<=palette<3:
        raise ValueError('Invalid scene or material')
    loop_b=data.get('loop_b',[[False]*16 for _ in range(6)])
    if not isinstance(loop_b,list) or len(loop_b)!=6 or any(not isinstance(row,list) or len(row)!=16 or any(type(v) is not bool for v in row) for row in loop_b):raise ValueError('Invalid deck B loop')
    target_b=data.get('target_b',1);cross=data.get('crossfade',0.);fx=data.get('fx',[.5,.3])
    if type(target_b) is not int or not 0<=target_b<FORM_COUNT:raise ValueError('Invalid deck B shape')
    if type(cross) not in (int,float) or not math.isfinite(cross) or not 0<=cross<=1:raise ValueError('Invalid fader')
    if not isinstance(fx,list) or len(fx)!=2 or any(type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=1 for v in fx):raise ValueError('Invalid FX')
    model.loop=[row.copy() for row in loop];model.loop_b=[row.copy() for row in loop_b];model.bpm=bpm
    model.select_shape(target,0);model.select_shape(target_b,1);renderer.palette=palette
    model.crossfade_target=float(cross);model.fx_target=list(fx)


def main():
    global CAPTURES
    import sys
    from recur.player import run
    if '--interaction-test' in sys.argv:CAPTURES=CAPTURES/'qa'
    return run(save_session,restore_session)


if __name__=='__main__':
    raise SystemExit(main())
