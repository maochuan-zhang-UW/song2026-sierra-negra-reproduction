import unittest
import numpy as np
from scripts.analyze_gnss_change import bend_fit
class GNSSBend(unittest.TestCase):
    def test_known_continuous_deformation_bend(self):
        time=np.arange(14,19,1/60)
        position=3+.02*(time-14)+.4*np.maximum(time-17,0)
        fit,coef=bend_fit(time,position,14,19)
        self.assertAlmostEqual(fit['bend_utc_hour'],17,places=8)
        self.assertAlmostEqual(fit['pre_slope_m_per_hour'],.02,places=8)
        self.assertAlmostEqual(fit['post_slope_m_per_hour'],.42,places=8)
