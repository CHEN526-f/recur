"""Transient-led articulation, shared by the score, live notes and local music."""
import math


class MusicalMotion:
    def __init__(self):
        self.pulses=[0.,0.,0.]
        self.levels=[0.,0.,0.]
        self.external=[0.,0.,0.]
        self.detect_external=True
        self._previous=[0.,0.,0.]
        self._kick=0.
        self.activity=0.
        self.beat=0.
        self.travel=0.
        self.transport_beat=None
        self.values=(0.,0.,0.,0.)
        self.phases=(0.,0.)
        self.voice_totals=[0.]*6
        self.on_note=None

    def note(self,voice,velocity=1.,gain=1.,source='LIVE'):
        amount=max(0.,min(1.,velocity*gain))
        self.voice_totals[voice]+=amount
        band=(0,2,1,1,0,2)[voice]
        self.pulses[band]=max(self.pulses[band],amount)
        if voice==0:self._kick=max(self._kick,amount)
        elif voice==4:self._kick=max(self._kick,amount*.35)
        if amount>0. and self.on_note:return self.on_note(voice,amount,source)

    def update(self,model,dt):
        if model.paused:return
        dt=max(0.,min(.15,dt))
        source=[max(0.,min(1.,x)) for x in self.external]
        for i in range(3):
            # Rises in the measured audio, not a free-running invented drum beat.
            onset=max(0.,source[i]-self._previous[i]-.018) if self.detect_external else 0.
            self.pulses[i]=max(self.pulses[i],min(1.,onset*(3.8,2.8,4.5)[i]))
            if i==0:self._kick=max(self._kick,min(1.,onset*4.5))
            self._previous[i]=source[i]
            rate=20. if source[i]>self.levels[i] else 5.
            self.levels[i]+=(source[i]-self.levels[i])*(1-math.exp(-dt*rate))
        desired=max(max(self.pulses),max(self.levels))
        self.activity+=(desired-self.activity)*(1-math.exp(-dt*(18. if desired>self.activity else 2.4)))
        self.beat=self.transport_beat if self.transport_beat is not None else self.beat+dt*model.bpm/60.*model.brake
        self.travel+=dt*(.5+self.pulses[1]*1.8+self._kick*.8)*self.activity*model.brake
        self.values=(self._kick,max(self.pulses[1],self.levels[1]*.85),
                     max(self.pulses[2],self.levels[2]*.7),self.activity)
        self.phases=(self.beat*math.tau/4.,self.travel)
        self._kick*=math.exp(-dt*9.)
        for i,rate in enumerate((6.,2.6,12.)):self.pulses[i]*=math.exp(-dt*rate)

    def reset(self):
        self.pulses[:]=[0.,0.,0.];self.levels[:]=[0.,0.,0.]
        self.external[:]=[0.,0.,0.];self._previous[:]=[0.,0.,0.]
        self._kick=self.activity=self.travel=0.
        self.beat=0.;self.phases=(0.,0.)
        self.transport_beat=None;self.values=(0.,0.,0.,0.)
        self.voice_totals[:]=[0.]*6

