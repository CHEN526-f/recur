import math
import unittest
from recur.model import Instrument,NAMES,KEYS,FORM_COUNT
from recur.structures import center


class StructureTests(unittest.TestCase):
    def test_original_six_names_and_keys_are_preserved(self):
        self.assertEqual(NAMES[:6],('SERPENT','RIBBON','BLOOM','CRYSTAL','ORBIT','TIDE'))
        self.assertEqual(KEYS,('A','S','D','J','K','L'))
        self.assertEqual(FORM_COUNT,10)

    def test_original_construction_positions_are_restored(self):
        fixtures=((0,1,(1.62,0.,0.)),(1,1,(-1.925,0.,.22)),
                  (2,0,(.35,0.,0.)),(3,1,(-1.7,-.825,0.)),
                  (4,0,(1.02,0.,0.)),(5,1,(-1.9,0.,.42*math.sin(.6))))
        for shape,band,expected in fixtures:
            weights=[float(i==shape) for i in range(FORM_COUNT)]
            actual=center(0.,band,0.,(0.,0.,0.),weights)
            for a,b in zip(actual,expected):self.assertAlmostEqual(a,b,places=6)

    def test_ribbon_and_tide_remain_open_ended(self):
        for shape in (1,5):
            weights=[float(i==shape) for i in range(FORM_COUNT)]
            a=center(0.,1,2.,(0.,0.,0.),weights)
            b=center(215/216*math.tau,1,2.,(0.,0.,0.),weights)
            self.assertGreater(math.dist(a,b),3.7)

    def test_only_the_added_radial_forms_require_paired_symmetry(self):
        for shape in range(6,FORM_COUNT):
            weights=[float(i==shape) for i in range(FORM_COUNT)]
            for theta in (.1,.7,1.9):
                p=center(theta,1,2.7,(.6,.4,.7),weights,.8)
                q=center(theta+math.pi,1,2.7,(.6,.4,.7),weights,.8)
                self.assertAlmostEqual(p[0],-q[0],places=6)
                self.assertAlmostEqual(p[1],-q[1],places=6)

    def test_extra_form_can_play_and_record_without_replacing_itself(self):
        model=Instrument(recording=True)
        model.select_shape(8);model.trigger(2,'FORM')
        for _ in range(120):model.advance(1/60)
        self.assertEqual(model.target,8)
        self.assertAlmostEqual(model.weights[8],1.)
        self.assertEqual(len(model.loop),6)
        self.assertTrue(any(model.loop[2]))
