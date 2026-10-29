import math
import unittest
import numpy as np
from recur.model import Instrument
from recur.motion import MusicalMotion
from recur.morphology import Morphogenesis,position


class MorphogenesisTests(unittest.TestCase):
    def simulate(self,seconds=30,hz=60):
        model=Instrument();motion=MusicalMotion();state=Morphogenesis();snapshots=[]
        motion.detect_external=False;motion.external=[.75,.55,.60]
        for frame in range(seconds*hz):
            if frame%(hz//2)==0:motion.note(0,.85)
            model.advance(1/hz);motion.update(model,1/hz)
            state.update(model,motion,1/hz,selected=True)
            if frame%hz==0:
                snapshots.append(np.array([position(theta,band,state.shape,state.detail,state.phases)
                                           for band in (0,1,3,5) for theta in np.linspace(0,math.tau,24,endpoint=False)]))
        return model,motion,state,snapshots

    def test_one_construction_develops_without_any_preset_selection(self):
        model,motion,state,frames=self.simulate()
        self.assertEqual((model.target,model.target_b),(0,1))
        self.assertGreater(state.strength,.99)
        # Distance matrices change: this cannot be satisfied by rotating or zooming.
        a,b=frames[3],frames[11]
        distances_a=np.linalg.norm(a[:,None,:]-a[None,:,:],axis=-1)
        distances_b=np.linalg.norm(b[:,None,:]-b[None,:,:],axis=-1)
        distances_a/=distances_a.mean();distances_b/=distances_b.mean()
        self.assertGreater(float(np.mean(abs(distances_a-distances_b))),.18)
        self.assertGreater(float(np.mean(np.linalg.norm(a-b,axis=1))),.5)
        self.assertTrue(np.isfinite(frames).all())
        self.assertLess(float(np.abs(frames).max()),6.)

    def test_pause_freezes_and_manual_control_smoothly_returns_originals(self):
        model,motion,state,_=self.simulate(3)
        before=(state.shape.copy(),state.detail.copy(),state.phases.copy(),state.strength)
        model.paused=True;state.update(model,motion,.1,selected=True)
        self.assertEqual(before,(state.shape,state.detail,state.phases,state.strength))
        model.paused=False
        for _ in range(180):state.update(model,motion,1/60,selected=False)
        self.assertLess(state.strength,.00001)

    def test_quiet_audio_does_not_invent_continuous_movement(self):
        state=Morphogenesis();model=Instrument();motion=MusicalMotion()
        for _ in range(600):state.update(model,motion,1/60,selected=True)
        self.assertEqual(state.phases,[0.,0.])

    def test_open_arc_closes_into_a_spiral_with_large_internal_change(self):
        params=[.2,.6,.8,.6];details=[.5,.4,.5,.8]
        def points(curvature):
            params[0]=curvature
            return np.array([position(t,1,params,details,[2.,1.]) for t in np.linspace(0,math.tau,72,endpoint=False)])
        arc,spiral=points(.2),points(1.25)
        self.assertGreater(float(np.mean(np.linalg.norm(arc-spiral,axis=1))),1.)
        self.assertGreater(float(np.ptp(arc[:,0])),3.)
        self.assertGreater(float(np.ptp(spiral[:,1])),1.5)

    def test_fx_pad_steers_construction_instead_of_only_rotating_the_view(self):
        states=[]
        for fx in ((0.,0.),(1.,1.)):
            state=Morphogenesis();model=Instrument();model.fx=list(fx)
            motion=MusicalMotion();motion.values=(.4,.6,.3,.7);motion.levels=[.7,.6,.3]
            for _ in range(180):state.update(model,motion,1/60,selected=True)
            states.append(state)
        self.assertGreater(states[1].shape[0]-states[0].shape[0],.2)
        self.assertGreater(states[1].shape[3]-states[0].shape[3],.2)

