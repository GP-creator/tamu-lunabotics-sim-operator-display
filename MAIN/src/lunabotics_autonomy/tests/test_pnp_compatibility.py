import sys
import types
import unittest
from unittest.mock import patch
import numpy as np
from autonomy.fiducials import estimate_camera_tag,tag_object_corners


class PnpCompatibilityTests(unittest.TestCase):
    def fake_cv(self,errors=(70.,0.),depth=1.):
        module=types.ModuleType('cv2');module.SOLVEPNP_IPPE_SQUARE=7;module.SOLVEPNP_ITERATIVE=0
        module.error=RuntimeError;module.flags=[]
        def solve(*args,flags):
            module.flags.append(flags);module.current=flags
            return True,np.zeros((3,1)),np.array([[0.],[0.],[depth]])
        module.solvePnP=solve
        module.projectPoints=lambda *args:(np.full((4,1,2),errors[0 if module.current==7 else 1]),None)
        module.Rodrigues=lambda *args:(np.eye(3),None)
        return module

    def estimate(self,cv,max_error=3.):
        with patch.dict(sys.modules,{'cv2':cv}):
            return estimate_camera_tag(tag_object_corners(.2),np.zeros((4,2)),np.eye(3),np.zeros(5),max_error)

    def test_bad_square_solution_can_use_valid_iterative_solution(self):
        cv=self.fake_cv();error,transform=self.estimate(cv)
        self.assertEqual(cv.flags,[7,0]);self.assertEqual(error,0.)
        self.assertEqual(transform[2,3],1.)

    def test_high_error_or_behind_camera_solutions_still_reject(self):
        self.assertIsNone(self.estimate(self.fake_cv(errors=(70.,71.))))
        self.assertIsNone(self.estimate(self.fake_cv(depth=-1.)))

    def test_invalid_quality_limit_rejected(self):
        for value in (0.,float('nan'),float('inf')):
            with self.assertRaises(ValueError):self.estimate(self.fake_cv(),value)
