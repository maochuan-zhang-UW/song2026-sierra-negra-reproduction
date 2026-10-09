#!/usr/bin/env python3
"""Analyze RTKLIB relative baseline; exclude single positions and stale bases."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]


def read_solution(path):
    columns = ['date','clock','east_m','north_m','up_m','quality','satellites',
               'sd_east_m','sd_north_m','sd_up_m','sd_en','sd_nu','sd_ue','age_s','ratio']
    frame = pd.read_csv(path,comment='%',sep=r'\s+',names=columns)
    frame['time_utc'] = pd.to_datetime(frame.date+' '+frame.clock,utc=True)
    return frame.drop(columns=['date','clock'])


def main():
    raw = read_solution(ROOT/'results/catalogs/gv09_relative_gv03.pos')
    epochs = pd.read_csv(ROOT/'results/tables/gv03_rinex_epochs.csv')
    shared = pd.to_datetime(epochs.time_utc,utc=True)
    usable = raw.time_utc.isin(shared) & (raw.age_s.abs()<.001) & raw.quality.isin([1,2])
    frame = raw.loc[usable].copy()
    fixed = frame[frame.quality==1].copy()
    quake = pd.Timestamp('2018-06-26T09:15:32.299Z')
    before = fixed[(fixed.time_utc>=quake-pd.Timedelta('1h'))&(fixed.time_utc<quake)]
    after = fixed[(fixed.time_utc>=quake)&(fixed.time_utc<quake+pd.Timedelta('1h'))]
    components = ['east_m','north_m','up_m']
    change = after[components].mean()-before[components].mean()
    # No observations span the fault earthquake: use a stated early-day datum.
    reference_window = fixed[(fixed.time_utc>=pd.Timestamp('2018-06-26T00:30Z')) &
                             (fixed.time_utc<pd.Timestamp('2018-06-26T01:30Z'))]
    if reference_window.empty:
        raise ValueError('No ambiguity-fixed epochs in reference window')
    reference = reference_window[components].mean()
    for component in components:
        frame[component.replace('_m','_change_m')] = frame[component]-reference[component]
    frame.to_csv(ROOT/'results/catalogs/gv09_relative_gv03.csv',index=False)
    intervals=[]
    for a,b in zip(shared[:-1],shared[1:]):
        if (b-a).total_seconds()>30.001:
            intervals.append(dict(start_utc=a.isoformat(),end_utc=b.isoformat(),spacing_s=(b-a).total_seconds()))
    summary = dict(method='RTKLIB 2.4.2 combined dual-frequency kinematic relative baseline',
                   rtklib_commit='71db0ffa0d9735697c6adfd06fdf766d0e5ce807',
                   rover='GV09',reference='GV03 (fixed computational reference; station may move)',
                   raw_solution_epochs=len(raw),valid_relative_epochs=len(frame),
                   ambiguity_fixed_epochs=len(fixed),ambiguity_float_epochs=int((frame.quality==2).sum()),
                   rejected_epochs=int((~usable).sum()),
                   earthquake_utc=quake.isoformat(),before_fixed_epochs=len(before),after_fixed_epochs=len(after),
                   nominal_epochs_per_hour=120,
                   mean_after_minus_before_relative_m=change.where(change.notna(),None).to_dict() if len(before) and len(after) else None,
                   coseismic_estimate_status='unavailable: GV03 gap contains both one-hour windows',
                   reference_window_utc=['2018-06-26T00:30Z','2018-06-26T01:30Z'],
                   reference_fixed_epochs=len(reference_window),
                   gv03_gaps=intervals,
                   limitations=['Relative motion only; both volcanic stations may move',
                                'Not original GIPSY PPP or absolute coseismic displacement',
                                'No precise orbit, clock, antenna calibration or tide products',
                                'GV03 gaps limit intrusion and eruption timing','VCH1 skipped by user'])
    for name, time in [('intrusion',pd.Timestamp('2018-06-26T17:00Z')),
                       ('eruption',pd.Timestamp('2018-06-26T19:40Z'))]:
        a=fixed[(fixed.time_utc>=time-pd.Timedelta('1h'))&(fixed.time_utc<time)]
        b=fixed[(fixed.time_utc>=time)&(fixed.time_utc<time+pd.Timedelta('1h'))]
        summary[name+'_hour_window_comparison']=dict(
            literature_boundary_utc=time.isoformat(),before_fixed_epochs=len(a),after_fixed_epochs=len(b),
            relative_mean_difference_m=(b[components].mean()-a[components].mean()).to_dict(),
            interpretation='descriptive average-window difference, not an instantaneous offset or inferred onset')
    (ROOT/'results/tables/gnss_relative_analysis.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    fig, axes = plt.subplots(4,1,figsize=(10,9),sharex=True,constrained_layout=True)
    zero=pd.Timestamp('2018-06-26T00:00:00Z')
    hours=(frame.time_utc-zero).dt.total_seconds()/3600
    for ax,component in zip(axes[:3],components):
        for q,label,color in [(1,'ambiguity fixed','tab:blue'),(2,'float','tab:orange')]:
            select=frame.quality==q
            ax.scatter(hours[select],frame.loc[select,component.replace('_m','_change_m')],s=3,label=label,color=color)
        ax.set_ylabel(component.replace('_m','')+' change (m)')
        ax.grid(alpha=.2)
    axes[0].legend(loc='best',markerscale=3)
    for station in ('gv03','gv09'):
        e=pd.read_csv(ROOT/f'results/tables/{station}_rinex_epochs.csv')
        t=pd.to_datetime(e.time_utc,utc=True)
        axes[3].scatter((t-zero).dt.total_seconds()/3600,np.full(len(t),station.upper()),s=2)
    axes[3].set_ylabel('RINEX coverage');axes[3].set_xlabel('26 June 2018 hour UTC')
    for ax in axes:
        for time,label in [(9.25,'fault EQ'),(17,'intrusion'),(19+40/60,'eruption')]:
            ax.axvline(time,color='k',lw=.7,ls='--')
        ax.set_xlim(0,24)
    axes[0].set_title('Independent GV09–GV03 relative baseline; datum 00:30–01:30 UTC')
    for extension in ('pdf','png'):
        fig.savefig(ROOT/f'results/figures/gnss_relative_baseline.{extension}',dpi=300)
    plt.close(fig)
    print(json.dumps(summary,indent=2))


if __name__ == '__main__':
    main()
