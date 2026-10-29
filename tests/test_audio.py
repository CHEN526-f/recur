import os
os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
import unittest
import numpy as np
import pygame
from recur.audio import Synth
from recur.model import Instrument


class AudioTests(unittest.TestCase):
    def test_all_patches_have_safe_nonzero_stereo_signal(self):
        synth=Synth()
        self.assertTrue(synth.enabled,synth.error)
        for index in range(6):
            data=synth.patch(index)
            self.assertEqual(data.ndim,2)
            self.assertEqual(data.shape[1],2)
            self.assertEqual(data.dtype,np.int16)
            self.assertGreater(float(np.std(data)),100)
            self.assertLessEqual(int(np.abs(data.astype(np.int32)).max()),11200)
        pygame.mixer.quit()

    def test_pitched_voices_have_different_fundamentals(self):
        synth=Synth()
        try:
            peaks=[]
            for note in (62,69):
                samples=synth.patch(1,note=note)[:22050,0].astype(float)
                spectrum=np.abs(np.fft.rfft(samples*np.hanning(len(samples))))
                frequency=np.fft.rfftfreq(len(samples),1/synth.RATE)
                peaks.append(frequency[spectrum.argmax()])
            self.assertAlmostEqual(peaks[0],293.665,delta=2.)
            self.assertAlmostEqual(peaks[1],440.,delta=2.)
            self.assertFalse(np.array_equal(synth.patch(5),synth.patch(5,variant='clap')))
        finally:pygame.mixer.quit()

    def test_mixer_keeps_velocity_and_separate_instrument_channels(self):
        synth=Synth()
        try:
            synth.play(0,velocity=.8)
            synth.play(1,note=62,velocity=.2)
            synth.play(1,note=69,velocity=.9)
            synth.update(Instrument())
            self.assertIsNotNone(synth.channels[0][0].get_sound())
            self.assertLess(synth.channels[0][2].get_volume(),.15)
            self.assertGreater(synth.channels[0][3].get_volume(),.40)
        finally:pygame.mixer.quit()

if __name__=='__main__':unittest.main()
