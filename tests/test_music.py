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

    def test_automatic_evolution_can_be_disabled_without_changing_audio(self):
        track=MusicTrack();track._position=8.;track.running=True
        track.set_auto(False);self.assertFalse(track.auto)
        track.set_auto(True);self.assertTrue(track.auto)
        self.assertEqual(track._position,8.)
        self.assertTrue(track.playing)

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
