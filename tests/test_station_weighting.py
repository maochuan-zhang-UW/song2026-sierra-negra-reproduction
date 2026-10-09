import unittest
import numpy as np
import pandas as pd
from scripts.analyze_candidate_families import network_matrix


class StationWeighting(unittest.TestCase):
    def test_equal_stations_and_missing_observations(self):
        rows=[];matrices={}
        for station,component,phase,score in [('A','Z','P',.9),('A','N','S',.9),('A','E','S',.9),('B','Z','P',-.9)]:
            matrices[f'{station}.{component}.{phase}']=np.array([[1,score],[score,1]])
            for event in (0,1):
                rows.append(dict(station=station,component=component,phase=phase,event_idx=event,snr=3))
        metadata=pd.DataFrame(rows)
        scores,count=network_matrix(matrices,metadata,[0,1],'snr')
        self.assertAlmostEqual(scores[0,1],0)
        self.assertEqual(count[0,1],2)
        metadata.loc[(metadata.station=='B')&(metadata.event_idx==1),'snr']=1
        scores,count=network_matrix(matrices,metadata,[0,1],'snr')
        self.assertAlmostEqual(scores[0,1],.9)
        self.assertEqual(count[0,1],1)
