import os
os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
from pathlib import Path
import tempfile
import unittest
import wave
import numpy as np
import pygame
from recur.music import MusicTrack,analyse


class MusicTests(unittest.TestCase):
    def test_measured_bands_distinguish_bass_mid_and_high(self):
        rate=22050;t=np.arange(rate*2)/rate
        for band,frequency in enumerate((90.,440.,4000.)):
            levels=analyse(.2*np.sin(t*2*np.pi*frequency),rate)
            middle=levels[15:45].mean(axis=0)
            self.assertGreater(middle[band],.85)
            for other in range(3):
                if other!=band:self.assertLess(middle[other],.15)

    def test_silence_does_not_create_a_false_climax(self):
        levels=analyse(np.zeros((44100,2),dtype=np.int16),44100)
        self.assertTrue(np.isfinite(levels).all())
        self.assertEqual(float(levels.max()),0.)

    def test_automatic_forms_respond_to_spectrum_and_wait_between_changes(self):
        track=MusicTrack()
        track.levels=np.tile([.9,.1,.05],(360,1)).astype(np.float32)
        self.assertIn(track.form(),(0,4,7))
        track._position=1.
        self.assertIsNone(track.form())
        track.levels[:]=[.08,.15,.95];track._position=4.
        self.assertIn(track.form(),(2,6,8))
        track.set_auto(False);track._position=8.
        self.assertIsNone(track.form())
        track.set_auto(True)
        self.assertIn(track.form(),(2,6,8))

    def test_automatic_forms_hold_during_silence(self):
        track=MusicTrack();track.levels=np.zeros((180,3),dtype=np.float32)
        self.assertIsNone(track.form())

    def test_local_playback_pause_and_failed_load_preserves_track(self):
        pygame.mixer.init(44100,-16,2,512)
        root=Path(__file__).resolve().parents[1]/'captures/test-tmp'
        root.mkdir(parents=True,exist_ok=True)
        try:
            with tempfile.TemporaryDirectory(dir=root) as folder:
                path=Path(folder)/'tone.wav'
                t=np.arange(44100*2)/44100
                pcm=np.column_stack([np.sin(t*2*np.pi*220)*6000]*2).astype('<i2')
                with wave.open(str(path),'wb') as out:
                    out.setnchannels(2);out.setsampwidth(2);out.setframerate(44100);out.writeframes(pcm.tobytes())
                track=MusicTrack();track.load(path)
                self.assertTrue(track.playing);self.assertAlmostEqual(track.duration,2.,places=2)
                with self.assertRaises(ValueError):track.load(Path(folder)/'missing.txt')
                self.assertEqual(track.path,path.resolve())
                self.assertEqual(len(track.sample()),3)
                track.pause(True);self.assertFalse(track.playing);self.assertEqual(track.sample(),[0.,0.,0.])
                track.pause(False);self.assertTrue(track.playing)
                track.close()
        finally:pygame.mixer.quit()
