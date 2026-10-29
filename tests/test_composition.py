import unittest
from recur.composition import Performance,build_score,harmony,section


class CompositionTests(unittest.TestCase):
    def test_score_has_harmony_melody_backbeat_and_section_contrast(self):
        score=build_score()
        self.assertEqual({e.voice for e in score},set(range(6)))
        self.assertGreaterEqual(len({e.note for e in score if e.voice==1}),8)
        self.assertEqual(len({harmony(bar)[0] for bar in range(8)}),4)
        self.assertTrue(any(e.variant=='clap' and e.tick%16==4 for e in score))
        intro=sum(e.tick<4*16 for e in score)
        peak=sum(16*16<=e.tick<20*16 for e in score)
        self.assertGreater(peak,intro*2)
        self.assertEqual(section(0),'INTRO');self.assertEqual(section(31),'OUTRO')

    def test_scheduler_emits_each_event_once_and_finishes(self):
        player=Performance();player.start();played=[]
        for _ in range(5000):
            played.extend(player.advance(1/60,108))
            if player.done:break
        self.assertEqual(played,list(player.score))
        self.assertTrue(player.done);self.assertFalse(player.playing)
        self.assertEqual(player.advance(.1,108),[])

    def test_pause_and_brake_preserve_playhead(self):
        player=Performance();player.start();player.advance(.1,120)
        before=player.position
        self.assertEqual(player.advance(.1,120,paused=True),[])
        self.assertEqual(player.position,before)
        self.assertEqual(player.advance(.1,120,speed=0.),[])
        self.assertEqual(player.position,before)

    def test_live_notes_vary_and_follow_chord_and_octave(self):
        player=Performance()
        notes=[player.live(1,0).note for _ in range(8)]
        self.assertGreaterEqual(len(set(notes)),5)
        self.assertNotEqual(player.live(2,0).chord,player.live(2,8).chord)
        self.assertNotEqual(player.live(4,0).note,player.live(4,0).note)
        player=Performance();normal=player.live(1,0).note
        player=Performance();player.octave=1
        self.assertEqual(player.live(1,0).note,normal+12)

    def test_song_supports_manual_takeover_without_resetting_the_score(self):
        player=Performance();player.start();player.position=123.
        player.set_auto(False);self.assertFalse(player.auto)
        self.assertEqual(player.position,123.)
        player.set_auto(True);self.assertTrue(player.auto)
        self.assertEqual(player.position,123.)

    def test_expansion_follows_sections_and_breathes_inside_the_peak(self):
        player=Performance();player.start();values=[]
        for bar in (0,12,16,17,24,31.9):
            player.position=bar*16;values.append(player.expansion)
        self.assertLess(values[0],.2)
        self.assertGreater(values[2],values[1])
        self.assertGreater(abs(values[2]-values[3]),.2)
        self.assertLess(values[4],.3);self.assertLess(values[5],.1)
