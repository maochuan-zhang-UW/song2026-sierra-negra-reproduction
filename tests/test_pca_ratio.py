import unittest
import numpy as np
from scripts.estimate_matched_magnitudes import pca_ratio

class PCARatio(unittest.TestCase):
    def test_physical_scale_and_shift(self):
        rng=np.random.default_rng(14);x=rng.normal(size=250)
        self.assertAlmostEqual(pca_ratio(x,2.7*x+8,0),2.7,places=6)
        y=np.r_[rng.normal(size=3),.4*x[:-3]]
        self.assertAlmostEqual(pca_ratio(x,y,3),.4,places=6)
