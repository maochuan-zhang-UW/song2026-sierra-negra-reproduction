"""Validate overlap averaging, blind edges and refusal of missing components."""
import unittest
try:
    import torch
    from obspy import Stream,Trace
    import numpy as np
    from src.earthquake_detection.volpick import annotate_contiguous
    AVAILABLE=True
except ImportError:
    AVAILABLE=False


@unittest.skipUnless(AVAILABLE,'Optional waveform environment required')
class Overlap(unittest.TestCase):
    def test_known_probabilities_and_edges(self):
        class Model:
            component_order='ZNE'
            in_samples=600
            phases='PS'
            def annotate_batch_pre(self,x,args):return x
            def __call__(self,x):return (x[:,0],2*x[:,0],3*x[:,0])
            def annotate_batch_post(self,x,piggyback,args):
                y=torch.stack(x,dim=-1)
                a,b=args['blinding'];y[:,:a]=float('nan');y[:,-b:]=float('nan')
                return y
        values=np.arange(950,dtype=np.float32)/1000
        stream=Stream([Trace(values.copy(),header=dict(network='XX',station='TEST',channel='HH'+c,sampling_rate=100)) for c in 'ZNE'])
        result=annotate_contiguous(Model(),stream,batch_size=2,overlap=300,blinding=(50,50))
        for factor,trace in enumerate(result,1):
            np.testing.assert_allclose(trace.data[50:-50],factor*values[50:-50],rtol=1e-6)
            self.assertTrue(np.isnan(trace.data[:50]).all())
            self.assertTrue(np.isnan(trace.data[-50:]).all())
        with self.assertRaises(ValueError):annotate_contiguous(Model(),stream[:2])
