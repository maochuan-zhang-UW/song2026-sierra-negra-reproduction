"""SI moment conversion and explicitly chosen recurrence/regression conventions."""
import numpy as np
from scipy.stats import linregress


def seismic_moment(local_magnitude):
    ml=np.asarray(local_magnitude,dtype=float)
    mw=np.where(ml>3,ml,2*ml/3+1)
    return 10**(1.5*mw+9.105)


def recurrence(times_seconds,ddof=0):
    times=np.sort(np.asarray(times_seconds,dtype=float))
    if len(times)<3 or not np.isfinite(times).all():
        raise ValueError('At least three finite event times required')
    intervals=np.diff(times)
    if np.any(intervals<=0):raise ValueError('Repeated origin times must be reviewed')
    sigma=intervals.std(ddof=ddof)
    return intervals, float(intervals.mean()/sigma) if sigma>0 else float('inf')


def moment_recurrence_pairs(times_seconds,magnitudes,pairing):
    order=np.argsort(times_seconds)
    times=np.asarray(times_seconds,dtype=float)[order]
    moment=seismic_moment(np.asarray(magnitudes)[order])
    intervals=np.diff(times)
    if pairing not in ('preceding','following') or np.any(intervals<=0):
        raise ValueError('Explicit pairing and distinct times required')
    return intervals,moment[1:] if pairing=='preceding' else moment[:-1]


def regression(x,y,transform):
    x,y=np.asarray(x,dtype=float),np.asarray(y,dtype=float)
    if x.shape!=y.shape or len(x)<4 or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError('At least four finite paired samples required')
    if transform=='log10':
        if np.any(x<=0) or np.any(y<=0):raise ValueError('Logarithms require positive values')
        x,y=np.log10(x),np.log10(y)
    elif transform!='linear':raise ValueError('Choose linear or log10 explicitly')
    if np.ptp(x)==0:raise ValueError('Constant predictor')
    fit=linregress(x,y)
    slopes=[]
    for i in range(len(x)):
        keep=np.arange(len(x))!=i
        if np.ptp(x[keep])==0:raise ValueError('Degenerate jackknife subset')
        slopes.append(linregress(x[keep],y[keep]).slope)
    slopes=np.asarray(slopes)
    se=np.sqrt((len(x)-1)/len(x)*np.sum((slopes-slopes.mean())**2))
    return dict(slope=float(fit.slope),intercept=float(fit.intercept),r_squared=float(fit.rvalue**2),
                p_value=float(fit.pvalue),jackknife_slope_se=float(se),transform=transform,n=len(x))


def coseismic_displacement(times_seconds,positions_m,event_time):
    t,p=np.asarray(times_seconds),np.asarray(positions_m,dtype=float)
    if len(t)!=len(p):raise ValueError('Time/position lengths differ')
    before=p[(t>=event_time-3600)&(t<event_time)]
    after=p[(t>event_time)&(t<=event_time+3600)]
    if not len(before) or not len(after):raise ValueError('Both one-hour windows required')
    return np.nanmean(after,axis=0)-np.nanmean(before,axis=0)
