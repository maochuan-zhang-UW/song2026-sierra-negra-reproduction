import unittest
import pandas as pd
from scripts.associate_approximate import unix_seconds


class AssociationTime(unittest.TestCase):
    def test_storage_units_do_not_change_physical_time(self):
        for unit in ('us','ns'):
            values=pd.Series(pd.to_datetime(['2018-06-26T00:00:00Z','2018-06-26T23:59:59Z'])).astype('datetime64['+unit+', UTC]')
            seconds=unix_seconds(values)
            self.assertAlmostEqual(seconds.iloc[0],1529971200)
            self.assertAlmostEqual(seconds.iloc[1]-seconds.iloc[0],86399)
