"""Song et al. Eq. 1: mean Fourier AMPLITUDES, not integrated power."""
import numpy as np


def frequency_index(window, sampling_rate, low=(2, 5), high=(9, 15)):
    x = np.asarray(window, dtype=float)
    if x.ndim != 1 or len(x) < 2 or not np.isfinite(x).all():
        raise ValueError('A finite one-dimensional waveform is required')
    if not 0 < low[0] < low[1] < high[0] < high[1] < sampling_rate/2:
        raise ValueError('Frequency bands must lie below Nyquist')
    f = np.fft.rfftfreq(len(x), 1/sampling_rate)
    a = np.abs(np.fft.rfft(x))
    bands = [a[(f >= b[0]) & (f <= b[1])] for b in (low, high)]
    if any(len(b) == 0 for b in bands):
        raise ValueError('No spectral bins in band')
    lo, hi = [b.mean() for b in bands]
    if lo <= 0 or hi <= 0:
        return float('nan')
    return float(np.log2(hi/lo))


def event_frequency_index(indices, snrs, minimum_snr=2):
    indices, snrs = np.asarray(indices), np.asarray(snrs)
    if indices.shape != snrs.shape:
        raise ValueError('Station FI and SNR arrays must match')
    keep = np.isfinite(indices) & np.isfinite(snrs) & (snrs >= minimum_snr)
    return float(indices[keep].mean()) if keep.any() else float('nan')


def classify(fi, threshold=-2):
    if not np.isfinite(fi):
        return 'unclassified'
    return 'LP' if fi < threshold else 'VT'
