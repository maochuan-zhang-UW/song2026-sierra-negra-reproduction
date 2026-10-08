"""Synthetic tests verify numerics; they are never Sierra Negra observations."""
import unittest
import numpy as np
from scipy.stats import linregress
from src.earthquake_classification.frequency import frequency_index,classify,event_frequency_index
from src.template_matching.matching import rolling_ncc,pair_ncc,detection_peaks
from src.multiplet_clustering.families import connected_families,network_similarity
from src.statistical_analysis.statistics import seismic_moment,recurrence,regression,moment_recurrence_pairs,coseismic_displacement
from src.data_processing.waveforms import preprocess,arrival_window


class Numerics(unittest.TestCase):
    def test_fft_against_direct(self):
        rng=np.random.RandomState(731)
        data=rng.normal(size=1000)+30; template=rng.normal(size=51)
        actual=rolling_ncc(data,template)
        expected=[np.corrcoef(data[i:i+51],template)[0,1] for i in range(950)]
        np.testing.assert_allclose(actual,expected,atol=1e-11)

    def test_injection_and_polarity(self):
        rng=np.random.RandomState(2);template=rng.normal(size=80)
        data=rng.normal(scale=.01,size=1000);data[230:310]=template;data[700:780]=-template
        score=rolling_ncc(data,template)
        self.assertAlmostEqual(score[230],1);self.assertAlmostEqual(score[700],-1)
        self.assertEqual(list(detection_peaks(score,.95,100,'absolute')),[230,700])
        self.assertTrue(np.isnan(rolling_ncc(np.zeros(200),template)).all())

    def test_cpp_against_numpy(self):
        rng=np.random.RandomState(22);a=rng.normal(size=100);b=rng.normal(size=100)
        values=[]
        for lag in range(-5,6):
            start=max(0,-lag);end=min(100,100-lag)
            values.append((np.corrcoef(a[start:end],b[start+lag:end+lag])[0,1],lag))
        expected=max(values,key=lambda p:abs(p[0]))
        actual=pair_ncc(a,b,5)
        self.assertAlmostEqual(expected[0],actual[0]);self.assertEqual(expected[1],actual[1])
        self.assertAlmostEqual(pair_ncc(a,-a,0)[0],-1)
        self.assertTrue(np.isnan(pair_ncc(np.ones(100),a,0)[0]))

    def test_frequency_amplitude_not_power(self):
        fs=100;n=500;f=np.fft.rfftfreq(n,1/fs)
        spectrum=np.zeros(len(f),dtype=complex)
        spectrum[(f>=2)&(f<=5)]=4
        spectrum[(f>=9)&(f<=15)]=1
        waveform=np.fft.irfft(spectrum,n=n)
        self.assertAlmostEqual(frequency_index(waveform,fs),-2,places=12)
        self.assertEqual(classify(-2),'VT');self.assertEqual(classify(-2.01),'LP')
        self.assertEqual(classify(float('nan')),'unclassified')
        self.assertEqual(event_frequency_index([-3,1],[2,1]),-3)

    def test_transitive_components_and_anti(self):
        families,anti=connected_families(['a','b','c','d'],[('a','b',.8),('b','c',.8),('c','d',-.9)],3)
        self.assertEqual(families,[['a','b','c']]);self.assertEqual(len(anti),1)
        self.assertEqual(connected_families(['a','b'],[('a','b',.7)],2)[0],[])
        self.assertEqual(network_similarity({'a':np.arange(10)},{'b':np.arange(10)},0)[1],0)

    def test_moment_conversion_boundary(self):
        ml=np.array([0,3,4]);mw=np.array([1,3,4])
        np.testing.assert_allclose(seismic_moment(ml),10**(1.5*mw+9.105))
        np.testing.assert_allclose(seismic_moment([1])-0,10**(np.array([11.605])))

    def test_recurrence_and_pairing(self):
        tr,p=recurrence([0,1,3,6]);np.testing.assert_array_equal(tr,[1,2,3])
        self.assertAlmostEqual(p,2/np.std([1,2,3]))
        x,y=moment_recurrence_pairs([3,0,1],[2,0,1],'preceding')
        np.testing.assert_array_equal(x,[1,2]);np.testing.assert_allclose(y,seismic_moment([1,2]))
        with self.assertRaises(ValueError):recurrence([0,0,2])

    def test_regression_and_jackknife(self):
        x=np.arange(1,11,dtype=float);y=x*3+4
        fit=regression(x,y,'linear')
        self.assertAlmostEqual(fit['slope'],3);self.assertAlmostEqual(fit['r_squared'],1)
        self.assertAlmostEqual(fit['jackknife_slope_se'],0)
        fit=regression(x,x**2,'log10');self.assertAlmostEqual(fit['slope'],2)

    def test_windows_and_gnss(self):
        self.assertEqual(len(arrival_window(np.zeros(1000),100,200)),500)
        with self.assertRaises(ValueError):arrival_window(np.zeros(100),100,10)
        with self.assertRaises(ValueError):preprocess(np.zeros(1000),100,None,None)
        self.assertEqual(coseismic_displacement([-100,0,100],[2,999,5],0),3)
        with self.assertRaises(ValueError):rolling_ncc([0,np.nan,2,3],[0,1,2])


if __name__=='__main__':unittest.main()
