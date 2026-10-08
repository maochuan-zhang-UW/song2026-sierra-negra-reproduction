"""Explicit preprocessing choices; no guessed published filter settings."""
import numpy as np
from scipy.signal import butter, sosfilt, sosfiltfilt, detrend, resample_poly
from fractions import Fraction


def preprocess(data, sampling_rate, order, zero_phase, target_rate=None, band=(2,20)):
    x = np.asarray(data, dtype=float)
    if x.ndim != 1 or not np.isfinite(x).all():
        raise ValueError('Process contiguous finite segments; never fill gaps silently')
    if order is None or zero_phase is None:
        raise ValueError('Filter order and phase convention must be explicit')
    if not 0 < band[0] < band[1] < sampling_rate/2:
        raise ValueError('Invalid passband')
    x = detrend(x, type='linear')
    sos = butter(order, band, btype='bandpass', fs=sampling_rate, output='sos')
    x = sosfiltfilt(sos,x) if zero_phase else sosfilt(sos,x)
    if target_rate is not None and target_rate != sampling_rate:
        if target_rate <= 2*band[1]:
            raise ValueError('Target rate must exceed twice upper passband')
        ratio = Fraction(str(target_rate))/Fraction(str(sampling_rate))
        x = resample_poly(x, ratio.numerator, ratio.denominator)
    return x


def arrival_window(data, sampling_rate, arrival_sample, prepick=1, duration=5):
    start = int(round(arrival_sample-prepick*sampling_rate))
    end = start+int(round(duration*sampling_rate))
    if start < 0 or end > len(data):
        raise ValueError('Incomplete arrival window')
    return np.asarray(data)[start:end]


def velocity_stream(stream, inventory, pre_filt):
    """ObsPy response removal; caller must specify stabilization frequencies."""
    out = stream.copy()
    out.detrend('linear')
    out.remove_response(inventory=inventory, output='VEL', pre_filt=pre_filt)
    return out
