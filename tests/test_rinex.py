import tempfile
import unittest
from pathlib import Path
from src.data_processing.rinex import read_observations
from scripts.analyze_gnss import read_solution
from scripts.analyze_gnss_ppp import ecef_to_enu_rotation
import numpy as np


class RinexTest(unittest.TestCase):
    def test_utc_and_missing_phase(self):
        def header(body,label):
            return body.ljust(60)+label+'\n'
        text=header('     2.11           OBSERVATION DATA    G','RINEX VERSION / TYPE')
        text+=header('     4    L1    L2    C1    P2','# / TYPES OF OBSERV')
        text+=header('    18','LEAP SECONDS')
        text+=header('  2018     6    26     0     0    0.0000000     GPS','TIME OF FIRST OBS')
        text+=header('','END OF HEADER')
        text+=' 18  6 26  0  0  0.0000000  0  1G01\n'
        text+=f'{123.0:14.3f}1 '+' '*16+f'{20000000.0:14.3f}  {20000010.0:14.3f}  '+'\n'
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'test.obs';p.write_text(text)
            metadata,frame=read_observations(p)
        self.assertEqual(frame.time_utc.iloc[0].isoformat(),'2018-06-25T23:59:42+00:00')
        self.assertTrue(frame.L2.isna().iloc[0])
        self.assertEqual(frame.L1_lli.iloc[0],1)

    def test_quality_codes_preserved(self):
        text='% UTC solution\n2018/06/26 17:00:12.000 1 2 3 5 9 1 1 1 0 0 0 60 0\n'
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'test.pos';p.write_text(text)
            frame=read_solution(p)
        self.assertEqual(frame.quality.iloc[0],5)
        self.assertEqual(frame.age_s.iloc[0],60)
        self.assertEqual(frame.time_utc.iloc[0].hour,17)

    def test_geodetic_axis_convention(self):
        # At longitude/latitude zero, ECEF x is up, y east and z north.
        rotation=ecef_to_enu_rotation(0,0)
        np.testing.assert_allclose(rotation @ np.array([1.,2.,3.]),[2.,3.,1.])
        np.testing.assert_allclose(rotation @ rotation.T,np.eye(3),atol=1e-15)
