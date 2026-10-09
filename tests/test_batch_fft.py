import unittest
import numpy as np
from src.template_matching.batch_fft import correlation_context,correlate_templates
from src.template_matching.matching import rolling_ncc


class BatchFFT(unittest.TestCase):
    def test_direct_reference_and_boundary_injection(self):
        rng=np.random.default_rng(23)
        templates=rng.normal(size=(3,250));data=rng.normal(size=3000)
        data[:250]=templates[0];data[-250:]=-templates[1]
        scores=correlate_templates(correlation_context(data,250),templates)
        for i in range(3):np.testing.assert_allclose(scores[i],rolling_ncc(data,templates[i]),atol=1e-12)
        self.assertAlmostEqual(scores[0,0],1)
        self.assertAlmostEqual(scores[1,-1],-1)
