#!/usr/bin/env python3
"""Independent float PPP with conservative post-gap convergence screening."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from pyproj import Transformer
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.analyze_gnss import read_solution

ROOT=Path(__file__).resolve().parents[1]


def ecef_to_enu_rotation(longitude,latitude):
    lon,lat=np.deg2rad([longitude,latitude])
    return np.array([[-np.sin(lon),np.cos(lon),0],
                     [-np.sin(lat)*np.cos(lon),-np.sin(lat)*np.sin(lon),np.cos(lat)],
                     [np.cos(lat)*np.cos(lon),np.cos(lat)*np.sin(lon),np.sin(lat)]])


def main():
    validation=json.loads((ROOT/'results/tables/gnss_rinex_validation.json').read_text())
    fig,axes=plt.subplots(3,1,figsize=(10,7),sharex=True,constrained_layout=True)
    summaries=[]
    quake=pd.Timestamp('2018-06-26T09:15:32.299Z')
    zero=pd.Timestamp('2018-06-26T00:00Z')
    for item in validation:
        station=item['station'];name=station.lower()
        # The RTKLIB XYZ layout has the same column positions as its ENU layout.
        frame=read_solution(ROOT/f'results/catalogs/{name}_ppp.pos')
        frame=frame.rename(columns=dict(east_m='x_m',north_m='y_m',up_m='z_m',
                                      sd_east_m='sd_x_m',sd_north_m='sd_y_m',sd_up_m='sd_z_m'))
        if frame.empty or frame.time_utc.duplicated().any():
            raise ValueError('Missing or duplicate PPP epochs')
        xyz=np.array(item['approx_xyz_m'])
        lon,lat,_=Transformer.from_crs(4978,4979,always_xy=True).transform(*xyz)
        rotation=ecef_to_enu_rotation(lon,lat)
        enu=(frame[['x_m','y_m','z_m']].to_numpy()-xyz)@rotation.T
        for i,component in enumerate(['east_m','north_m','up_m']):frame[component]=enu[:,i]
        starts=frame.time_utc.diff().dt.total_seconds().fillna(9999)>300
        segment=starts.cumsum()
        elapsed=(frame.time_utc-frame.groupby(segment).time_utc.transform('min')).dt.total_seconds()
        screen=(frame.quality==6)&(frame.satellites>=5)&(elapsed>=3600)
        frame['screened_usable']=screen
        frame['post_gap_elapsed_s']=elapsed
        good=frame.loc[screen].copy()
        if good.empty:raise ValueError('No converged PPP epochs')
        components=['east_m','north_m','up_m']
        datum=good[(good.time_utc>=pd.Timestamp('2018-06-26T01:00Z'))&
                   (good.time_utc<pd.Timestamp('2018-06-26T02:00Z'))][components].mean()
        if datum.isna().any():raise ValueError('Missing PPP reference window')
        for component in components:frame[component.replace('_m','_change_m')]=frame[component]-datum[component]
        frame.to_csv(ROOT/f'results/catalogs/{name}_ppp.csv',index=False)
        summary=dict(station=station,solution_epochs=len(frame),ppp_quality_epochs=int((frame.quality==6).sum()),
                     screened_epochs=int(screen.sum()),screen='Q=6, >=5 satellites, >=1 hour after gap >300 s',
                     reference_utc=['2018-06-26T01:00Z','2018-06-26T02:00Z'])
        for label,time in [('fault_earthquake',quake),('intrusion',pd.Timestamp('2018-06-26T17:00Z')),
                           ('eruption',pd.Timestamp('2018-06-26T19:40Z'))]:
            a=good[(good.time_utc>=time-pd.Timedelta('1h'))&(good.time_utc<time)]
            b=good[(good.time_utc>=time)&(good.time_utc<time+pd.Timedelta('1h'))]
            summary[label]=dict(before_epochs=len(a),after_epochs=len(b),
                                mean_difference_m=(b[components].mean()-a[components].mean()).to_dict() if len(a) and len(b) else None,
                                before_std_m=a[components].std().to_dict() if len(a)>1 else None,
                                after_std_m=b[components].std().to_dict() if len(b)>1 else None)
        summaries.append(summary)
        hours=(frame.time_utc-zero).dt.total_seconds()/3600
        for ax,component in zip(axes,components):
            ax.scatter(hours[screen],frame.loc[screen,component.replace('_m','_change_m')],s=3,label=station)
            ax.set_ylabel(component.replace('_m','')+' change (m)');ax.grid(alpha=.2)
    for ax in axes:
        for time in (9.25,17,19+40/60):ax.axvline(time,color='k',lw=.7,ls='--')
        ax.set_xlim(0,24)
    axes[0].legend(markerscale=3)
    axes[0].set_title('Independent RTKLIB float PPP; datum 01:00–02:00 UTC')
    axes[-1].set_xlabel('26 June 2018 hour UTC')
    for ext in ('pdf','png'):fig.savefig(ROOT/f'results/figures/gnss_independent_ppp.{ext}',dpi=300)
    plt.close(fig)
    record=dict(method='RTKLIB 2.4.2 forward GPS-only float PPP',stations=summaries,
                products='ESA reprocessed final SP3 and 30-second clocks; IGS20 ANTEX',
                limitations=['Not original GIPSY-OASIS PPP','Saastamoinen estimated ZTD rather than VMF1',
                             'Solid Earth tides only; no FES2004 ocean loading','Independent conservative convergence screening',
                             'Daily orbit endpoints and antenna-calibration version may differ',
                             'Window differences include evolving deformation; no instantaneous step fit'])
    (ROOT/'results/tables/gnss_ppp_analysis.json').write_text(json.dumps(record,indent=2,allow_nan=False)+'\n')
    # Compare both methods in the base station's ENU frame, at common epochs.
    base=pd.read_csv(ROOT/'results/catalogs/gv03_ppp.csv')
    rover=pd.read_csv(ROOT/'results/catalogs/gv09_ppp.csv')
    baseline=pd.read_csv(ROOT/'results/catalogs/gv09_relative_gv03.csv')
    common=base[base.screened_usable].merge(rover[rover.screened_usable],on='time_utc',suffixes=('_base','_rover'))
    common=common.merge(baseline[baseline.quality==1],on='time_utc')
    xyz=np.array(validation[0]['approx_xyz_m'])
    lon,lat,_=Transformer.from_crs(4978,4979,always_xy=True).transform(*xyz)
    delta=common[[c+'_rover' for c in ['x_m','y_m','z_m']]].to_numpy()-common[[c+'_base' for c in ['x_m','y_m','z_m']]].to_numpy()
    ppp_baseline=delta@ecef_to_enu_rotation(lon,lat).T
    differences=ppp_baseline-common[['east_m','north_m','up_m']].to_numpy()
    times=pd.to_datetime(common.time_utc,utc=True)
    datum=(times>=pd.Timestamp('2018-06-26T01:00Z'))&(times<pd.Timestamp('2018-06-26T01:30Z'))
    offset=np.mean(differences[datum],axis=0)
    residual=differences-offset
    crosscheck=dict(common_screened_fixed_epochs=len(common),datum_epochs=int(datum.sum()),
                    residual_rmse_m=dict(zip(['east','north','up'],np.sqrt(np.mean(residual**2,axis=0)))),
                    residual_median_absolute_m=dict(zip(['east','north','up'],np.median(np.abs(residual),axis=0))),
                    note='PPP baseline and relative solution differences after common datum; shared input errors are correlated')
    (ROOT/'results/tables/gnss_method_crosscheck.json').write_text(json.dumps(crosscheck,indent=2,allow_nan=False)+'\n')
    print(json.dumps(record,indent=2,allow_nan=False))


if __name__ == '__main__':main()
