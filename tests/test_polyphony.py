import unittest
import numpy as np
from pathlib import Path
import re
from recur.polyphony import PolyphonicStage,InputContacts,LIFETIMES
from recur.model import Instrument
from recur.motion import MusicalMotion
from recur.spatial import note_field,deformation


class PolyphonicTests(unittest.TestCase):
    def test_second_key_does_not_retarget_or_remove_first_animation(self):
        stage=PolyphonicStage();first=stage.note(0);stage.time=.3
        theta=np.linspace(0,6.28,216)
        before=note_field(first,stage.time,theta);snapshot=vars(first).copy()
        stage.note(1)
        self.assertIn(first,stage.notes)
        self.assertEqual(snapshot,vars(first))
        np.testing.assert_array_equal(note_field(first,stage.time,theta),before)

    def test_spectrum_changes_cannot_make_a_live_note_twitch(self):
        stage=PolyphonicStage();stage.note(3);stage.time=.4
        before=deformation(stage).copy();stage.levels=[1.,0.,1.]
        np.testing.assert_array_equal(deformation(stage),before)

    def test_three_fingers_and_keyboard_have_independent_contacts(self):
        contacts=InputContacts();calls=[]
        for token,voice in ((('finger',1),0),(('finger',2),1),(('finger',3),2),(('key',4),3)):
            self.assertTrue(contacts.down(token,voice,calls.append))
        self.assertEqual(calls,[0,1,2,3]);self.assertFalse(contacts.down(('key',4),3,calls.append))
        contacts.up(('finger',2))
        self.assertEqual(contacts.voices,{0,2,3})

    def test_all_six_keys_produce_different_geometry_and_finish_smoothly(self):
        shapes=[]
        for voice in range(6):
            stage=PolyphonicStage();note=stage.note(voice);stage.time=.3
            data=note_field(note,stage.time,np.linspace(0,6.28,216))
            self.assertTrue(np.isfinite(data).all())
            shapes.append(data.tobytes())
            self.assertEqual(note.envelope(note.born),0.)
            self.assertEqual(note.envelope(note.born+note.duration),0.)
            self.assertLess(note.envelope(note.born+note.duration-.01),.002)
        self.assertGreaterEqual(len(set(shapes)),5)

    def test_repeated_key_varies_captured_placement_and_construction(self):
        stage=PolyphonicStage();notes=[stage.note(0) for _ in range(5)]
        self.assertEqual(len({n.center for n in notes}),5)
        self.assertEqual(len({n.variant for n in notes}),5)
        for n in notes:
            self.assertLess(abs(n.center[0]),1.5)
            self.assertLess(abs(n.center[1]),.8)

    def test_overlay_stays_bounded_and_preserves_shared_layer_order(self):
        stage=PolyphonicStage()
        for _ in range(8):
            for voice in range(6):stage.note(voice)
        stage.time=.3
        field=deformation(stage).reshape(9,2,216,4)
        self.assertTrue(np.isfinite(field).all())
        for band in range(1,9):np.testing.assert_array_equal(field[band],field[0])
        self.assertLessEqual(float(abs(field[:,0,:,0]).max()),.201)
        self.assertLessEqual(float(abs(field[:,0,:,1]).max()),.121)
        self.assertLessEqual(float(abs(field[:,0,:,3]).max()),.821)
        self.assertGreater(float((1+field[:,1,:,0]).min()),.4)
        angular=field[0,0,:,1].astype(float)
        steps=2*np.pi/216+np.roll(angular,-1)-angular
        self.assertGreater(float(steps.min()),0.)

    def test_pause_freezes_tails_and_expiry_removes_only_finished_notes(self):
        stage=PolyphonicStage();model=Instrument();motion=MusicalMotion()
        first=stage.note(5);stage.time=.8;second=stage.note(4)
        model.paused=True;stage.update(model,motion,.1);self.assertEqual(stage.time,.8)
        model.paused=False
        for _ in range(6):stage.update(model,motion,.1)
        self.assertNotIn(first,stage.notes);self.assertIn(second,stage.notes)

    def test_live_simultaneous_same_voice_notes_are_not_debounced(self):
        stage=PolyphonicStage()
        first=stage.note(1,source='TOUCH');second=stage.note(1,source='TOUCH')
        self.assertIsNot(first,second);self.assertEqual(len(stage.notes),2)

    def test_music_rate_limit_never_cuts_a_previous_tail(self):
        stage=PolyphonicStage();first=stage.note(0,source='TRACK')
        for _ in range(100):stage.note(0,source='TRACK')
        self.assertEqual(stage.notes,[first])

    def test_touch_zone_edges_are_clamped(self):
        self.assertEqual(InputContacts.zone(0.,0.),0)
        self.assertEqual(InputContacts.zone(1.,1.),5)
        self.assertEqual(InputContacts.zone(.5,.2),1)

    def test_shipped_interface_is_english_except_project_title(self):
        root=Path(__file__).resolve().parents[1]
        paths=list((root/'recur').glob('*.py'))
        paths.extend(root/name for name in ('README.md','START_HERE.md','SUBMISSION.md','CREDITS.md','PROCESS.md'))
        paths.extend(p for p in (root/'web/dist').glob('*') if p.suffix in ('.js','.html','.css'))
        for path in paths:
            text=path.read_text(encoding='utf8').replace('环生','')
            self.assertIsNone(re.search('[\u4e00-\u9fff]',text),str(path))
