"""Local music playback and measured low/mid/high envelopes. No remote services."""
from pathlib import Path
import math
import numpy as np
import pygame
from .analysis import analyse_track

DEMO_PATH=Path(__file__).resolve().parents[1]/'assets/music/technological-messup.ogg'


def analyse(samples, rate, fps=30):
    data=np.asarray(samples,dtype=np.float32)
    if data.ndim==2:data=data.mean(axis=1)
    if not len(data):raise ValueError('Empty audio')
    if np.max(np.abs(data))>2.:data/=32768.
    size=4096;hop=max(1,int(rate/fps))
    padded=np.pad(data,(size//2,size//2))
    frames=max(1,int(np.ceil(len(data)/hop)))
    levels=np.zeros((frames,3),dtype=np.float32)
    frequency=np.fft.rfftfreq(size,1/rate)
    masks=[(frequency>=lo)&(frequency<hi) for lo,hi in ((40,180),(180,1600),(1600,min(10000,rate*.49)))]
    window=np.hanning(size).astype(np.float32)
    for first in range(0,frames,96):
        indices=(np.arange(first,min(first+96,frames))*hop)[:,None]+np.arange(size)[None,:]
        power=np.abs(np.fft.rfft(padded[indices]*window,axis=1))**2
        for band,mask in enumerate(masks):
            if mask.any():levels[first:first+len(power),band]=np.sqrt(power[:,mask].mean(axis=1))
    # One reference per frequency band preserves real pauses and section dynamics.
    scale=np.maximum(np.percentile(levels,95,axis=0),.001)
    levels=np.clip(levels/scale,0.,1.)
    for i in range(1,frames):levels[i]=levels[i-1]*.40+levels[i]*.60
    return levels


class MusicTrack:
    def __init__(self):
        self.path=None;self.levels=None;self.duration=0.;self.running=False;self.paused=False
        self.volume=.50;self.muted=False;self._position=0.;self._form=-1
        self.auto=True
        self.analysis=None;self.fps=30.;self._attack_cursor=0

    @property
    def playing(self):
        return self.running and not self.paused

    def load(self,path):
        path=Path(path).expanduser().resolve()
        if path.suffix.lower() not in ('.wav','.mp3','.ogg','.flac'):
            raise ValueError('Use WAV, MP3, OGG or FLAC')
        if not path.is_file():raise ValueError('Music file not found')
        sound=pygame.mixer.Sound(str(path))
        duration=sound.get_length()
        if duration>600:raise ValueError('Choose a track shorter than 10 minutes')
        rate=pygame.mixer.get_init()[0]
        analysis=analyse_track(pygame.sndarray.array(sound),rate)
        # Only replace the current track after decoding and analysis have succeeded.
        pygame.mixer.music.load(str(path))
        self.path=path;self.duration=duration;self.levels=analysis.levels
        self.analysis=analysis;self.fps=analysis.fps;self._attack_cursor=0
        self._form=-1;self._position=0.;self.paused=False;self.running=True
        self.auto=True
        pygame.mixer.music.set_volume(0. if self.muted else self.volume)
        pygame.mixer.music.play()

    def pause(self,value):
        if not self.running:return
        if value and not self.paused:pygame.mixer.music.pause()
        elif not value and self.paused:pygame.mixer.music.unpause()
        self.paused=value

    def toggle(self):
        if not self.path:return
        if not self.running:
            pygame.mixer.music.play();self.running=True;self.paused=False;self._form=-1
            self._position=0.;self._attack_cursor=0
        else:self.pause(not self.paused)

    def sample(self):
        pygame.mixer.music.set_volume(0. if self.muted else self.volume)
        if not self.playing:return [0.,0.,0.]
        if not pygame.mixer.music.get_busy():self.running=False;return [0.,0.,0.]
        position=max(0.,pygame.mixer.music.get_pos()/1000.)
        self._position=position
        if self.analysis:return self.analysis.sample(position)
        index=min(len(self.levels)-1,int(position*self.fps))
        return self.levels[index].tolist()

    @property
    def bpm(self):
        return self.analysis.bpm if self.analysis else 120.

    @property
    def beat_position(self):
        if not self.analysis or len(self.analysis.beats)<2:return self._position*self.bpm/60.
        beats=self.analysis.beats
        index=int(np.clip(np.searchsorted(beats,self._position)-1,0,len(beats)-2))
        return index+(self._position-beats[index])/max(.1,beats[index+1]-beats[index])

    @property
    def expansion(self):
        levels=self.analysis.sample(self._position) if self.analysis else [0.,0.,0.]
        energy=sum(a*b for a,b in zip(levels,(.35,.4,.25)))
        phrase=.5-.5*math.cos(self.beat_position*math.tau/8.)
        return min(.92,energy*(.50+.28*phrase))

    def take_attacks(self):
        if not self.playing or not self.analysis:return []
        attacks=self.analysis.attacks;first=self._attack_cursor
        while self._attack_cursor<len(attacks) and attacks[self._attack_cursor].time<=self._position:
            self._attack_cursor+=1
        return [event for event in attacks[first:self._attack_cursor] if self._position-event.time<.15]

    def set_auto(self,value):
        self.auto=bool(value)

    def close(self):
        if pygame.mixer.get_init():pygame.mixer.music.stop();pygame.mixer.music.unload()
