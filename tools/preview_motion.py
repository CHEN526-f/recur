"""Render the real SONG motion and matching local audio for visual verification.

Optional export dependencies: PyAV and Pillow (also available in .reference/packages).
No reference frames, meshes or audio are used in this output.
"""
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
from PIL import Image,ImageDraw
from recur.model import Instrument
from recur.composition import Performance
from recur.renderer import SculptureRenderer


def main():
    fps=24;size=(1100,704);bpm=108;start_bar=10;bars=10
    start=start_bar*4*60/bpm;seconds=bars*4*60/bpm
    output=ROOT/'captures/motion';output.mkdir(parents=True,exist_ok=True)
    with wave.open(str(ROOT/'captures/recur-song.wav'),'rb') as source:
        rate=source.getframerate()
        source.setpos(round(start*rate))
        samples=np.frombuffer(source.readframes(round(seconds*rate)),dtype='<i2').reshape(-1,2)
    pygame.display.init()
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION,3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION,3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK,pygame.GL_CONTEXT_PROFILE_CORE)
    pygame.display.set_mode(size,pygame.OPENGL|pygame.DOUBLEBUF|pygame.HIDDEN)
    renderer=SculptureRenderer(size);renderer.instrument_visible=False
    model=Instrument(crossfade=.45,crossfade_target=.45)
    performance=Performance();performance.start();renderer.performance=performance
    overlay=bytes(size[0]*size[1]*4)
    container=av.open(str(output/'song-motion.mp4'),'w',options={'movflags':'+faststart'})
    video=container.add_stream('libx264',rate=fps)
    video.width,video.height=size;video.pix_fmt='yuv420p';video.options={'crf':'19','preset':'fast'}
    audio=container.add_stream('aac',rate=rate);audio.layout='stereo';audio.bit_rate=160000
    sheet=Image.new('RGB',(1440,8*240//4),'#0b0d0e');draw=ImageDraw.Draw(sheet)
    proof_times=(.12,.44,4.7,7.,9.1,12.,14.,19.)
    proof=0;previous=None;differences=[];forms=set();index=0
    try:
        for tick in range(round((start+seconds)*fps)):
            pygame.event.pump();model.advance(1/fps)
            for event in performance.advance(1/fps,bpm):
                model.trigger(event.voice,'DEMO',event.deck)
                gain=np.cos(.45*np.pi/2) if event.deck==0 else np.sin(.45*np.pi/2)
                renderer.motion.note(event.voice,event.velocity,gain)
                renderer.climax.note(event.voice,gain*event.velocity)
            if tick<round(start*fps):
                renderer.motion.transport_beat=performance.position/4
                renderer.motion.update(model,1/fps)
                renderer.stage.update(model,renderer.motion,1/fps)
                renderer.evolution.update(model,renderer.motion,1/fps,selected=True)
                renderer.climax.score_target=performance.expansion
                renderer.climax.update(model,1/fps)
                renderer._last_clock=model.clock;renderer._visual_phase=model.clock
                continue
            renderer.draw(model,overlay)
            raw=renderer.ctx.screen.read(components=3,alignment=1)
            pixels=np.frombuffer(raw,dtype=np.uint8).reshape(size[1],size[0],3)[::-1].copy()
            frame=av.VideoFrame.from_ndarray(pixels,format='rgb24');frame.pts=index
            for packet in video.encode(frame):container.mux(packet)
            if previous is not None:differences.append(float(np.abs(pixels.astype(float)-previous).mean()))
            previous=pixels.astype(float);forms.add(model.target)
            if proof<len(proof_times) and index/fps>=proof_times[proof]:
                im=Image.fromarray(pixels);im.save(output/f'frame-{proof+1}.png')
                im.thumbnail((356,212));x=(proof%4)*360;y=(proof//4)*240
                sheet.paste(im,(x,y+25))
                draw.text((x+8,y+6),f'{index/fps:.2f}s / {performance.label} / form {model.target}',fill='#e4d8ae')
                proof+=1
            pygame.display.flip();index+=1
        for packet in video.encode():container.mux(packet)
        for first in range(0,len(samples),1024):
            pcm=samples[first:first+1024].astype(np.float32).T.copy()/32768
            frame=av.AudioFrame.from_ndarray(pcm,format='fltp',layout='stereo')
            frame.sample_rate=rate;frame.time_base=Fraction(1,rate);frame.pts=first
            for packet in audio.encode(frame):container.mux(packet)
        for packet in audio.encode():container.mux(packet)
    finally:container.close();pygame.quit()
    sheet.save(output/'contact.jpg')
    assert len(forms)==1 and min(differences)>0.,'The visual timeline did not move'
    print(f'MOTION OK: {index} frames; {len(forms)} forms; mean adjacent-frame change {np.mean(differences):.2f}/255')
    print(output/'song-motion.mp4')


if __name__=='__main__':main()
