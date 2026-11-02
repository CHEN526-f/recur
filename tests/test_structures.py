import math
import unittest
from recur.model import Instrument,NAMES,KEYS,FORM_COUNT
from recur.structures import center


class StructureTests(unittest.TestCase):
    def test_six_keys_and_ten_shapes_are_preserved(self):
        self.assertEqual(NAMES[:6],('PORTAL','FAN','BLOOM','CRYSTAL','ORBIT','TIDE'))
        self.assertEqual(KEYS,('A','S','D','J','K','L'))
        self.assertEqual(FORM_COUNT,10)

    def test_original_construction_positions_are_restored(self):
        fixtures=((2,0,(.35,0.,0.)),(3,1,(-1.7,-.825,0.)),
                  (4,0,(1.02,0.,0.)),(5,1,(-1.9,0.,.42*math.sin(.6))))
        for shape,band,expected in fixtures:
            weights=[float(i==shape) for i in range(FORM_COUNT)]
            actual=center(0.,band,0.,(0.,0.,0.),weights)
            for a,b in zip(actual,expected):self.assertAlmostEqual(a,b,places=6)

    def test_a_is_a_nested_portal_with_separate_radii_and_depth(self):
        weights=[1.]+[0.]*9
        for theta in (0.,.4,1.8,3.9):
            points=[center(theta,band,2.5,(0.,0.,0.),weights) for band in range(9)]
            radii=[math.hypot(p[0],p[1]) for p in points]
            self.assertGreater(min(b-a for a,b in zip(radii,radii[1:])),.07)
            self.assertGreater(max(p[2] for p in points)-min(p[2] for p in points),.95)

    def test_tide_remains_open_ended(self):
        for shape in (5,):
            weights=[float(i==shape) for i in range(FORM_COUNT)]
            a=center(0.,1,2.,(0.,0.,0.),weights)
            b=center(215/216*math.tau,1,2.,(0.,0.,0.),weights)
            self.assertGreater(math.dist(a,b),3.7)

    def test_s_has_three_separate_fans_instead_of_one_strip(self):
        weights=[0.,1.]+[0.]*8
        roots=[center(j/216*math.tau,1,0.,(0.,0.,0.),weights) for j in (0,72,144)]
        self.assertGreater(min(math.dist(roots[i],roots[(i+1)%3]) for i in range(3)),1.)
        for coordinate in (0,1):self.assertAlmostEqual(sum(p[coordinate] for p in roots),0.,places=6)

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
