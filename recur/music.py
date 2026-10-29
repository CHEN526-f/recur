"""Local music playback and measured low/mid/high envelopes. No remote services."""
from pathlib import Path
import bisect
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
        self.auto=True;self._last_form=None;self._last_change=-100.;self._last_profile=None
        self.analysis=None;self.fps=30.;self._attack_cursor=0;self._cue_cursor=0
        self.morph_seconds=.30

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
        self.analysis=analysis;self.fps=analysis.fps;self._attack_cursor=0;self._cue_cursor=0
        self._form=-1;self._position=0.;self.paused=False;self.running=True
        self.auto=True;self._last_form=None;self._last_change=-100.;self._last_profile=None
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
            self._position=0.;self._attack_cursor=0;self._cue_cursor=0
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
        if self.auto:self._last_change=-100.
        if self.auto and self.analysis:
            self._cue_cursor=max(0,bisect.bisect_right([time for time,_ in self.analysis.cues],self._position)-1)

    def form(self,bpm=None):
        # Spectrum/section response, with enough dwell for each construction to settle.
        if not self.auto or self.levels is None:return None
        if self.analysis:
            lead=min(.32,60/self.bpm*.65);cues=self.analysis.cues
            if self._cue_cursor>=len(cues) or cues[self._cue_cursor][0]>self._position+lead:return None
            cue=cues[self._cue_cursor];self._cue_cursor+=1
            while self._cue_cursor<len(cues) and cues[self._cue_cursor][0]<=self._position:
                cue=cues[self._cue_cursor];self._cue_cursor+=1
            time,shape=cue
            if time<self._position:
                future=[event.time for event in self.analysis.attacks if event.time>self._position+.05]
                if not future:return None
                time=future[0]
            self.morph_seconds=max(.05,time-self._position)
            return shape
        end=min(len(self.levels),int(self._position*self.fps)+1)
        window=self.levels[max(0,end-75):end]
        if not len(window):return None
        profile=window.mean(axis=0)
        if float(profile.max())<.08:return None
        age=self._position-self._last_change
        change=1. if self._last_profile is None else float(np.abs(profile-self._last_profile).mean())
        if age<3.2 or (change<.12 and age<7.5):return None
        low,mid,high=profile.tolist()
        transients=float(np.abs(np.diff(window,axis=0)).mean()) if len(window)>1 else 0.
        if high>max(low,mid)*1.12:
            candidates=(2,6,8) if high>.60 else (2,6)
        elif low>mid*1.15:
            candidates=(0,4,7) if low>.72 else (0,4)
        elif transients>.075:
            candidates=(3,9,5)
        else:
            candidates=(1,5,2)
        chosen=next((form for form in candidates if form!=self._last_form),candidates[0])
        self._last_form=chosen;self._last_change=self._position;self._last_profile=profile.copy()
        return chosen

    def close(self):
        if pygame.mixer.get_init():pygame.mixer.music.stop();pygame.mixer.music.unload()
