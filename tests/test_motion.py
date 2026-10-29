import math
import unittest
from recur.model import Instrument
from recur.motion import MusicalMotion
from recur.structures import center


class MotionTests(unittest.TestCase):
    def test_kick_moves_real_geometry_then_recovers_instead_of_saturating(self):
        state=MusicalMotion();model=Instrument()
        weights=[1.]+[0.]*9
        quiet=center(.4,1,0.,(0.,0.,0.),weights)
        state.note(0,.9);state.update(model,1/60)
        attack=center(.4,1,0.,(0.,0.,0.),weights,motion=state.values,motion_phase=state.phases)
        self.assertGreater(math.dist(quiet,attack),.20)
        for _ in range(120):state.update(model,1/60)
        self.assertLess(state.values[0],.001)
        recovered=center(.4,1,0.,(0.,0.,0.),weights,motion=state.values,motion_phase=state.phases)
        self.assertLess(math.dist(quiet,recovered),.01)

    def test_imported_audio_reacts_to_rises_and_holds_sustained_midrange(self):
        state=MusicalMotion();model=Instrument()
        state.external=[.8,.6,.2];state.update(model,1/60)
        self.assertGreater(state.values[0],.9)
        for _ in range(120):state.update(model,1/60)
        self.assertLess(state.values[0],.001)  # no invented kicks on a constant tone
        self.assertGreater(state.values[1],.50)
        state.external=[0.,0.,0.]
        for _ in range(240):state.update(model,1/60)
        self.assertLess(max(state.values),.001)

    def test_sustained_music_articulates_each_original_without_overgrowing(self):
        motion=(.7,.8,.6,.8)
        for shape in range(10):
            weights=[float(i==shape) for i in range(10)]
            positions=[];differences=[]
            for theta in (.2,.9,1.7,2.5,3.8,5.1):
                a=center(theta,1,0.,(0.,0.,0.),weights,motion=motion,motion_phase=(.3,.2))
                b=center(theta,1,0.,(0.,0.,0.),weights,motion=motion,motion_phase=(2.2,1.8))
                differences.append(math.dist(a,b));positions.extend((a,b))
            self.assertGreater(sum(differences)/len(differences),.12,shape)
            self.assertTrue(all(math.isfinite(v) and abs(v)<4 for p in positions for v in p))

    def test_pause_freezes_geometry_phase_and_silent_deck_cannot_trigger_it(self):
        state=MusicalMotion();model=Instrument()
        state.note(1,gain=0.);state.update(model,.1)
        self.assertEqual(state.values,(0.,0.,0.,0.))
        state.note(0);state.update(model,.1)
        before=(state.values,state.phases)
        model.paused=True
        for _ in range(30):state.update(model,.1)
        self.assertEqual((state.values,state.phases),before)
        state.reset();self.assertEqual(state.values,(0.,0.,0.,0.))

