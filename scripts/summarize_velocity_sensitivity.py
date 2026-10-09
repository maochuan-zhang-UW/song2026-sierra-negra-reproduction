#!/usr/bin/env python3
"""Declared +/-5% uniform velocity perturbations; not confidence bounds."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from pyproj import Geod

ROOT=Path(__file__).resolve().parents[1]


def main():
    nominal=pd.read_csv(ROOT/'results/catalogs/approximate_associated_events.csv')
    records=[]
    for label in ('velocity_slow','velocity_fast'):
        alternative=pd.read_csv(ROOT/f'results/catalogs/{label}_associated_events.csv')
        settings=json.loads((ROOT/f'results/tables/{label}_association.json').read_text())
        distances=np.abs(nominal.time.to_numpy()[:,None]-alternative.time.to_numpy()[None,:])
        forward=distances.argmin(axis=1);reverse=distances.argmin(axis=0)
        indices=np.arange(len(nominal))
        keep=(reverse[forward]==indices)&(distances[indices,forward]<=2)
        a=nominal.iloc[indices[keep]];b=alternative.iloc[forward[keep]]
        _,_,distance=Geod(ellps='WGS84').inv(a.longitude.to_numpy(),a.latitude.to_numpy(),
                                         b.longitude.to_numpy(),b.latitude.to_numpy())
        depth_difference=np.abs(a.depth.to_numpy()-b.depth.to_numpy())
        records.append(dict(label=label,speed_scale=settings['speed_scale'],events=len(alternative),
                            change_from_nominal_events=len(alternative)-len(nominal),
                            mutual_time_matches_within_2s=int(keep.sum()),
                            median_horizontal_shift_km=float(np.median(distance)/1000),
                            p90_horizontal_shift_km=float(np.quantile(distance,.9)/1000),
                            median_absolute_depth_shift_km=float(np.median(depth_difference)),
                            p90_absolute_depth_shift_km=float(np.quantile(depth_difference,.9)),
                            removed_arrivals_final_qc=settings['raw_arrivals_before_final_qc']-settings['assigned_picks']))
    result=dict(nominal_events=len(nominal),tests=records,
                interpretation='Uniform P/S speed perturbations are declared sensitivity cases, not physical confidence intervals; time matches do not prove event identity')
    (ROOT/'results/tables/velocity_sensitivity.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':main()
