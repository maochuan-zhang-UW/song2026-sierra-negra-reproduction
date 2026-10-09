"""Reuse one continuous-data FFT across a batch of finite equal-length templates."""
import numpy as np
from scipy.fft import rfft,irfft,next_fast_len


def correlation_context(data,length):
    x=np.asarray(data,dtype=float)
    if x.ndim!=1 or len(x)<length or not np.isfinite(x).all():raise ValueError('Finite contiguous data required')
    x=x-x.mean();nfft=next_fast_len(len(x)+length-1)
    sums=np.r_[0.,np.cumsum(x)];squares=np.r_[0.,np.cumsum(x*x)]
    mean_sum=sums[length:]-sums[:-length]
    energy=np.maximum(squares[length:]-squares[:-length]-mean_sum**2/length,0)
    return dict(spectrum=rfft(x,n=nfft),nfft=nfft,length=length,energy=energy)


def correlate_templates(context,templates):
    templates=np.asarray(templates,dtype=float)
    if templates.ndim!=2 or templates.shape[1]!=context['length'] or not np.isfinite(templates).all():
        raise ValueError('Finite equal-length template rows required')
    centered=templates-templates.mean(axis=1,keepdims=True)
    numerator=irfft(rfft(centered[:,::-1],n=context['nfft'],axis=1)*context['spectrum'],
                    n=context['nfft'],axis=1)
    length=context['length'];numerator=numerator[:,length-1:length-1+len(context['energy'])]
    denominator=np.sqrt((centered**2).sum(axis=1)[:,None]*context['energy'])
    output=np.full_like(numerator,np.nan)
    np.divide(numerator,denominator,out=output,where=denominator>0)
    return np.clip(output,-1,1)
