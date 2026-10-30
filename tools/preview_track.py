"""Export the app's measured music/motion path, with the original recording."""
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
os.environ['SDL_AUDIODRIVER']='dummy'
import argparse
from pathlib import Path
from fractions import Fraction
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'.reference/packages'))
import av
import numpy as np
import pygame
from PIL import Image,ImageDraw
from recur.model import Instrument
from recur.renderer import SculptureRenderer
from recur.music import MusicTrack,DEMO_PATH


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--music',default=str(DEMO_PATH))
    parser.add_argument('--output',default='captures/rhythm-demo.mp4')
    parser.add_argument('--seconds',type=float,default=20.)
    args=parser.parse_args();fps=30;size=(1100,704)
    pygame.mixer.init(44100,-16,2,512);pygame.display.init()
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION,3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION,3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK,pygame.GL_CONTEXT_PROFILE_CORE)
    pygame.display.set_mode(size,pygame.OPENGL|pygame.DOUBLEBUF|pygame.HIDDEN)
    music=MusicTrack();music.load(args.music);music.muted=True
    pcm=pygame.sndarray.array(pygame.mixer.Sound(args.music))
    renderer=SculptureRenderer(size);renderer.instrument_visible=False;renderer.music=music
    renderer.evolution.strength=1.
    renderer.motion.detect_external=False
    model=Instrument();overlay=bytes(size[0]*size[1]*4)
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    seconds=min(args.seconds,music.duration);pcm=pcm[:round(seconds*44100)]
    container=av.open(str(output),'w',options={'movflags':'+faststart'})
    video=container.add_stream('libx264',rate=fps);video.width,video.height=size
    video.pix_fmt='yuv420p';video.options={'crf':'19','preset':'fast'}
    audio=container.add_stream('aac',rate=44100);audio.layout='stereo';audio.bit_rate=192000
    checkpoints=tuple(np.linspace(min(1.,seconds*.15),max(.1,seconds-1.),12))
    sheet=Image.new('RGB',(1440,240*((len(checkpoints)+3)//4)),'#090b0c');draw=ImageDraw.Draw(sheet)
    proof=0;forms=set();attacks=0
    try:
        for index in range(round(seconds*fps)):
            pygame.event.pump();time=index/fps;music._position=time
            measured=music.analysis.sample(time);renderer.motion.external=measured
            renderer.climax.music_level=sum(a*b for a,b in zip(measured,(.2,.35,.45)))
            for event in music.take_attacks():
                renderer.motion.note(event.voice,(.45+.55*event.strength)*np.exp(-(time-event.time)*9.));attacks+=1
            for i in range(3):model.band_targets[i]=max(model.band_targets[i],measured[i])
            model.energy_target=max(model.energy_target,sum(measured)/3)
            model.advance(1/fps);renderer.draw(model,overlay);forms.add(model.target)
            pixels=np.frombuffer(renderer.ctx.screen.read(components=3,alignment=1),dtype=np.uint8)
            pixels=pixels.reshape(size[1],size[0],3)[::-1].copy()
            frame=av.VideoFrame.from_ndarray(pixels,format='rgb24');frame.pts=index
            for packet in video.encode(frame):container.mux(packet)
            if proof<len(checkpoints) and time>=checkpoints[proof]:
                im=Image.fromarray(pixels);im.save(output.with_name(f'{output.stem}-{proof+1}.png'))
                im.thumbnail((356,212));x=(proof%4)*360;y=(proof//4)*240
                sheet.paste(im,(x,y+25));draw.text((x+8,y+6),f'{time:.2f}s / {renderer.evolution.vj.label}',fill='#e5d9ad')
                proof+=1
            pygame.display.flip()
        for packet in video.encode():container.mux(packet)
        for first in range(0,len(pcm),1024):
            samples=pcm[first:first+1024].astype(np.float32).T.copy()/32768*.5
            frame=av.AudioFrame.from_ndarray(samples,format='fltp',layout='stereo')
            frame.sample_rate=44100;frame.time_base=Fraction(1,44100);frame.pts=first
            for packet in audio.encode(frame):container.mux(packet)
        for packet in audio.encode():container.mux(packet)
    finally:container.close();music.close();pygame.quit()
    sheet.save(output.with_suffix('.jpg'))
    print(f'TRACK PREVIEW OK: {seconds:.1f}s; {len(forms)} fixed base; continuous geometry; {attacks} measured attacks; {output}')


if __name__=='__main__':main()
