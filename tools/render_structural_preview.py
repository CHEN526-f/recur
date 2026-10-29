"""Render original motion and local fallback sound. Reference video is not used."""
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
from pathlib import Path
from fractions import Fraction
import sys
import wave
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'.reference/packages'))
import av
import numpy as np
import pygame
from recur.model import Instrument
from recur.renderer import SculptureRenderer
from recur.music import analyse

size=(1280,720);fps=24
with wave.open(str(ROOT/'captures/local-audio-preview.wav'),'rb') as source:
    rate=source.getframerate();samples=np.frombuffer(source.readframes(source.getnframes()),dtype='<i2').reshape(-1,2)
envelopes=analyse(samples,rate)
seconds=len(samples)/rate
pygame.display.init()
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION,3)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION,3)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK,pygame.GL_CONTEXT_PROFILE_CORE)
pygame.display.set_mode(size,pygame.OPENGL|pygame.DOUBLEBUF)
renderer=SculptureRenderer(size);renderer.instrument_visible=False
renderer.orbit[:]=[0.,.12];renderer.orbit_target[:]=[0.,.12]
renderer.zoom=renderer.zoom_target=5.9
model=Instrument();overlay=bytes(size[0]*size[1]*4)
out=ROOT/'captures/structure-preview.mp4'
container=av.open(str(out),'w',options={'movflags':'+faststart'})
video=container.add_stream('libx264',rate=fps)
video.width,video.height=size;video.pix_fmt='yuv420p';video.options={'crf':'20','preset':'fast'}
audio=container.add_stream('aac',rate=rate);audio.layout='stereo';audio.bit_rate=160000
previous=-1;proof=set()
try:
    for index in range(int(seconds*fps)):
        pygame.event.pump();time=index/fps
        section=min(5,int(time/3.4))
        if section!=previous:model.select_shape((0,1,2,4,3,5)[section]);previous=section
        bands=envelopes[min(len(envelopes)-1,int(time*30))].tolist()
        for band in range(3):model.band_targets[band]=max(model.band_targets[band],bands[band])
        renderer.climax.music_level=sum(a*b for a,b in zip(bands,(.2,.35,.45)))
        model.advance(1/fps);renderer.draw(model,overlay)
        raw=renderer.ctx.screen.read(components=3,alignment=1)
        pixels=np.frombuffer(raw,dtype=np.uint8).reshape(size[1],size[0],3)[::-1].copy()
        frame=av.VideoFrame.from_ndarray(pixels,format='rgb24');frame.pts=index
        for packet in video.encode(frame):container.mux(packet)
        if section not in proof and time%3.4>2.8:
            pygame.image.save(pygame.image.frombytes(pixels.tobytes(),size,'RGB'),str(ROOT/f'captures/structure-{section+1}.png'))
            proof.add(section)
        pygame.display.flip()
    for packet in video.encode():container.mux(packet)
    for first in range(0,len(samples),1024):
        pcm=samples[first:first+1024].astype(np.float32).T.copy()/32768.
        frame=av.AudioFrame.from_ndarray(pcm,format='fltp',layout='stereo')
        frame.sample_rate=rate;frame.time_base=Fraction(1,rate);frame.pts=first
        for packet in audio.encode(frame):container.mux(packet)
    for packet in audio.encode():container.mux(packet)
finally:container.close();pygame.quit()
print(f'PREVIEW OK: {seconds:.2f}s; {out}; {len(proof)} structural frames')
