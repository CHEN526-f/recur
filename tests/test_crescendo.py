import unittest

from recur.crescendo import Crescendo
from recur.model import Instrument


class CrescendoTests(unittest.TestCase):
    def advance(self, state, model, seconds, hz=60):
        for _ in range(round(seconds * hz)):
            state.update(model, 1. / hz)

    def test_single_high_note_leaves_space_but_phrase_fills_it(self):
        state = Crescendo(); model = Instrument()
        state.note(1)
        self.advance(state, model, .3)
        self.assertLess(state.amount, .07)
        for _ in range(6):
            state.note(1)
            self.advance(state, model, .18)
        self.assertGreater(state.amount, .70)

    def test_bass_and_silent_deck_do_not_open_space(self):
        state = Crescendo(); model = Instrument()
        for _ in range(20):
            state.note(0); state.note(1, gain=0.)
            self.advance(state, model, .1)
        self.assertEqual(state.amount, 0.)

    def test_release_sustains_then_returns_smoothly(self):
        state = Crescendo(); model = Instrument(cycle=1)
        state.drop(1.,model.weights)
        self.advance(state, model, 2.)
        self.assertGreater(state.amount, .98)
        previous = state.amount
        state.update(model, 1/60)
        self.assertLess(abs(state.amount - previous), .04)
        self.advance(state, model, 12.)
        self.assertLess(state.amount, .01)

    def test_pause_freezes_and_reset_recedes(self):
        state = Crescendo(); model = Instrument(cycle=1)
        state.drop(1.,model.weights)
        self.advance(state, model, 1.)
        before = (state.time, state.amount)
        model.paused = True
        self.advance(state, model, 4.)
        self.assertEqual((state.time, state.amount), before)
        model.paused = False; state.reset()
        self.advance(state, model, 5.)
        self.assertLess(state.amount, .02)

    def test_envelope_consistent_across_frame_rates(self):
        results = []
        for hz in (30, 60, 120):
            state = Crescendo(); model = Instrument(cycle=1)
            state.drop(1.,model.weights)
            self.advance(state, model, 3., hz)
            results.append(state.amount)
        self.assertLess(max(results) - min(results), .015)


if __name__ == '__main__':
    unittest.main()
