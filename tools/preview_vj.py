"""Inspect every spatial generator through the real OpenGL surface passes."""
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
os.environ['SDL_AUDIODRIVER']='dummy'
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'.reference/packages'))
import pygame
import numpy as np
from PIL import Image,ImageDraw
from recur.renderer import SculptureRenderer
from recur.model import Instrument
from recur.vj import NAMES

pygame.display.init();pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION,3)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION,3)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK,pygame.GL_CONTEXT_PROFILE_CORE)
size=(1000,680);pygame.display.set_mode(size,pygame.OPENGL|pygame.DOUBLEBUF|pygame.HIDDEN)
renderer=SculptureRenderer(size);renderer.instrument_visible=False
renderer.evolution.strength=1.;renderer.climax.amount=.55
renderer.motion.values=(.5,.7,.5,.8);renderer.motion.levels=[.7,.6,.6]
model=Instrument();model.paused=True;model.energy=.6
output=Path('captures/vj');output.mkdir(parents=True,exist_ok=True)
sheet=Image.new('RGB',(1200,620),'#090b0c');draw=ImageDraw.Draw(sheet)
for i,name in enumerate(NAMES):
 renderer.evolution.vj.source=renderer.evolution.vj.target=i
 renderer.evolution.vj.variant=i;renderer.evolution.vj.blend=1.;renderer.evolution.vj.time=4.+i
 renderer.draw(model,bytes(size[0]*size[1]*4))
 pixels=np.frombuffer(renderer.ctx.screen.read(components=3,alignment=1),dtype='uint8').reshape(size[1],size[0],3)[::-1].copy()
 im=Image.fromarray(pixels);im.save(output/f'{name.lower()}.png');im.thumbnail((394,390))
 x=i%3*400;y=i//3*310;sheet.paste(im,(x,y+28));draw.text((x+12,y+8),name,fill='#d2ad68')
 pygame.display.flip()
sheet.save(output/'gallery.jpg')
# Inspect the actual manual A -> S transport, with automatic direction disabled.
renderer.evolution.strength=0.;renderer.climax.amount=.2
renderer.motion.reset();model=Instrument();model.select_shape(1)
sheet=Image.new('RGB',(1600,600),'#090b0c');draw=ImageDraw.Draw(sheet)
checkpoints=(0.,.15,.35,.55,.75,.95,1.2,1.5);proof=0
for frame in range(100):
 model.advance(1/60);renderer.draw(model,bytes(size[0]*size[1]*4))
 if proof<len(checkpoints) and frame/60>=checkpoints[proof]:
  pixels=np.frombuffer(renderer.ctx.screen.read(components=3,alignment=1),dtype='uint8').reshape(size[1],size[0],3)[::-1].copy()
  im=Image.fromarray(pixels);im.save(output/f'transition-{proof}.png');im.thumbnail((394,266))
  x=proof%4*400;y=proof//4*300;sheet.paste(im,(x,y+28));draw.text((x+12,y+8),f'A -> S / {frame/60:.2f}s',fill='#d2ad68');proof+=1
 pygame.display.flip()
sheet.save(output/'transition.jpg');pygame.quit();print('VJ GALLERY OK: six spatial generators and manual reassembly, real renderer')
