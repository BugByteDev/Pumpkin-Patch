import unittest
from carving import smooth_stroke,mirrored_cuts

class CarvingTests(unittest.TestCase):
    def test_mirror_is_exact_reflection(self):
        p=[[-.8,.2],[-.7,.4],[-.5,.1]];left,right=mirrored_cuts(p,True)
        self.assertEqual(right,[[-x,y] for x,y in reversed(left)])
    def test_stabilization_does_not_expand_stroke(self):
        p=[[-.7,.2],[-.6,.4],[-.5,.39],[-.4,.1],[-.6,.09]];result=smooth_stroke(p,.9)
        self.assertGreater(len(result),len(p))
        self.assertTrue(all(-.7<=x<=-.4 and .09<=y<=.4 for x,y in result))
    def test_zero_stabilization_keeps_points(self):
        p=[[0,0],[.2,.4],[.4,0],[.1,-.3]];self.assertEqual(smooth_stroke(p,0),p)
    def test_long_strokes_are_bounded(self):
        import math
        p=[[.3*math.cos(i/100),.3*math.sin(i/100)] for i in range(1000)]
        self.assertLessEqual(len(smooth_stroke(p,.95)),900)

    def test_center_and_shoulders_use_the_actual_pumpkin_hull(self):
        from carving import face_hit
        from library import LIBRARY
        for body in LIBRARY['bodies']:
            with self.subTest(body=body['id']):
                hit=face_hit([0,body['sy'],5],[0,0,-1],body)
                self.assertIsNotNone(hit);self.assertAlmostEqual(hit[0],0,places=5);self.assertAlmostEqual(hit[1],0,places=5)
                self.assertIsNotNone(face_hit([body['sx']*.70,body['sy'],5],[0,0,-1],body))
        self.assertIsNotNone(face_hit([LIBRARY['bodies'][0]['sx']*1.03,LIBRARY['bodies'][0]['sy'],5],[0,0,-1],LIBRARY['bodies'][0]))
        self.assertIsNone(face_hit([8,8,5],[0,0,-1],LIBRARY['bodies'][0]))

    def test_small_center_cuts_are_accepted(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        from library import default_design
        from native import Patch
        owner=SimpleNamespace(d=default_design(),view=SimpleNamespace(mirror=False),cut_groups=[],remember=Mock(),changed=Mock(),status=Mock())
        Patch.add_cut(owner,[[0,0],[.03,0],[0,.03]])
        self.assertEqual(len(owner.d['cuts']),1)
