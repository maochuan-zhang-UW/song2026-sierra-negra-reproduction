#!/usr/bin/env python3
"""Associate real picks using an explicitly approximate published 1-D model."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pyocto
from obspy import read_inventory

ROOT = Path(__file__).resolve().parents[1]


def main():
    model = pd.read_csv(ROOT/'config/tepp2014_model_f.csv')
    # Piecewise linear depth interpolation; not the target paper's 4-D model.
    path = ROOT/'.cache/tepp2014_tt.bin'
    pyocto.VelocityModel1D.create_model(model, .1, 70., 32., path)
    velocity = pyocto.VelocityModel1D(path, tolerance=.5,
                                    surface_p_velocity=4.29, surface_s_velocity=2.38)
    associator = pyocto.OctoAssociator.from_area(
        lat=(-.90,-.76), lon=(-91.22,-91.08), zlim=(0,30),
        velocity_model=velocity, time_before=30, n_picks=5, n_p_picks=4,
        n_s_picks=1, n_p_and_s_picks=0, pick_match_tolerance=.5,
        min_interevent_time=2, min_node_size_location=1, n_threads=8)
    picks = pd.read_csv(ROOT/'results/catalogs/volpick_picks.csv')
    picks['station'] = picks.trace_id
    picks['time'] = pd.to_datetime(picks.peak_time_utc).astype('int64')/1e9
    records = []
    for network in read_inventory(ROOT/'data/raw/stations.xml'):
        for station in network:
            identifier = f'{network.code}.{station.code}.'
            if identifier in set(picks.station):
                records.append(dict(id=identifier, latitude=station.latitude,
                                    longitude=station.longitude,elevation=station.elevation))
    stations = associator.transform_stations(pd.DataFrame(records))
    events, assignments = associator.associate(picks, stations)
    events = associator.transform_events(events)
    events['origin_time_utc'] = pd.to_datetime(events.time,unit='s',utc=True)
    events['location_method'] = 'PyOcto approximate Tepp2014 Model F; not differential relocation'
    events.to_csv(ROOT/'results/catalogs/approximate_associated_events.csv',index=False)
    assignments.to_csv(ROOT/'results/catalogs/approximate_pick_assignments.csv',index=False)
    summary = dict(events=len(events),assigned_picks=len(assignments),
                   assigned_P=int((assignments.phase=='P').sum()),assigned_S=int((assignments.phase=='S').sum()),
                   median_absolute_residual_s=float(assignments.residual.abs().median()),
                   max_absolute_residual_s=float(assignments.residual.abs().max()),
                   model='Tepp et al. 2014 Table 1 Model F; top grid value at -2 km',
                   interpolation='piecewise linear',depth_datum='km below sea level',
                   elevation_correction='PyOcto surface Vp 4.29, Vs 2.38 km/s',
                   domain_lat=[-.90,-.76],domain_lon=[-91.22,-91.08],depth_km=[0,30],
                   minimum_P=4,minimum_S=1,minimum_total=5,minimum_both_phase_stations=0,
                   match_tolerance_s=.5,duplicate_time_s=2,location_node_km=1,
                   travel_time_grid_km=.1,pyocto_version=pyocto.__version__,
                   limitations=['Seven 8G stations only; EC picks pending','Not the source model',
                                'No HypoInverse or HypoDD quality control','No magnitudes estimated',
                                'Candidate events are not the published enhanced catalog'])
    (ROOT/'results/tables/approximate_association.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__ == '__main__':
    main()
