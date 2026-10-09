#!/usr/bin/env python3
"""Independent continuous piecewise-linear GNSS bend sensitivity, not magma inversion."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]


def bend_fit(time,position,start,end):
    mask=(time>=start)&(time<end);t=time[mask];y=position[mask]
    if len(t)<60:raise ValueError('Insufficient GNSS window')
    candidates=np.arange(start+.5,end-.5+.0001,1/60)
    fits=[]
    for bend in candidates:
        matrix=np.column_stack([np.ones(len(t)),t-start,np.maximum(t-bend,0)])
        coefficients=np.linalg.lstsq(matrix,y,rcond=None)[0]
        fits.append((float(np.sum((y-matrix@coefficients)**2)),bend,coefficients))
    rss,bend,coef=min(fits,key=lambda row:row[0])
    return dict(bend_utc_hour=float(bend),pre_slope_m_per_hour=float(coef[1]),post_slope_m_per_hour=float(coef[1]+coef[2]),rss_m2=rss,minutes=len(t)),coef


def main():
    fig,axes=plt.subplots(3,1,figsize=(10,7),sharex=True);records=[];primary=[]
    for station in ('gv03','gv09'):
        frame=pd.read_csv(ROOT/f'results/catalogs/{station}_ppp.csv')
        frame=frame[frame.screened_usable].copy()
        frame['time_utc']=pd.to_datetime(frame.time_utc,utc=True)
        minute=frame.set_index('time_utc')[['east_change_m','north_change_m','up_change_m']].resample('1min').median().dropna()
        hour=np.asarray((minute.index-pd.Timestamp('2018-06-26',tz='UTC')).total_seconds()/3600)
        for number,component in enumerate(['east','north','up']):
            y=minute[component+'_change_m'].to_numpy()
            for start in (13.75,14.5,15):
                for end in (18,18.5,19.25):
                    fit,coef=bend_fit(hour,y,start,end)
                    records.append(dict(station=station,component=component,start_utc_hour=start,end_utc_hour=end,**fit))
                    if start==14.5 and end==19.25:
                        primary.append(records[-1]);mask=(hour>=start)&(hour<end)
                        axes[number].plot(hour[mask],y[mask],lw=.8,label=station.upper())
                        t=np.linspace(start,end,300)
                        prediction=coef[0]+coef[1]*(t-start)+coef[2]*np.maximum(t-fit['bend_utc_hour'],0)
                        line,=axes[number].plot(t,prediction,ls='--',lw=1)
                        axes[number].axvline(fit['bend_utc_hour'],color=line.get_color(),ls=':',lw=.8)
            axes[number].set_ylabel(component+' change (m)')
    for ax in axes:ax.axvline(17,color='black',lw=.7);ax.set_xlim(13.75,19.4)
    axes[0].legend();axes[0].set_title('Independent GNSS linear-bend fit; solid black line is published 17:00 timing')
    axes[-1].set_xlabel('26 June 2018 UTC hour');fig.tight_layout()
    for suffix in ('pdf','png'):fig.savefig(ROOT/f'results/figures/gnss_intrusion_bend.{suffix}',dpi=300,bbox_inches='tight')
    pd.DataFrame(records).to_csv(ROOT/'results/tables/gnss_bend_sensitivity.csv',index=False)
    record=dict(primary=primary,model='continuous piecewise-linear mean displacement; least squares bend at 1-minute grid; 1-minute median PPP',
                limitations=['Independent statistical bend, not inversion for intrusion onset','Postseismic curvature and evolving intrusion may bias fit',
                             'Window spread is sensitivity, not a confidence interval','PPP errors and serial correlation not modeled'])
    (ROOT/'results/tables/gnss_bend_execution.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))

if __name__=='__main__':main()
