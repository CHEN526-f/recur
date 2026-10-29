"""A short, clearly labelled preview of the local fallback instrument, not Suno."""
import os
os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
from pathlib import Path
import sys
import wave
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pygame
from recur.audio import Synth

synth=Synth();rate=synth.RATE;beat=60/108
duration=beat*32+3.7
mix=np.zeros((int(duration*rate),2),dtype=np.float32)
def add(index,when,gain=1.,pitch=1.):
    raw=synth.raw[index].astype(np.float32)/32768
    if pitch!=1:
        positions=np.arange(0,len(raw)-1,pitch);lo=positions.astype(int);alpha=(positions-lo)[:,None]
        raw=raw[lo]*(1-alpha)+raw[lo+1]*alpha
    start=int(when*rate);end=min(len(mix),start+len(raw))
    mix[start:end]+=raw[:end-start]*gain
for bar in range(8):
    offset=bar*4*beat
    add(2,offset,.65)
    for step in range(4):
        add(0,offset+step*beat,.80)
        add(5,offset+(step+.5)*beat,.48)
    add(4,offset,.62)
    for step,pitch in ((.75,1.),(1.5,.75),(2.75,.89)):
        add(1,offset+step*beat,.32,pitch)
    if bar%2:add(3,offset+3*beat,.38)
mix*=np.minimum(1.,np.arange(len(mix))/rate/.15)[:,None]
mix*=np.minimum(1.,(len(mix)-1-np.arange(len(mix)))/rate/1.3)[:,None]
mix*=.62/max(.62,float(np.abs(mix).max()))
pcm=np.ascontiguousarray(mix*32767,dtype='<i2')
out=Path('captures/local-audio-preview.wav');out.parent.mkdir(exist_ok=True)
with wave.open(str(out),'wb') as wav:
    wav.setnchannels(2);wav.setsampwidth(2);wav.setframerate(rate);wav.writeframes(pcm.tobytes())
pygame.mixer.quit()
print(out.resolve())
