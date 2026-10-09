import unittest,tempfile,struct
from pathlib import Path
import numpy as np
from src.data_processing.travel_times import load_travel_times,nearest_pick
from scripts.validate_heldout_stations import availability

class HeldoutTravel(unittest.TestCase):
    def test_interpolation_units_and_truncation(self):
        x=np.arange(4)*.5;z=np.arange(3)*.5
        p=x[:,None]/4+z[None,:]/3;s=2*p
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'tt.bin'
            path.write_bytes(struct.pack('iid',4,3,.5)+np.stack([p,s]).tobytes())
            model=load_travel_times(path)
            self.assertAlmostEqual(model['P']([[.75,.25]])[0],.75/4+.25/3)
            self.assertAlmostEqual(model['S']([[.75,.25]])[0],2*(.75/4+.25/3))
            with self.assertRaises(ValueError):model['P']([[3,.25]])
            path.write_bytes(path.read_bytes()[:-8])
            with self.assertRaises(ValueError):load_travel_times(path)
    def test_nearest_pick_sign_and_missing_picks(self):
        np.testing.assert_allclose(nearest_pick([9,11,15],[10,14]),[1,-1,-1])
        self.assertTrue(np.isnan(nearest_pick([1,2],[])).all())
    def test_gaps_and_blind_edges(self):
        np.testing.assert_array_equal(availability(np.array([2,5,55,56,90,105,155,156]),[(0,60),(100,160)]),[False,True,True,False,False,True,True,False])
