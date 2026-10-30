"""Independent one-shot visual voices. New notes never retarget older notes."""
from dataclasses import dataclass
import math
import numpy as np

NAMES=('OPEN','FOLD','PETALS','TURN','DEPTH','RIPPLE')
LIFETIMES=(1.65,2.3,2.65,2.1,3.0,1.25)


def ease(value):
    value=np.clip(value,0.,1.)
    return value*value*(3-2*value)


@dataclass
class Note:
    voice:int
    born:float
    strength:float
    serial:int
    center:tuple
    duration:float
    scheduled:bool=False
    variant:float=0.
    direction:float=1.

    def phase(self,now):return max(0.,min(1.,(now-self.born)/self.duration))

    def envelope(self,now):
        age=now-self.born
        return float(ease(age/.09)*(1-ease((age-self.duration*.52)/(self.duration*.48))))


class InputContacts:
    """A key/finger owns only its own contact, independent of animation tails."""
    def __init__(self):self.held={}

    def down(self,token,voice,callback):
        if token in self.held:return False
        self.held[token]=voice;callback(voice);return True

    def up(self,token):return self.held.pop(token,None)
    def clear(self):self.held.clear()

    @property
    def voices(self):return set(self.held.values())

    @staticmethod
    def zone(x,y):
        return min(2,max(0,int(x*3)))+3*min(1,max(0,int(y*2)))


class PolyphonicStage:
    def __init__(self):
        self.time=0.;self.notes=[];self.serial=0;self.levels=[0.,0.,0.]
        self.contacts=InputContacts();self.last=[-10.]*6;self.counts=[0]*6
        self.fx=[.5,.3]
        self.base_family=6;self.base_age=2.;self.base_duration=1.35
        self.weights=np.eye(10,dtype=float)[6].copy();self.base_start=self.weights.copy()

    def set_base(self,family,duration=1.35):
        self.base_start=self.weights.copy();self.base_family=int(family)
        self.base_age=0.;self.base_duration=max(0.,duration)
        if not duration:
            self.weights=np.eye(10,dtype=float)[self.base_family].copy()
            self.base_start=self.weights.copy();self.base_age=1.

    def reset(self):
        self.notes.clear();self.contacts.clear();self.last=[-10.]*6

    def update(self,model,motion,dt):
        if model.paused:return
        self.time+=max(0.,min(.15,dt))*(.25+.75*model.brake)
        self.levels=list(motion.levels);self.fx=list(model.fx)
        self.base_age+=max(0.,dt)
        blend=float(ease(self.base_age/max(.001,self.base_duration)))
        self.weights=self.base_start*(1-blend)+np.eye(10)[self.base_family]*blend
        self.notes[:]=[note for note in self.notes if self.time-note.born<note.duration]

    def note(self,voice,strength=1.,source='LIVE'):
        if strength<=.015:return None
        if source=='TRACK':
            if voice==0:
                result=self.spawn(0,strength,.19,True)
                if self.levels[0]>.35:self.spawn(4,strength*.5,2.3,True)
                if self.levels[1]>.55 and strength>.8:self.spawn(2,strength*.65,2.,True)
                return result
            if voice==3:
                role=1 if self.levels[2]>.40 else 3
                result=self.spawn(role,strength,.32,True)
                if strength>.72:self.spawn(2,strength*.6,1.5,True)
                return result
            result=self.spawn(5,strength,.16,True)
            if strength>.8 and self.levels[1]>.45:self.spawn(1,strength*.55,.8,True)
            return result
        scheduled=source not in ('LIVE','TOUCH','GRID')
        return self.spawn(voice,strength,.16 if scheduled else 0.,scheduled)

    def spawn(self,voice,strength,cooldown=0.,scheduled=False):
        if self.time-self.last[voice]<cooldown:return None
        # Bound density by declining additional hits, never by removing a live tail.
        if len(self.notes)>=48 or sum(n.voice==voice for n in self.notes)>=8:return None
        self.last[voice]=self.time;self.serial+=1;self.counts[voice]+=1
        angle=self.serial*2.3999632297+voice*.65
        radial=.25+.70*((self.serial*.61803398875)%1.)
        center=(math.cos(angle)*radial*1.25,math.sin(angle)*radial*.65)
        variant=(self.serial*.41421356237+voice*.17)%1.
        duration=(.75,1.45,1.8,1.4,2.0,.8)[voice] if scheduled else LIFETIMES[voice]
        note=Note(voice,self.time,min(1.,max(.05,strength)),self.serial,
                  center,duration,scheduled,variant,
                  1. if self.serial%2 else -1.)
        self.notes.append(note)
        return note
