"""FFT matched filtering via compiled SciPy, C++ event-pair correlations."""
import ctypes
from pathlib import Path
import numpy as np
from scipy.signal import correlate, find_peaks


def rolling_ncc(data, template):
    x, t = np.asarray(data,dtype=float), np.asarray(template,dtype=float)
    if x.ndim != 1 or t.ndim != 1 or len(t)<3 or len(x)<len(t):
        raise ValueError('Invalid continuous data or template shape')
    if not np.isfinite(x).all() or not np.isfinite(t).all():
        raise ValueError('Gaps must be processed as separate segments')
    # Constant offsets cancel analytically, but remove the global mean for stability.
    x = x-x.mean(); t = t-t.mean(); n=len(t)
    if np.dot(t,t)==0:
        raise ValueError('Constant template')
    sums=np.r_[0,np.cumsum(x)]; squares=np.r_[0,np.cumsum(x*x)]
    s=sums[n:]-sums[:-n]; q=squares[n:]-squares[:-n]
    energy=np.maximum(q-s*s/n,0)
    denominator=np.sqrt(energy*np.dot(t,t))
    numerator=correlate(x,t,mode='valid',method='fft')
    out=np.full(len(numerator),np.nan)
    np.divide(numerator,denominator,out=out,where=denominator>0)
    return np.clip(out,-1,1)


def detection_peaks(score, threshold, minimum_gap_samples, threshold_type):
    if threshold is None or threshold_type not in ('absolute','MAD'):
        raise ValueError('Published threshold unavailable; choose and label sensitivity run')
    if minimum_gap_samples < 1 or threshold <= 0:
        raise ValueError('Positive detection threshold and separation required')
    score=np.asarray(score,dtype=float)
    if not np.isfinite(score).any():
        return np.array([],dtype=int)
    cutoff=threshold if threshold_type=='absolute' else threshold*np.nanmedian(np.abs(score))
    values=np.where(np.isfinite(score),np.abs(score),-np.inf)
    # Padding makes detections at segment endpoints eligible.
    indices,_=find_peaks(np.r_[-np.inf,values,-np.inf],height=cutoff,distance=minimum_gap_samples)
    return indices-1


def pair_ncc(a,b,maximum_lag_samples):
    a,b=np.ascontiguousarray(a,dtype=np.float64),np.ascontiguousarray(b,dtype=np.float64)
    if a.ndim!=1 or a.shape!=b.shape or len(a)<3 or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Finite equal-length waveform vectors required')
    if not 0 <= maximum_lag_samples <= len(a)-3:
        raise ValueError('Invalid lag limit')
    path=Path(__file__).resolve().parents[2]/'.cache/libcorrelation.so'
    lib=ctypes.CDLL(str(path))
    fun=lib.best_ncc
    pointer=ctypes.POINTER(ctypes.c_double)
    fun.argtypes=[pointer,pointer,ctypes.c_int,ctypes.c_int,ctypes.POINTER(ctypes.c_int)]
    fun.restype=ctypes.c_double
    lag=ctypes.c_int()
    r=fun(a.ctypes.data_as(pointer),b.ctypes.data_as(pointer),len(a),maximum_lag_samples,ctypes.byref(lag))
    return r,lag.value
