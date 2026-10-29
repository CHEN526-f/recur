"""Offline spectral transients and beat-aligned cues; NumPy only, no network."""
from dataclasses import dataclass
import math
import numpy as np


@dataclass(frozen=True)
class Attack:
    time: float
    voice: int
    strength: float


@dataclass
class TrackAnalysis:
    levels: np.ndarray
    fps: float
    attacks: tuple
    beats: np.ndarray
    bpm: float
    cues: tuple
    duration: float

    def sample(self,time):
        position=max(0.,min(len(self.levels)-1,time*self.fps))
        first=int(position);last=min(first+1,len(self.levels)-1);fraction=position-first
        return (self.levels[first]*(1-fraction)+self.levels[last]*fraction).tolist()


def _tempo(novelty,fps):
    if len(novelty)<fps*2 or float(novelty.max())<.1:return 120.
    data=novelty-novelty.mean()
    n=1<<(len(data)*2-1).bit_length()
    spectrum=np.fft.rfft(data,n=n)
    correlation=np.fft.irfft(spectrum*spectrum.conj(),n=n)[:len(data)]
    correlation/=np.maximum(1,np.arange(len(data),0,-1))
    lags=np.arange(round(fps*60/180),round(fps*60/80)+1)
    scores=correlation[lags]+.25*correlation[np.minimum(lags*2,len(data)-1)]
    lag=int(lags[np.argmax(scores)])
    # Parabolic sub-frame estimate reduces drift over long tracks.
    if 0<lag<len(correlation)-1:
        a,b,c=correlation[lag-1:lag+2];den=a-2*b+c
        offset=float(.5*(a-c)/den) if abs(den)>1e-12 else 0.
    else:offset=0.
    return float(60*fps/(lag+max(-.5,min(.5,offset))))


def analyse_track(samples,rate):
    data=np.asarray(samples,dtype=np.float32)
    if data.ndim==2:data=data.mean(axis=1)
    if not len(data):raise ValueError('Empty audio')
    if np.max(np.abs(data))>2.:data=data/32768.
    duration=len(data)/rate
    stride=max(1,round(rate/22050));data=data[::stride];rate=rate/stride
    hop=max(1,round(rate/100));fps=rate/hop;size=1024
    padded=np.pad(data,(size//2,size//2));frames=int(math.ceil(len(data)/hop))
    levels=np.zeros((frames,3),dtype=np.float32);flux=np.zeros_like(levels)
    frequency=np.fft.rfftfreq(size,1/rate)
    masks=[(frequency>=lo)&(frequency<hi) for lo,hi in ((35,190),(190,2000),(2000,min(10000,rate*.49)))]
    window=np.hanning(size).astype(np.float32);previous=None
    for first in range(0,frames,128):
        indices=(np.arange(first,min(first+128,frames))*hop)[:,None]+np.arange(size)[None,:]
        magnitude=np.abs(np.fft.rfft(padded[indices]*window,axis=1))
        prior=np.vstack((np.zeros((1,magnitude.shape[1])) if previous is None else previous[None,:],magnitude[:-1]))
        rise=np.maximum(0.,magnitude-prior);previous=magnitude[-1]
        for band,mask in enumerate(masks):
            if mask.any():
                levels[first:first+len(magnitude),band]=np.sqrt((magnitude[:,mask]**2).mean(axis=1))
                flux[first:first+len(magnitude),band]=rise[:,mask].mean(axis=1)
    reference=np.maximum(np.percentile(levels,97,axis=0),.002)
    flux_scale=np.maximum(np.percentile(flux,95,axis=0),reference*.045)
    # Leakage in a nearly empty band must not be normalized into a fictitious drum.
    flux_scale=np.maximum(flux_scale,max(.001,float(reference.max())*.003))
    normalized=np.clip(flux/flux_scale,0.,4.)
    novelty=np.maximum.reduce((normalized[:,0],normalized[:,1]*.7,normalized[:,2]*.65))
    width=min(frames,round(fps*.5));kernel=np.ones(width)/width
    average=np.convolve(novelty,kernel,mode='same')
    deviation=np.sqrt(np.maximum(0.,np.convolve(novelty**2,kernel,mode='same')-average**2))
    peaks=np.flatnonzero((novelty>np.maximum(.30,average+deviation*.45))
                         &(novelty>=np.roll(novelty,1))&(novelty>np.roll(novelty,-1)))
    # Refine FFT timing on a 5 ms causal energy slope (FFT windows see ahead).
    milliseconds=max(1,round(rate/1000))
    count=int(math.ceil(len(data)/milliseconds))
    square=np.pad(data*data,(0,count*milliseconds-len(data)))
    energy=square.reshape(-1,milliseconds).mean(axis=1)
    energy=np.convolve(energy,np.ones(5)/5,mode='same')
    slope=np.maximum(0.,np.diff(energy,prepend=0.))
    attacks=[]
    for index in peaks:
        expected=index/fps
        left=max(0,round((expected-.030)*rate/milliseconds))
        right=min(len(slope),round((expected+.026)*rate/milliseconds)+1)
        refined=(left+int(np.argmax(slope[left:right])))*milliseconds/rate-.001 if right>left else expected
        time=max(0.,refined)
        if attacks and time-attacks[-1].time<.075:
            if novelty[index]<=attacks[-1].strength*1.6:continue
            attacks.pop()
        low,mid,high=normalized[index]
        voice=0 if low>=max(mid*.75,high*.65) else 5 if high>mid*.8 else 3
        strength=float(np.clip(novelty[index]/1.8,.25,1.))
        attacks.append(Attack(time,voice,strength))
    attacks=tuple(sorted(attacks,key=lambda event:event.time))
    bpm=_tempo(novelty,fps);period=60/bpm
    # Use a grid only for phrasing. Actual motion attacks always use the measured events.
    anchor_candidates=[e for e in attacks if e.voice==0 and e.time<8.] or list(attacks[:20])
    if anchor_candidates:
        times=np.array([e.time for e in attacks]);weights=np.array([e.strength*(1.5 if e.voice==0 else .7) for e in attacks])
        def score(anchor):
            distance=np.abs((times-anchor+period/2)%period-period/2)
            return float(np.sum(weights*np.exp(-(distance/(period*.12))**2)))
        anchor=max(anchor_candidates,key=lambda e:score(e.time)).time%period
        beats=np.arange(anchor,duration,period)
        for i,predicted in enumerate(beats):
            near=np.flatnonzero(np.abs(times-predicted)<period*.20)
            if len(near):beats[i]=times[near[np.argmax(weights[near]*np.exp(-((times[near]-predicted)/(period*.14))**2))]]
    else:beats=np.array([],dtype=float)
    levels=np.clip(levels/reference,0.,1.).astype(np.float32)
    # Audio determines energy and family; a bounded route keeps the vocabulary rich.
    routes=((0,4,7,0,5),(1,5,2,3,9),(2,6,8,4,1))
    cues=[];last=-1
    phrase_beats=8 if bpm>=110 else 4
    for beat in range(0,len(beats),phrase_beats):
        predicted=float(beats[beat])
        nearest=min(attacks,key=lambda event:abs(event.time-predicted),default=None)
        if nearest is None or abs(nearest.time-predicted)>period*.21:continue
        time=nearest.time
        index=min(frames-1,round(time*fps))
        profile=levels[max(0,index-round(fps)):min(frames,index+round(fps))].mean(axis=0)
        if float(profile.max())<.08:continue
        family=int(np.argmax(profile*np.array((1.,1.,1.10))))
        route=routes[family];slot=(beat//phrase_beats)%len(route)
        shape=next((route[(slot+n)%len(route)] for n in range(len(route)) if route[(slot+n)%len(route)]!=last),route[slot])
        cues.append((time,shape));last=shape
    return TrackAnalysis(levels,fps,attacks,beats,bpm,tuple(cues),duration)
