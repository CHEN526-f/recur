import unittest
import numpy as np
from recur.model import Instrument
from recur.motion import MusicalMotion
from recur.morphology import Morphogenesis
from recur.vj import VJDirector


class MorphogenesisTests(unittest.TestCase):
    def simulate(self,seconds=30,voice=0):
        model=Instrument();motion=MusicalMotion();state=Morphogenesis();snapshots=[]
        motion.detect_external=False
        for frame in range(seconds*60):
            t=frame/60
            motion.external=[.55+.35*np.sin(t*.7)**2,.4+.4*np.sin(t*.31)**2,.3+.6*np.sin(t*.43)**2]
            if frame%30==0:motion.note(voice,.9)
            if frame%19==0:motion.note(3,.7)
            model.advance(1/60);motion.update(model,1/60)
            state.update(model,motion,1/60,selected=True)
            if frame%60==0:
                state.vj.build(state,motion,.4)
                snapshots.append(state.vj.centers[:,::12].reshape(-1,3).copy())
        return model,motion,state,snapshots

    def test_music_edits_compositions_without_cycling_manual_shape_ids(self):
        model,motion,state,frames=self.simulate()
        self.assertEqual((model.target,model.target_b),(0,1))
        self.assertGreater(state.strength,.99)
        self.assertGreaterEqual(len({cue[1] for cue in state.vj.history}),4)
        self.assertTrue(np.isfinite(frames).all())
        self.assertLess(float(np.abs(frames).max()),12.)

    def test_pause_freezes_direction_and_manual_returns_originals(self):
        model,motion,state,_=self.simulate(3)
        before=(state.vj.time,state.vj.beat,state.vj.blend,state.strength)
        model.paused=True;state.update(model,motion,.1,selected=True)
        self.assertEqual(before,(state.vj.time,state.vj.beat,state.vj.blend,state.strength))
        model.paused=False
        for _ in range(180):state.update(model,motion,1/60,selected=False)
        self.assertLess(state.strength,.00001)

    def test_silence_does_not_advance_or_change_composition(self):
        state=Morphogenesis();model=Instrument();motion=MusicalMotion()
        for _ in range(600):state.update(model,motion,1/60,selected=True)
        self.assertEqual(state.vj.time,0.)
        self.assertEqual(state.vj.edits,0)

    def test_no_measured_attacks_means_no_automatic_edits(self):
        model=Instrument();motion=MusicalMotion();vj=VJDirector()
        motion.external=[.7,.6,.6];motion.detect_external=False
        for frame in range(3600):
            motion.update(model,1/60);vj.update(model,motion,1/60)
            if frame<10:self.assertEqual(vj.blend,1.,'A stable first shot must not reassemble into itself')
        self.assertEqual(vj.edits,0)

    def test_all_generators_and_reassembly_frames_are_finite_orthogonal(self):
        motion=MusicalMotion();motion.values=(.8,.7,.6,.8);motion.levels=[.8,.7,.6]
        for family in range(6):
            for blend in (0.,.25,.5,.75,1.):
                vj=VJDirector();vj.target=family;vj.variant=family;vj.blend=blend;vj.time=7.
                pose=vj.build(None,motion,.6)
                self.assertEqual(pose.shape,(36,216,4))
                self.assertEqual(pose.dtype,np.dtype('f4'))
                self.assertTrue(pose.flags.c_contiguous and np.isfinite(pose).all())
                matrices=vj.frames
                unit=matrices/np.linalg.norm(matrices,axis=-2,keepdims=True)
                product=np.einsum('...ji,...jk->...ik',unit,unit)
                np.testing.assert_allclose(product,np.broadcast_to(np.eye(3),product.shape),atol=1e-5)
                self.assertGreater(float(np.linalg.det(unit).min()),.99)

    def test_layouts_differ_in_internal_distances_not_only_rotation(self):
        motion=MusicalMotion();motion.values=(.4,.7,.5,.8);motion.levels=[.7,.6,.6]
        matrices=[]
        for family in range(6):
            vj=VJDirector();vj.target=family;vj.variant=family;vj.time=4.
            vj.build(None,motion,.4)
            points=vj.centers[:,::18].reshape(-1,3)
            distances=np.linalg.norm(points[:,None]-points[None,:],axis=-1)
            matrices.append(distances/distances.mean())
        for first in range(6):
            for second in range(first):
                self.assertGreater(float(np.abs(matrices[first]-matrices[second]).mean()),.12)

    def test_voice_history_affects_compositional_decisions(self):
        _,_,first,_=self.simulate(30,0)
        _,_,second,_=self.simulate(30,5)
        self.assertNotEqual(first.vj.history,second.vj.history)

    def test_attack_articulates_current_layout_immediately(self):
        vj=VJDirector();vj.target=1;vj.time=4.;motion=MusicalMotion()
        vj.build(None,motion,0.);before=vj.centers.copy();normal=vj.frames[...,2].copy()
        motion.values=(.9,.4,.4,.9);vj.build(None,motion,0.)
        self.assertGreater(float(np.linalg.norm(vj.centers-before,axis=-1).mean()),.08)
        dots=np.sum(normal*vj.frames[...,2],axis=-1)/(np.linalg.norm(normal,axis=-1)*np.linalg.norm(vj.frames[...,2],axis=-1))
        self.assertGreater(float(np.arccos(np.clip(dots,-1,1)).mean()),.25)

    def test_fx_changes_spatial_arrangement(self):
        poses=[];motion=MusicalMotion()
        for fx in ((0.,0.),(1.,1.)):
            model=Instrument();model.fx=list(fx);vj=VJDirector()
            vj.update(model,motion,1/60);vj.time=4.;vj.build(None,motion,.4)
            poses.append(vj.centers.copy())
        self.assertGreater(float(np.linalg.norm(poses[1]-poses[0],axis=-1).mean()),.5)
