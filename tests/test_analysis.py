import math
import unittest
import numpy as np
from recur.analysis import analyse_track
from recur.music import MusicTrack
from recur.model import Instrument


def drum_track(rate=22050):
    seconds=16;time=np.arange(seconds*rate)/rate
    data=.035*np.sin(2*np.pi*440*time)*(1-np.exp(-time*8))
    kicks=np.arange(.35,15.,60/128)
    for i,start in enumerate(kicks):
        local=time-start;mask=(local>=0)&(local<.3);t=local[mask]
        data[mask]+=.65*np.sin(2*np.pi*(65*t+.8*(1-np.exp(-t*40))))*np.exp(-t*20)
        # Hats on offbeats, with a syncopated fill to defeat a fixed-BPM timer.
        offset=.21 if i%4!=3 else .14
        local=time-start-offset;mask=(local>=0)&(local<.08);t=local[mask]
        data[mask]+=.12*np.sin(2*np.pi*4300*t)*np.exp(-t*75)
    return data,kicks


class TrackAnalysisTests(unittest.TestCase):
    def test_measured_kicks_align_to_audio_and_retain_syncopated_attacks(self):
        data,kicks=drum_track();analysis=analyse_track(data,22050)
        detected=[e.time for e in analysis.attacks if e.voice==0]
        errors=[min(abs(time-start) for time in detected) for start in kicks]
        self.assertLess(max(errors),.025)
        self.assertAlmostEqual(analysis.bpm,128.,delta=2.)
        self.assertTrue(any(e.voice==5 for e in analysis.attacks))
        self.assertTrue(all(any(abs(time-e.time)<.0001 for e in analysis.attacks) for time,_ in analysis.cues))
        self.assertGreater(np.mean([min(abs(t-e.time) for e in analysis.attacks)<.03 for t in analysis.beats]),.9)

    def test_silence_and_sustained_note_do_not_invent_a_drum_pattern(self):
        silence=analyse_track(np.zeros(22050*3),22050)
        self.assertEqual(silence.attacks,());self.assertEqual(silence.cues,())
        time=np.arange(22050*4)/22050
        tone=analyse_track(.2*np.sin(2*np.pi*440*time),22050)
        self.assertFalse(any(.2<e.time<3.8 for e in tone.attacks))

    def test_import_clock_consumes_each_attack_once_and_pause_holds_it(self):
        data,_=drum_track();analysis=analyse_track(data,22050)
        track=MusicTrack();track.analysis=analysis;track.levels=analysis.levels;track.running=True
        played=[]
        for frame in range(16*60+1):
            track._position=frame/60
            attacks=track.take_attacks();played.extend(attacks)
            self.assertEqual(track.take_attacks(),[])
            self.assertTrue(all(0<=track._position-e.time<1/60+.00001 for e in attacks))
        self.assertEqual(played,list(analysis.attacks))
        track.paused=True;self.assertEqual(track.take_attacks(),[])

    def test_morph_prepares_before_audio_accent_and_lands_on_it(self):
        data,_=drum_track();analysis=analyse_track(data,22050)
        track=MusicTrack();track.analysis=analysis;track.levels=analysis.levels
        model=Instrument();landings=[]
        for frame in range(16*120):
            track._position=frame/120
            form=track.form()
            if form is not None:
                target=track._position+track.morph_seconds
                model.select_shape(form,0,track.morph_seconds)
                landings.append((target,form))
            model.advance(1/120)
            for target,form in landings:
                if target<=track._position<target+1/120:
                    self.assertAlmostEqual(model.morph[form],1.,places=5)
        self.assertGreater(len(landings),2)
        self.assertTrue(all(any(abs(time-beat)<.001 for beat in analysis.beats) for time,_ in landings[1:]))
