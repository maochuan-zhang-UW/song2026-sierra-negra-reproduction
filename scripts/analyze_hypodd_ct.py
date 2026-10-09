#!/usr/bin/env python3
"""Audit actual HypoDD outputs; numerical completion is not physical validation."""
import argparse,hashlib,json,re
from pathlib import Path
import numpy as np
import pandas as pd
from pyproj import Geod
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--keep-shallow-events',action='store_true');args=parser.parse_args()
    suffix='_keep' if args.keep_shallow_events else ''
    folder=ROOT/f'.cache/hypodd_ct{suffix}'
    log=(folder/'hypoDD.log').read_text(errors='replace')
    if 'Program hypoDD finished' not in log:raise RuntimeError('Incomplete run')
    raw=np.loadtxt(folder/'hypoDD.reloc',ndmin=2)
    if raw.shape[1]!=24 or not np.isfinite(raw).all():raise ValueError('Unexpected nonfinite HypoDD output')
    ids=raw[:,0].astype(int)-1
    if len(set(ids))!=len(ids):raise ValueError('Duplicate event IDs')
    original=pd.read_csv(ROOT/'results/catalogs/nine_station_associated_events.csv').set_index('idx')
    if not set(ids)<=set(original.index):raise ValueError('Unknown event IDs')
    relocated=pd.DataFrame({'idx':ids,'relocated_latitude':raw[:,1],'relocated_longitude':raw[:,2],'relocated_depth_km':raw[:,3],
        'formal_x_error_m':raw[:,7],'formal_y_error_m':raw[:,8],'formal_z_error_m':raw[:,9],
        'P_differential_observations':raw[:,19].astype(int),'S_differential_observations':raw[:,20].astype(int),
        'catalog_differential_rms_s':raw[:,22],'cluster':raw[:,23].astype(int)}).set_index('idx')
    times=[]
    for row in raw:
        base=pd.Timestamp(year=int(row[10]),month=int(row[11]),day=int(row[12]),hour=int(row[13]),minute=int(row[14]),tz='UTC')
        times.append(base+pd.to_timedelta(row[15],unit='s'))
    relocated['relocated_origin_time_utc']=times
    for column in ['formal_x_error_m','formal_y_error_m','formal_z_error_m']:
        relocated.loc[relocated[column]<0,column]=np.nan
    joined=original.join(relocated)
    joined['retained']=joined.relocated_depth_km.notna()
    retained=joined[joined.retained].copy()
    distance=Geod(ellps='WGS84').inv(retained.longitude.to_numpy(),retained.latitude.to_numpy(),retained.relocated_longitude.to_numpy(),retained.relocated_latitude.to_numpy())[2]/1000
    joined.loc[retained.index,'horizontal_shift_km']=distance
    joined['depth_shift_km']=joined.relocated_depth_km-joined.depth
    joined['within_initial_domain']=joined.retained & joined.relocated_latitude.between(-.90,-.76) & joined.relocated_longitude.between(-91.22,-91.08) & joined.relocated_depth_km.between(0,30)
    # Never present formal LSQR errors as original bootstrap uncertainty.
    joined['scientifically_accepted']=False
    joined.to_csv(ROOT/f'results/catalogs/hypodd_ct{suffix}_audit.csv')
    record=dict(completed=True,scientifically_accepted=False,input_events=len(original),retained_events=len(raw),not_retained_events=len(original)-len(raw),
        retained_within_initial_domain=int(joined.within_initial_domain.sum()),clusters=relocated.cluster.value_counts().sort_index().to_dict(),
        median_horizontal_shift_km=float(np.median(distance)),maximum_horizontal_shift_km=float(max(distance)),
        median_absolute_depth_shift_km=float(np.median(abs(retained.relocated_depth_km-retained.depth))),
        depth_range_km=[float(raw[:,3].min()),float(raw[:,3].max())],
        zero_depth_warnings=len(re.findall('Warning: negative depth',log)),
        policy='retain event, freeze negative depth update' if args.keep_shallow_events else 'remove negative-depth event',
        reason=('Boundary-sensitive CT-only pilot; native zero-depth step freezing; not validated as original relocation' if args.keep_shallow_events else 'CT-only pilot with alternative velocity layering and settings; substantial location drift; not accepted as paper reproduction'),
        output_sha256=hashlib.sha256((folder/'hypoDD.reloc').read_bytes()).hexdigest(),
        note='Domain flag is diagnostic, not independent truth. -9 metadata omitted; formal LSQR errors are not bootstrap confidence intervals.')
    (ROOT/f'results/tables/hypodd_ct{suffix}_execution.json').write_text(json.dumps(record,indent=2)+'\n')
    fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
    axes[0].scatter(original.longitude,original.latitude,s=6,label='Input candidates')
    axes[0].scatter(raw[:,2],raw[:,1],s=8,label='Pilot retained',alpha=.6)
    axes[0].set(xlabel='Longitude (degrees)',ylabel='Latitude (degrees)',title=f'Unaccepted CT-only pilot: {len(raw)}/{len(original)} retained');axes[0].legend(fontsize=8)
    axes[1].scatter(retained.depth,retained.relocated_depth_km,s=8,alpha=.5)
    axes[1].plot([0,30],[0,30],'k--',linewidth=1)
    axes[1].set(xlabel='Input depth below sea level (km)',ylabel='Pilot depth below sea level (km)',title='Depth drift; source zero-depth boundary')
    for ext in ['png','pdf']:fig.savefig(ROOT/f'results/figures/hypodd_ct{suffix}_audit.{ext}',dpi=300)
    plt.close(fig);print(json.dumps(record,indent=2))
if __name__=='__main__':main()
