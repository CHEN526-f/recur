import json
import os
import unittest
from unittest.mock import patch
from pathlib import Path
import tempfile

os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
from recur.model import Instrument
from app import restore_session


class InteractionTests(unittest.TestCase):
    def test_morph_is_smooth_normalized_and_converges(self):
        m=Instrument();m.trigger(4)
        self.assertEqual(m.morph[0],1.)
        for _ in range(180):m.advance(1/60)
        self.assertAlmostEqual(sum(m.morph),1.,places=6)
        self.assertGreater(m.morph[4],.999)

    def test_record_quantizes_and_loop_does_not_rerecord(self):
        m=Instrument(recording=True,deck_times=[.3,0.])
        m.trigger(2)
        self.assertTrue(m.loop[2][2])
        m.trigger(4,'LOOP')
        self.assertFalse(any(m.loop[4]))

    def test_loop_fires_once_at_boundary(self):
        m=Instrument(bpm=120,playing=True)
        m.loop[0][1]=True
        self.assertEqual(m.advance(.124),[])
        self.assertEqual(m.advance(.002),[0])
        self.assertEqual(m.advance(.001),[])

    def test_grid_audition_neither_changes_shape_nor_overdubs_another_cell(self):
        m=Instrument(recording=True)
        m.trigger(1,'GRID')
        self.assertEqual(m.target,0)
        self.assertFalse(any(m.loop[1]))

    def test_hold_and_release(self):
        m=Instrument(holding=True)
        for _ in range(120):m.advance(1/60)
        self.assertLess(m.brake,.06)
        self.assertGreater(m.release(),.97)
        self.assertEqual(m.cycle,1)
        self.assertFalse(m.holding)

    def test_pause_and_reset_preserve_composition(self):
        m=Instrument(paused=True,recording=True)
        m.loop[1][5]=True;m.advance(.1)
        self.assertEqual(m.clock,0)
        m.reset()
        self.assertTrue(m.loop[1][5])

    def test_corrupt_restore_is_atomic(self):
        import types
        m=Instrument();r=types.SimpleNamespace(palette=0)
        with tempfile.TemporaryDirectory() as folder:
            Path(folder,'latest-session.json').write_text(json.dumps({'loop':[[True]*16]*6,'bpm':999}))
            with patch('app.CAPTURES',Path(folder)):
                with self.assertRaises(ValueError):restore_session(m,r)
        self.assertFalse(any(map(any,m.loop)))

    def test_valid_restore(self):
        import types
        m=Instrument();r=types.SimpleNamespace(palette=0)
        loop=[[False]*16 for _ in range(6)];loop[3][2]=True
        with tempfile.TemporaryDirectory() as folder:
            Path(folder,'latest-session.json').write_text(json.dumps({'loop':loop,'bpm':92,'target':2,'palette':1}))
            with patch('app.CAPTURES',Path(folder)):restore_session(m,r)
        self.assertTrue(m.loop[3][2]);self.assertEqual(m.bpm,92);self.assertEqual(r.palette,1)

if __name__=='__main__':unittest.main()
