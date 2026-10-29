"""Original, locally synthesized patches. No copied music, samples, or API."""
import math
import numpy as np
import pygame


class Synth:
    RATE = 44100

    def __init__(self):
        self.enabled = False
        self.muted = False
        self.volume = .5
        self.duck = 1.
        self.error = ""
        self.sounds = []
        self.raw = []
        self.cache = {}
        self.raw_cache = {}
        self.channel_velocities = [[1.]*12 for _ in range(2)]
        self.voice_turn = [[0]*6 for _ in range(2)]
        self.controls = (0., .5, .3, 1.)
        self.channels = [[], []]
        self.scratch_channels = []
        try:
            pygame.mixer.init(frequency=self.RATE, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(32)
            self.raw = [self.patch(i) for i in range(6)]
            self.sounds = [pygame.sndarray.make_sound(x) for x in self.raw]
            self.channels = [[pygame.mixer.Channel(i) for i in range(12)], [pygame.mixer.Channel(i) for i in range(12,24)]]
            self.scratch_channels = [pygame.mixer.Channel(24),pygame.mixer.Channel(25)]
            self.drop_sound = pygame.sndarray.make_sound(self.make_drop())
            self.enabled = True
        except (pygame.error, ValueError) as exc:
            self.error = str(exc)

    @staticmethod
    def stereo(wave, pan=0., rate=44100):
        # A quiet stereo delay gives spatial width; normalize then limit gain.
        delay = int(rate * .083)
        echo = np.zeros_like(wave)
        echo[delay:] = wave[:-delay] * .14
        left = wave * (1. - pan * .3) + echo
        right = wave * (1. + pan * .3) + np.roll(echo, int(rate * .027))
        data = np.column_stack((left, right))
        peak = max(1., float(np.abs(data).max()))
        return np.ascontiguousarray(np.clip(data / peak * .34, -1., 1.) * 32767, dtype=np.int16)

    def patch(self, index,note=None,chord=(),variant=''):
        # Pitched voices share the score's harmonic palette.
        lengths=[.85,1.6,3.6,1.7,1.5,.45]
        t=np.arange(int(self.RATE*lengths[index]))/self.RATE
        if index==0:
            frequency=36.708+45.*np.exp(-t*28.)
            phase=2*np.pi*np.cumsum(frequency)/self.RATE
            y=.85*np.sin(phase)*np.exp(-t*8.)
            y+=.055*np.sin(2*np.pi*146.83*t)*np.exp(-t*25.)
            y+=.20*np.sin(2*np.pi*73.416*t)*np.exp(-t*10.)
        elif index==1:
            f=440. if note is None else 440.*2**((note-69)/12.)
            y=(.65*np.sin(2*np.pi*f*t)*np.exp(-t*3.2)
               +.12*np.sin(2*np.pi*f*2.002*t)*np.exp(-t*5.)
               +.035*np.sin(2*np.pi*f*3.*t)*np.exp(-t*7.))
            y*=1-np.exp(-t*75.)
        elif index==2:
            y=np.zeros_like(t)
            frequencies=[440.*2**((n-69)/12.) for n in (chord or (50,53,57,60,64))]
            for i,f in enumerate(frequencies):
                y+=(np.sin(2*np.pi*f*t+i*.71)+.08*np.sin(2*np.pi*f*2*t))/len(frequencies)
            y*=.72*(1-np.exp(-t*5.))*np.exp(-t*.95)
        elif index==3:
            f=349.228 if note is None else 440.*2**((note-69)/12.)
            y=(.68*np.sin(2*np.pi*f*t)+.12*np.sin(2*np.pi*f*2*t))*np.exp(-t*4.)
            y*=1-np.exp(-t*110.)
        elif index==4:
            f=73.416 if note is None else 440.*2**((note-69)/12.)
            y=(.67*np.sin(2*np.pi*f*t)+.25*np.sin(2*np.pi*f*2*t)
               +.14*np.sin(2*np.pi*f*3*t))
            y*=(1-np.exp(-t*32.))*np.exp(-t*3.)
        else:
            rng=np.random.default_rng(895)
            noise=rng.normal(0.,.7,len(t))
            fine=np.convolve(noise,np.ones(3)/3,mode='same')
            broad=np.convolve(noise,np.ones(23)/23,mode='same')
            y=(fine-broad)*np.exp(-t*24.)*.68
            if variant=='clap':
                envelope=sum(gain*np.exp(-np.maximum(t-delay,0.)*23.)*(t>=delay)
                             for delay,gain in ((0.,.65),(.014,.38),(.029,.25)))
                y=(fine-broad*.45)*envelope*.70
                y+=.10*np.sin(2*np.pi*185*t)*np.exp(-t*20.)
        y*=np.minimum(1.,t*220.)*np.minimum(1.,(t[-1]-t)*80.)
        return self.stereo(y,(index-2.5)/5)

    def make_drop(self):
        t=np.arange(int(self.RATE*2.5))/self.RATE
        y=.65*np.sin(2*np.pi*36.708*t)*(1-np.exp(-t*55.))*np.exp(-t*2.8)
        for f in (146.832,174.614,220.,261.626):
            y+=.065*np.sin(2*np.pi*f*t)*(1-np.exp(-t*6.))*np.exp(-t*1.5)
        y*=np.minimum(1.,(t[-1]-t)*50.)
        return self.stereo(y)

    def update(self,model):
        self.controls=(model.crossfade,model.fx[0],model.fx[1],model.brake)
        if not self.enabled:return
        for deck in (0,1):
            gain=self.volume*(math.cos(model.crossfade*math.pi/2) if deck==0 else math.sin(model.crossfade*math.pi/2))
            gain*=min(1.,model.brake*2.)
            gain*=self.duck
            if self.muted:gain=0.
            for i,ch in enumerate(self.channels[deck]):ch.set_volume(gain*self.channel_velocities[deck][i])
            self.scratch_channels[deck].set_volume(gain)

    def voice_pcm(self,index,rate=1.,reverse=False,note=None,chord=(),variant=''):
        # Filter/pitch are applied to new voices, while the mixer crossfades live tails.
        _,tone,echo,brake=self.controls
        speed=round(max(.15,min(2.,abs(rate)*max(.15,brake)))*8)/8
        band=int(tone*5)
        echo_band=int(echo*3)
        raw_key=(index,note,tuple(chord),variant)
        if note is None and not chord and not variant:raw=self.raw[index]
        else:
            if raw_key not in self.raw_cache:
                if len(self.raw_cache)>=64:self.raw_cache.pop(next(iter(self.raw_cache)))
                self.raw_cache[raw_key]=self.patch(index,note,chord,variant)
            raw=self.raw_cache[raw_key]
        raw=raw.astype(np.float32)/32768.
        if reverse:raw=raw[::-1]
        points=np.arange(0,len(raw)-1,speed)
        lo=points.astype(np.int32);a=(points-lo)[:,None]
        wave=raw[lo]*(1-a)+raw[lo+1]*a
        # Short, role-specific filters keep percussion audible at the default FX.
        width=([7,5,3,1,1,1] if index in (0,5) else [15,9,5,3,1,1])[band]
        if width>1:
            for ch in range(2):wave[:,ch]=np.convolve(wave[:,ch],np.ones(width)/width,mode='same')
        delay=int(self.RATE*.19)
        wet=echo_band*.12
        for n in (1,2):
            shift=delay*n
            if len(wave)>shift:wave[shift:]+=wave[:-shift].copy()*(wet/n)
        return np.ascontiguousarray(np.clip(wave,-.7,.7)*32767,dtype=np.int16)

    def voice(self,index,rate=1.,reverse=False,note=None,chord=(),variant=''):
        _,tone,echo,brake=self.controls
        speed=round(max(.15,min(2.,abs(rate)*max(.15,brake)))*8)/8
        key=(index,speed,int(tone*5),int(echo*3),reverse,note,tuple(chord),variant)
        if key not in self.cache:
            pcm=self.voice_pcm(index,rate,reverse,note,chord,variant)
            if len(self.cache)>=96:self.cache.pop(next(iter(self.cache)))
            self.cache[key]=pygame.sndarray.make_sound(pcm)
        return self.cache[key]

    def play(self,index,deck=0,rate=1.,note=None,velocity=1.,chord=(),variant=''):
        if self.enabled and not self.muted:
            sound=self.voice(index,rate,rate<0,note,chord,variant)
            # Two voices per role: a melody cannot steal a bass or chord channel.
            slot=index*2+self.voice_turn[deck][index]
            self.voice_turn[deck][index]=1-self.voice_turn[deck][index]
            self.channel_velocities[deck][slot]=max(0.,min(1.,velocity))
            channel=self.channels[deck][slot]
            cross,_,_,brake=self.controls
            gain=self.volume*(math.cos(cross*math.pi/2) if deck==0 else math.sin(cross*math.pi/2))
            channel.set_volume(gain*min(1.,brake*2.)*self.duck*self.channel_velocities[deck][slot])
            channel.play(sound,fade_ms=8)

    def prepare(self,score):
        if not self.enabled:return
        seen=set()
        for event in score:
            key=(event.voice,event.note,event.chord,event.variant)
            if key not in seen:
                self.voice(event.voice,note=event.note,chord=event.chord,variant=event.variant)
                seen.add(key)

    def scratch(self,index,deck,position,velocity):
        if not self.enabled or self.muted or abs(velocity)<.07:return
        raw=self.raw[index]
        n=3072;offset=int((position%1)*max(1,len(raw)-n-1))
        grain=raw[offset:offset+n].astype(np.float32)
        if velocity<0:grain=grain[::-1]
        grain*=np.hanning(len(grain))[:,None]*.8
        sound=pygame.sndarray.make_sound(np.ascontiguousarray(grain,dtype=np.int16))
        self.scratch_channels[deck].play(sound,fade_ms=5)

    def drop(self, amount):
        if self.enabled and not self.muted and amount > .1:
            self.drop_sound.set_volume(self.volume * min(1., amount + .25))
            self.drop_sound.play()

    def silence(self):
        if self.enabled:
            pygame.mixer.stop()

