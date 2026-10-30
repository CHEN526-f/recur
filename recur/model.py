"""Two decks, bounded smooth transitions and continuous performance controls."""
import math
from dataclasses import dataclass, field

NAMES = ("SERPENT", "RIBBON", "BLOOM", "CRYSTAL", "ORBIT", "TIDE",
         "IRIS", "CORONA", "ROSETTE", "FACET")
FORM_COUNT = len(NAMES)
VOICE_FOR_FORM = (0,1,2,3,4,5,1,2,2,3)
KEYS = ("A", "S", "D", "J", "K", "L")
LABELS = NAMES


def ease(current, target, rate, dt):
    return current + (target-current)*(1-math.exp(-rate*dt))


def smootherstep(t):
    t=max(0.,min(1.,t))
    return t*t*t*(t*(t*6-15)+10)


@dataclass
class Instrument:
    bpm: int = 108
    clock: float = 0.
    morph: list = field(default_factory=lambda: [1.]+[0.]*(FORM_COUNT-1))
    morph_b: list = field(default_factory=lambda: [0.,1.]+[0.]*(FORM_COUNT-2))
    target: int = 0
    target_b: int = 1
    selected_deck: int = 0
    crossfade: float = 0.
    crossfade_target: float = 0.
    fx: list = field(default_factory=lambda: [.5,.3])
    fx_target: list = field(default_factory=lambda: [.5,.3])
    energy: float = 0.
    energy_target: float = 0.
    bands: list = field(default_factory=lambda: [0.,0.,0.])
    band_targets: list = field(default_factory=lambda: [0.,0.,0.])
    impact: float = 0.
    twist: float = 0.
    charge: float = 0.
    holding: bool = False
    brake: float = 1.
    paused: bool = False
    playing: bool = False
    recording: bool = False
    loop: list = field(default_factory=lambda: [[False]*16 for _ in range(6)])
    loop_b: list = field(default_factory=lambda: [[False]*16 for _ in range(6)])
    events_b: list = field(default_factory=list)
    flashes: list = field(default_factory=lambda: [0.]*6)
    deck_times: list = field(default_factory=lambda: [0.,0.])
    deck_phases: list = field(default_factory=lambda: [0.,0.])
    deck_speeds: list = field(default_factory=lambda: [1.,1.])
    jog: list = field(default_factory=lambda: [None,None])
    accents: list = field(default_factory=lambda: [10.,10.])
    step: int = -1
    step_b: int = -1
    cycle: int = 0
    hits: int = 0
    last_source: str = "READY"
    _ages: list = field(default_factory=lambda: [2.,2.])
    _durations: list = field(default_factory=lambda: [1.35,1.35])
    _starts: list = field(default_factory=lambda: [[1.]+[0.]*(FORM_COUNT-1),[0.,1.]+[0.]*(FORM_COUNT-2)])
    _ticks: list = field(default_factory=lambda: [-1,-1])

    @property
    def weights(self):
        return [a*(1-self.crossfade)+b*self.crossfade for a,b in zip(self.morph,self.morph_b)]

    @property
    def active_loop(self):
        return self.loop if self.selected_deck==0 else self.loop_b

    @property
    def active_target(self):
        return self.target if self.selected_deck==0 else self.target_b

    @property
    def step_seconds(self):
        return 60./self.bpm/4

    def select_shape(self,index,deck=None,duration=1.35):
        deck=self.selected_deck if deck is None else deck
        if not 0<=index<FORM_COUNT or deck not in (0,1):return
        old=self.target if deck==0 else self.target_b
        if old==index:return
        self._starts[deck]=(self.morph if deck==0 else self.morph_b).copy()
        self._ages[deck]=0.
        self._durations[deck]=max(.05,float(duration))
        if deck==0:self.target=index
        else:self.target_b=index

    def trigger(self,index,source="LIVE",deck=None):
        if not 0<=index<6:return
        deck=self.selected_deck if deck is None else deck
        if source not in ("LOOP","DEMO","SCRATCH","FORM","GRID","PAD"):
            self.select_shape(index,deck)
        self.energy_target=min(1.,self.energy_target+.16)
        gain=math.cos(self.crossfade*math.pi/2) if deck==0 else math.sin(self.crossfade*math.pi/2)
        band=(0,2,1,1,0,2)[index]
        self.band_targets[band]=min(1.,self.band_targets[band]+(.70 if index==0 else .40)*gain)
        self.flashes[index]=1.
        self.hits+=1;self.last_source=source
        if self.recording and source not in ("LOOP","DEMO","SCRATCH","GRID"):
            step=round(self.deck_times[deck]/self.step_seconds)%16
            (self.loop if deck==0 else self.loop_b)[index][step]=True

    def advance(self,dt):
        self.events_b=[]
        if self.paused:return []
        dt=max(0.,min(dt,.15));self.clock+=dt
        self.accents=[min(10.,age+dt) for age in self.accents]
        self.energy_target*=math.exp(-dt*1.2)
        self.energy=ease(self.energy,self.energy_target,3.,dt)
        for i in range(3):
            self.band_targets[i]*=math.exp(-dt*(2.8,1.4,3.5)[i])
            self.bands[i]=ease(self.bands[i],self.band_targets[i],10. if self.band_targets[i]>self.bands[i] else 4.,dt)
        self.impact*=math.exp(-dt*3.)
        self.charge=ease(self.charge,1. if self.holding else 0.,1.8,dt)
        self.brake=ease(self.brake,.04 if self.holding else 1.,3.,dt)
        self.crossfade=ease(self.crossfade,self.crossfade_target,7.,dt)
        for k in range(2):self.fx[k]=ease(self.fx[k],self.fx_target[k],5.,dt)
        self.twist=(self.fx[0]-.5)*1.3
        events=[[],[]]
        for deck in (0,1):
            self._ages[deck]+=dt
            blend=smootherstep(self._ages[deck]/self._durations[deck])
            values=self.morph if deck==0 else self.morph_b
            target=self.target if deck==0 else self.target_b
            for i in range(FORM_COUNT):values[i]=self._starts[deck][i]*(1-blend)+(1. if i==target else 0.)*blend
            desired=1. if self.jog[deck] is None else max(-3.,min(3.,self.jog[deck]))
            self.deck_speeds[deck]=ease(self.deck_speeds[deck],desired*self.brake,12.,dt)
            previous_tick=self._ticks[deck]
            self.deck_times[deck]+=dt*self.deck_speeds[deck]
            self.deck_phases[deck]+=dt*self.deck_speeds[deck]*.22
            tick=math.floor(self.deck_times[deck]/self.step_seconds)
            if self.playing and tick!=previous_tick:
                direction=1 if tick>previous_tick else -1
                if abs(tick-previous_tick)<16:
                    for crossed in range(previous_tick+direction,tick+direction,direction):
                        events[deck].extend(i for i in range(6) if (self.loop if deck==0 else self.loop_b)[i][crossed%16])
            self._ticks[deck]=tick
        for i in range(6):self.flashes[i]*=math.exp(-dt*5.)
        self.step=self._ticks[0]%16 if self.playing else -1
        self.step_b=self._ticks[1]%16 if self.playing else -1
        self.events_b=events[1]
        return events[0]

    def release(self):
        amount=self.charge;self.holding=False
        if amount>.1:
            self.energy_target=min(1.,self.energy_target+amount*.4);self.cycle+=1
        return amount

    def reset(self):
        self.select_shape(0,0);self.select_shape(1,1)
        self.energy_target=0.;self.holding=False;self.paused=False
        self.band_targets[:]=[0.,0.,0.]
        self.fx_target[:]=[.5,.3];self.crossfade_target=0.
        self.jog[:]=[None,None]

    def toggle_cell(self,row,col):
        self.active_loop[row][col]=not self.active_loop[row][col]

