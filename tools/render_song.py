"""Export the same authored score and synthesizer voices used by T / SONG."""
import os
os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
from pathlib import Path
import sys
import math
import wave
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pygame
from recur.audio import Synth
from recur.composition import build_score,BAR_COUNT

synth=Synth();bpm=108;rate=synth.RATE;seconds_per_tick=60/bpm/4
synth.controls=(.45,.5,.3,1.)
score=build_score()
mix=np.zeros((int((BAR_COUNT*16*seconds_per_tick+3.6)*rate),2),dtype=np.float32)
for event in score:
    pcm=synth.voice_pcm(event.voice,note=event.note,chord=event.chord,variant=event.variant)
    gain=math.cos(.45*math.pi/2) if event.deck==0 else math.sin(.45*math.pi/2)
    audio=pcm.astype(np.float32)/32768.*event.velocity*synth.volume*gain
    start=int(event.tick*seconds_per_tick*rate);end=min(len(mix),start+len(audio))
    mix[start:end]+=audio[:end-start]
peak=float(np.abs(mix).max())
if peak>.75:mix*=.75/peak
out=Path('captures');out.mkdir(exist_ok=True)

def save(path,data):
    data=data.copy()
    fade_in=min(len(data),int(rate*.035));fade_out=min(len(data),int(rate*.8))
    data[:fade_in]*=np.linspace(0,1,fade_in)[:,None]
    data[-fade_out:]*=np.linspace(1,0,fade_out)[:,None]
    with wave.open(str(path),'wb') as wav:
        wav.setnchannels(2);wav.setsampwidth(2);wav.setframerate(rate)
        wav.writeframes(np.ascontiguousarray(data*32767,dtype='<i2').tobytes())

save(out/'recur-song.wav',mix)
save(out/'recur-song-preview.wav',mix[int(12*16*seconds_per_tick*rate):int(21*16*seconds_per_tick*rate)])
pygame.mixer.quit()
print(f'SONG: {BAR_COUNT} bars, {len(score)} events, peak={peak:.3f}, {(len(mix)/rate):.1f}s')
print((out/'recur-song.wav').resolve())
