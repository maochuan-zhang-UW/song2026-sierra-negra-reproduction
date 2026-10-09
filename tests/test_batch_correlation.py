import unittest
import numpy as np
from src.template_matching.matching import pairwise_ncc,pair_ncc


class BatchCorrelation(unittest.TestCase):
    def test_signed_matrix_and_lags(self):
        a=np.random.default_rng(12).normal(size=250)
        rows=np.array([a,-a,np.roll(a,3),np.ones(250)])
        for lag in [0,10]:
            matrix=pairwise_ncc(rows,lag)
            self.assertAlmostEqual(matrix[0,1],-1)
            np.testing.assert_allclose(matrix,matrix.T,equal_nan=True)
            for i in range(4):
                for j in range(i+1,4):
                    expected,_=pair_ncc(rows[i],rows[j],lag)
                    if np.isnan(expected):self.assertTrue(np.isnan(matrix[i,j]))
                    else:self.assertAlmostEqual(matrix[i,j],expected)
