"""Render isolated voices and overlapping notes using the real OpenGL path."""
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
os.environ['SDL_AUDIODRIVER']='dummy'
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'.reference/packages'))
import pygame
import numpy as np
from PIL import Image,ImageDraw
from recur.renderer import SculptureRenderer
from recur.model import Instrument
from recur.polyphony import NAMES

size=(1000,680);pygame.display.init()
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION,3)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION,3)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK,pygame.GL_CONTEXT_PROFILE_CORE)
pygame.display.set_mode(size,pygame.OPENGL|pygame.DOUBLEBUF|pygame.HIDDEN)
renderer=SculptureRenderer(size);renderer.instrument_visible=False
model=Instrument();model.paused=True
out=ROOT/'captures/polyphony';out.mkdir(parents=True,exist_ok=True)
sheet=Image.new('RGB',(1200,620),'#090b0c');draw=ImageDraw.Draw(sheet)
for voice,name in enumerate(NAMES):
 renderer.stage.reset();renderer.stage.note(voice,.9);renderer.stage.time+=.45
 renderer.draw(model,bytes(size[0]*size[1]*4))
 pixels=np.frombuffer(renderer.ctx.screen.read(components=3,alignment=1),dtype=np.uint8).reshape(size[1],size[0],3)[::-1].copy()
 im=Image.fromarray(pixels);im.save(out/f'{voice}-{name.lower()}.png');im.thumbnail((394,268))
 x=voice%3*400;y=voice//3*310;sheet.paste(im,(x,y+28));draw.text((x+12,y+8),'ASDJKL'[voice]+' / '+name,fill='#d2ad68')
 pygame.display.flip()
sheet.save(out/'voices.jpg')
renderer.stage.reset();renderer.stage_renderer.idle=0.
for voice in range(6):renderer.stage.note(voice,.8)
renderer.stage.time+=.4;renderer.draw(model,bytes(size[0]*size[1]*4))
pygame.image.save(renderer.capture(),str(out/'ensemble.png'))
renderer.stage.reset();renderer.stage_renderer.idle=0.
for _ in range(4):renderer.stage.note(0,.85)
renderer.stage.time+=.5;renderer.draw(model,bytes(size[0]*size[1]*4))
pygame.image.save(renderer.capture(),str(out/'repeat-rings.png'))
pygame.quit();print('SPATIAL PREVIEW OK: one original 3D base; six isolated local motions, overlap and repeated-key variation')
