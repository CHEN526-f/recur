"""An authored 32-bar piece and chord-aware live notes; no external music service."""
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Note:
    tick: int
    voice: int
    deck: int = 0
    note: int | None = None
    velocity: float = .7
    chord: tuple = ()
    variant: str = ''


CHORDS = (
    ('Dm9',38,(50,53,57,60,64)),
    ('Bbmaj9',34,(50,53,57,60,62)),
    ('Fmaj9',41,(53,57,60,64,67)),
    ('Cadd9',36,(48,52,55,62,67)),
)
SECTIONS = ((0,'INTRO'),(4,'THEME'),(12,'BUILD'),(16,'PEAK'),(24,'BREAK'),(28,'OUTRO'))
BAR_COUNT = 32
# Two bars per phrase. Open, asymmetrical originals remain most of the vocabulary.
SONG_FORMS = (0,1,5,2,4,9,3,5,6,2,7,8,1,5,4,0)


def harmony(bar):
    return CHORDS[(bar//2)%len(CHORDS)]


def section(bar):
    return next(name for start,name in reversed(SECTIONS) if bar>=start)


def build_score():
    notes=[]
    for bar in range(BAR_COUNT):
        label=section(bar);_,root,chord=harmony(bar)
        def add(step,voice,note=None,velocity=.6,chord=(),variant=''):
            deck=0 if voice in (0,4,5) else 1
            notes.append(Note(bar*16+step,voice,deck,note,velocity,chord,variant))
        # Space in the opening and breakdown; a clear four-to-the-floor peak.
        kicks=(0,8) if label=='INTRO' else (0,) if label=='BREAK' else (0,4,8,12)
        if label=='OUTRO' and bar>=30:kicks=(0,8) if bar==30 else (0,)
        for step in kicks:add(step,0,velocity=.82 if step==0 else .70)
        if label!='BREAK' and bar<31:
            hats=(2,6,10,14) if label!='PEAK' else (2,3,6,10,11,14,15)
            for step in hats:
                if label=='INTRO' and bar<2 and step not in (6,14):continue
                add(step,5,velocity=.26 if step%2==0 else .13)
        if label in ('THEME','BUILD','PEAK'):
            for step in (4,12):add(step,5,velocity=.48,variant='clap')
        if bar%2==0:add(0,2,velocity=.72,chord=chord)
        if bar>=2 and bar<30 and label!='BREAK':
            bass=((0,root,.72),(6,root,.48),(8,root+12,.54),(14,root+7,.43))
            for step,note,velocity in bass:
                if label=='INTRO' and step not in (0,8):continue
                add(step,4,note,velocity)
        elif label=='BREAK' and bar%2==0:add(0,4,root,.45)
        # A recurrent motif moves through four voicings, with answer phrases.
        melody=(chord[0]+12,chord[2]+12,chord[3]+12,chord[1]+12,
                chord[4]+12,chord[3]+12,chord[2]+12,chord[0]+12)
        if label not in ('INTRO','BREAK','OUTRO') or bar in (3,25,27,28):
            steps=(2,6,10,14) if label in ('THEME','BUILD') else (0,3,6,8,11,14) if label=='PEAK' else (2,10)
            for position,step in enumerate(steps):
                slot=(position+(bar%2)*4)%len(melody)
                add(step,1,melody[slot],.42 if position%2==0 else .32)
        if label in ('BUILD','PEAK') or (label=='THEME' and bar%2):
            for position,step in enumerate((1,7,13)):
                add(step,3,chord[(position+bar)%len(chord)]+12,.30)
        if label in ('BUILD','PEAK') and bar%4==3:
            for step in (13,14,15):add(step,5,velocity=.22+(step-13)*.05,variant='clap')
    return tuple(sorted(notes,key=lambda n:(n.tick,n.deck,n.voice)))


class Performance:
    def __init__(self):
        self.score=build_score();self.position=0.;self._tick=-1
        self.playing=False;self.done=False;self.octave=0;self.counters=[0]*6
        self.auto=True;self._visual_phrase=-1
        self._events={}
        for note in self.score:self._events.setdefault(note.tick,[]).append(note)

    @property
    def bar(self):
        return min(BAR_COUNT-1,int(self.position)//16)

    @property
    def label(self):
        return section(self.bar)

    @property
    def chord_name(self):
        return harmony(self.bar)[0]

    def start(self):
        self.position=0.;self._tick=-1;self.done=False;self.playing=True
        self.auto=True;self._visual_phrase=-1

    def stop(self):
        self.playing=False

    def set_auto(self,value):
        self.auto=bool(value)
        if self.auto:self._visual_phrase=-1

    def form(self):
        phrase=self.bar//2
        if not self.playing or not self.auto or phrase==self._visual_phrase:return None
        self._visual_phrase=phrase
        return SONG_FORMS[phrase]

    @property
    def expansion(self):
        # Phrases open AND close; dense melody no longer pins expansion at 100%.
        position=self.position/16.
        base={'INTRO':.08,'THEME':.25,'BUILD':.42,'PEAK':.66,'BREAK':.12,'OUTRO':.24}[self.label]
        if self.label=='BUILD':base+=(position-12)*.045
        if self.label=='OUTRO':base*=max(0.,(32-position)/4)
        breath=.5-.5*math.cos(self.position/32.*math.tau)
        return min(.96,base+breath*(.26 if self.label=='PEAK' else .13))

    def advance(self,dt,bpm=108,paused=False,speed=1.):
        if not self.playing or paused:return []
        self.position+=max(0.,min(dt,.15))*bpm/60.*4.*max(0.,speed)
        tick=min(BAR_COUNT*16-1,math.floor(self.position))
        events=[note for crossed in range(self._tick+1,tick+1) for note in self._events.get(crossed,())]
        self._tick=tick
        if self.position>=BAR_COUNT*16:self.done=True;self.playing=False
        return events

    def live(self,voice,beat):
        _,root,chord=harmony(int(beat//4))
        count=self.counters[voice];self.counters[voice]+=1
        if voice in (1,3):
            order=(0,2,3,1,4,3,2,0)
            pitch=chord[order[count%8]]+12+self.octave*12
            return Note(0,voice,note=pitch,velocity=.68 if voice==1 else .76)
        if voice==2:return Note(0,voice,velocity=.85,chord=chord)
        if voice==4:return Note(0,voice,note=root+(0,7,12,7)[count%4],velocity=.85)
        return Note(0,voice,velocity=.88 if voice==0 else .55)
