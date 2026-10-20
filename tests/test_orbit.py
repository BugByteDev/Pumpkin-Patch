import unittest,math
import numpy as np
from renderer import orbit_drag,lookat,perspective

class OrbitTests(unittest.TestCase):
    def projected_front(self,yaw,pitch):
        eye=np.array([5.4*math.sin(yaw)*math.cos(pitch),1+5.4*math.sin(pitch),5.4*math.cos(yaw)*math.cos(pitch)],dtype=np.float32)
        q=perspective(34,1.4,.05,30)@lookat(eye,np.array([0,1,0],dtype=np.float32))@np.array([0,1,1,1],dtype=np.float32)
        return q[:2]/q[3]
    def test_horizontal_surface_follows_hand(self):
        yaw,pitch=orbit_drag(0,0,50,0,600)
        self.assertGreater(self.projected_front(yaw,pitch)[0],0)
    def test_vertical_surface_follows_hand(self):
        yaw,pitch=orbit_drag(0,0,0,50,600)
        self.assertLess(self.projected_front(yaw,pitch)[1],0)
    def test_does_not_flip_at_poles(self):
        yaw,pitch=orbit_drag(0,0,0,100000,600)
        self.assertLess(pitch,math.pi/2)
    def test_drag_and_reverse_return_to_start(self):
        yaw,pitch=orbit_drag(0,0,50,30,600);yaw,pitch=orbit_drag(yaw,pitch,-50,-30,600)
        self.assertAlmostEqual(yaw,0);self.assertAlmostEqual(pitch,0)
