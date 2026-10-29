import unittest
import numpy as np
from recur.model import Instrument
from recur.motion import MusicalMotion
from recur.morphology import Morphogenesis


class MorphogenesisTests(unittest.TestCase):
    def simulate(self,seconds=30,hz=60):
        model=Instrument();motion=MusicalMotion();state=Morphogenesis();snapshots=[]
        motion.detect_external=False;motion.external=[.75,.55,.60]
        for frame in range(seconds*hz):
            if frame%(hz//2)==0:motion.note(0,.85)
            model.advance(1/hz);motion.update(model,1/hz)
            state.update(model,motion,1/hz,selected=True)
            if frame%hz==0:
                state.organism.build(state,motion,.4)
                snapshots.append(state.organism.centers[[0,1,3,5],::9].reshape(-1,3).copy())
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
        self.assertLess(float(np.abs(frames).max()),9.)

    def test_pause_freezes_and_manual_control_smoothly_returns_originals(self):
        model,motion,state,_=self.simulate(3)
        before=(state.shape.copy(),state.detail.copy(),state.phases.copy(),state.strength)
        roots=state.organism.roots.copy();children=state.organism.children.copy()
        model.paused=True;state.update(model,motion,.1,selected=True)
        self.assertEqual(before,(state.shape,state.detail,state.phases,state.strength))
        np.testing.assert_array_equal(state.organism.roots,roots)
        np.testing.assert_array_equal(state.organism.children,children)
        model.paused=False
        for _ in range(180):state.update(model,motion,1/60,selected=False)
        self.assertLess(state.strength,.00001)

    def test_quiet_audio_does_not_invent_continuous_movement(self):
        state=Morphogenesis();model=Instrument();motion=MusicalMotion()
        for _ in range(600):state.update(model,motion,1/60,selected=True)
        self.assertEqual(state.phases,[0.,0.])

    def test_child_hinge_changes_its_fan_without_rigidly_moving_other_fans(self):
        state=Morphogenesis();motion=MusicalMotion();network=state.organism
        network.build(state,motion,0.);before=network.centers.copy()
        network.children[7]=(.8,.9,-.6,.8)
        network.build(state,motion,0.);after=network.centers
        delta=np.linalg.norm(after-before,axis=-1)
        self.assertGreater(float(delta[:,84:96].max()),.08)
        np.testing.assert_array_equal(delta[:,:84],0.)
        np.testing.assert_array_equal(delta[:,96:],0.)

    def test_real_render_pose_contains_valid_local_frames_and_varied_joints(self):
        _,motion,state,_=self.simulate(15)
        pose=state.organism.build(state,motion,.6)
        self.assertEqual(pose.shape,(36,216,4))
        self.assertEqual(pose.dtype,np.dtype('f4'))
        self.assertTrue(pose.flags.c_contiguous)
        self.assertTrue(np.isfinite(pose).all())
        frames=state.organism.frames
        unit=frames/np.linalg.norm(frames,axis=-2,keepdims=True)
        product=np.einsum('...ji,...jk->...ik',unit,unit)
        np.testing.assert_allclose(product,np.broadcast_to(np.eye(3),product.shape),atol=1e-5)
        self.assertGreater(float(np.ptp(state.organism.roots[:,1])),.5)
        self.assertGreater(float(np.ptp(state.organism.children[:,2])),.5)

    def test_voice_history_changes_branches_at_matching_current_loudness(self):
        roots=[]
        for voice in (0,3):
            state=Morphogenesis();model=Instrument();motion=MusicalMotion()
            motion.values=(.3,.5,.4,.7);motion.levels=[.6,.5,.4]
            for frame in range(360):
                if frame%30==0:motion.voice_totals[voice]+=.8
                state.update(model,motion,1/60,selected=True)
            roots.append(state.organism.roots.copy())
        self.assertGreater(float(np.max(abs(roots[0]-roots[1]))),.015)

    def test_drum_attack_changes_internal_geometry_immediately(self):
        state=Morphogenesis();motion=MusicalMotion();network=state.organism
        network.build(state,motion,0.);before=network.centers[0,::6].copy()
        normals=network.frames[...,0].copy()
        motion.values=(.9,0.,0.,.9)
        network.build(state,motion,0.);after=network.centers[0,::6]
        def distances(points):
            matrix=np.linalg.norm(points[:,None]-points[None,:],axis=-1)
            return matrix/matrix.mean()
        # Normalized distances exclude a simple global scale/rotation response.
        self.assertGreater(float(np.abs(distances(after)-distances(before)).mean()),.01)
        current=network.frames[...,0]
        dots=np.sum(normals*current,axis=-1)/(np.linalg.norm(normals,axis=-1)*np.linalg.norm(current,axis=-1))
        self.assertGreater(float(np.arccos(np.clip(dots,-1.,1.)).mean()),.25)

    def test_fx_pad_steers_construction_instead_of_only_rotating_the_view(self):
        states=[]
        for fx in ((0.,0.),(1.,1.)):
            state=Morphogenesis();model=Instrument();model.fx=list(fx)
            motion=MusicalMotion();motion.values=(.4,.6,.3,.7);motion.levels=[.7,.6,.3]
            for _ in range(180):state.update(model,motion,1/60,selected=True)
            states.append(state)
        self.assertGreater(states[1].shape[0]-states[0].shape[0],.2)
        self.assertGreater(states[1].shape[3]-states[0].shape[3],.2)

