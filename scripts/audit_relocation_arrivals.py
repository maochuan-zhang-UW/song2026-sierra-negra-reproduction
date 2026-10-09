#!/usr/bin/env python3
"""Compare fixed assigned arrival residuals before/after diagnostic relocation.

Use the association FMM model for both predictions. This tests consistency
with the initial model, not independent location accuracy or HypoDD's layered
forward model. No picks are reassigned or discarded based on residual size.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from pyproj import Geod
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from src.data_processing.travel_times import load_travel_times

ROOT = Path(__file__).resolve().parents[1]


def main():
    catalog = pd.read_csv(ROOT/'results/catalogs/hypodd_ct_keep_audit.csv').set_index('idx')
    picks = pd.read_csv(ROOT/'results/catalogs/nine_station_pick_assignments.csv')
    stations = pd.read_csv(ROOT/'results/tables/acquired_station_metadata.csv').set_index('station')
    travel = load_travel_times(ROOT/'.cache/approximate_tt.bin')
    geod = Geod(ellps='WGS84')
    # Compare identical observations only where both positions are inside the
    # FMM interpolation domain. Preserve excluded observations in the CSV.
    rows = picks.merge(catalog, left_on='event_idx', right_index=True, validate='many_to_one').reset_index(drop=True)
    rows['station_code'] = rows.station.str.split('.').str[1]
    for label, lat, lon, depth, origin in [
        ('initial', 'latitude', 'longitude', 'depth', 'origin_time_utc'),
        ('relocated', 'relocated_latitude', 'relocated_longitude', 'relocated_depth_km', 'relocated_origin_time_utc')]:
        rows[label+'_residual_s'] = np.nan
        origins = pd.to_datetime(rows[origin], utc=True, format='ISO8601').map(lambda t: t.timestamp() if pd.notna(t) else np.nan).to_numpy()
        for (station, phase), group in rows.groupby(['station_code', 'phase']):
            metadata = stations.loc[station]
            distance = geod.inv(group[lon].to_numpy(), group[lat].to_numpy(),
                                np.full(len(group), metadata.longitude),
                                np.full(len(group), metadata.latitude))[2]/1000
            points = np.column_stack([distance, group[depth]])
            grid = travel[phase].grid
            valid = np.isfinite(points).all(axis=1)
            for axis in range(2):
                valid &= (points[:,axis]>=grid[axis][0]) & (points[:,axis]<=grid[axis][-1])
            selected = group.index[valid]
            speed = {'P':4.29, 'S':2.38}[phase]
            predicted = origins[selected] + travel[phase](points[valid]) + metadata.elevation_m/1000/speed
            rows.loc[selected,label+'_residual_s'] = rows.loc[selected,'time_x'].to_numpy()-predicted
    if not np.allclose(rows.initial_residual_s, rows.residual, atol=1e-4, rtol=0):
        raise ValueError('Initial arrival predictions disagree with stored association residuals')
    rows['paired_prediction'] = rows[['initial_residual_s','relocated_residual_s']].notna().all(axis=1)
    rows[['event_idx','pick_idx','station','phase','paired_prediction','initial_residual_s','relocated_residual_s']].to_csv(
        ROOT/'results/tables/relocation_absolute_arrival_residuals.csv',index=False)
    paired = rows[rows.paired_prediction]
    summaries = []
    for phase in ['all','P','S']:
        subset = paired if phase=='all' else paired[paired.phase==phase]
        for label in ['initial','relocated']:
            residual = subset[label+'_residual_s'].to_numpy()
            summaries.append(dict(phase=phase,position=label,observations=len(residual),events=subset.event_idx.nunique(),
                rms_s=float(np.sqrt(np.mean(residual**2))),median_absolute_residual_s=float(np.median(abs(residual))),
                fraction_within_0_5_s=float(np.mean(abs(residual)<=.5))))
    summary = pd.DataFrame(summaries)
    summary.to_csv(ROOT/'results/tables/relocation_absolute_arrival_summary.csv',index=False)
    record = dict(assigned_observations=len(rows),paired_observations=len(paired),excluded_observations=int((~rows.paired_prediction).sum()),
        initial_residual_maximum_check_difference_s=float(np.max(abs(rows.initial_residual_s-rows.residual))),
        method='Fixed original assigned picks; initial and IAQ=0 positions predicted with association FMM and identical elevation correction',
        limitations=['Fitted observations, not held-out validation','FMM interpolation differs from HypoDD piecewise-constant layers',
                     'Interpolation-domain exclusions are recorded, not extrapolated','No candidate locations scientifically accepted'])
    (ROOT/'results/tables/relocation_absolute_arrival_execution.json').write_text(json.dumps(record,indent=2)+'\n')
    fig, axes = plt.subplots(1,2,figsize=(9,4),layout='constrained')
    for ax,phase in zip(axes,['P','S']):
        subset=paired[paired.phase==phase]
        for label in ['initial','relocated']:
            values=np.sort(abs(subset[label+'_residual_s'].to_numpy()))
            ax.plot(values,np.arange(1,len(values)+1)/len(values),label=label)
        ax.set(xlabel='Absolute assigned-arrival residual (s)',ylabel='Cumulative fraction',title=phase+' arrivals',xscale='log')
        ax.legend()
    for ext in ['pdf','png']:fig.savefig(ROOT/f'results/figures/relocation_absolute_arrivals.{ext}',dpi=300)
    plt.close(fig)
    print(summary.to_string(index=False))


if __name__=='__main__':main()
