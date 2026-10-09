import unittest
import numpy as np
from obspy import Stream,Trace,UTCDateTime
from scripts.pick_ec_waveforms import common_segments


class CommonSegments(unittest.TestCase):
 def test_common_segments_preserve_gaps(self):
    stream=Stream()
    for component in 'ZNE':
        spans=[(0,90),(120,210)] if component=='N' else [(0,210)]
        for start,end in spans:
            trace=Trace(np.ones((end-start)*100),header={'station':'TEST','network':'XX','channel':'HH'+component,'sampling_rate':100,'starttime':UTCDateTime(0)+start})
            stream.append(trace)
    segments=common_segments(stream)
    self.assertEqual(len(segments),2)
    self.assertEqual([(float(s[0].stats.starttime),s[0].stats.npts) for s in segments],[(0,9000),(120,9000)])
    self.assertTrue(all(len(s)==3 and all(np.isfinite(t.data).all() for t in s) for s in segments))
