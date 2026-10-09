#!/usr/bin/env python3
"""Associate real picks using an explicitly approximate published 1-D model."""
import json
import argparse
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import pyocto
from obspy import read_inventory

ROOT = Path(__file__).resolve().parents[1]


def unix_seconds(values):
    # pandas 3 infers microsecond storage; never assume its integer unit.
    return pd.to_datetime(values,utc=True).astype('datetime64[ns, UTC]').astype('int64')/1e9


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--speed-scale',type=float,default=1.,help='Declared uniform P/S speed sensitivity factor')
    parser.add_argument('--label',default='approximate',choices=['approximate','velocity_slow','velocity_fast','nine_station'])
    parser.add_argument('--picks',type=Path,default=ROOT/'results/catalogs/volpick_picks.csv')
    parser.add_argument('--inventories',type=Path,nargs='+',default=[ROOT/'data/raw/stations.xml'])
    args=parser.parse_args()
    args.picks=args.picks.resolve()
    args.inventories=[p.resolve() for p in args.inventories]
    if args.speed_scale<=0:raise ValueError('Positive speed scale required')
    model = pd.read_csv(ROOT/'config/tepp2014_model_f.csv')
    model[['vp','vs']]*=args.speed_scale
    # Piecewise linear depth interpolation; not the target paper's 4-D model.
    path = ROOT/f'.cache/{args.label}_tt.bin'
    pyocto.VelocityModel1D.create_model(model, .1, 70., 32., path)
    velocity = pyocto.VelocityModel1D(path, tolerance=.5,
                                    surface_p_velocity=4.29*args.speed_scale, surface_s_velocity=2.38*args.speed_scale)
    associator = pyocto.OctoAssociator.from_area(
        lat=(-.90,-.76), lon=(-91.22,-91.08), zlim=(0,30),
        velocity_model=velocity, time_before=30, n_picks=5, n_p_picks=4,
        n_s_picks=1, n_p_and_s_picks=0, pick_match_tolerance=.5,
        min_interevent_time=2, min_node_size_location=1, n_threads=16,
        time_slicing=300, node_log_interval=100000)
    picks = pd.read_csv(args.picks)
    picks['station'] = picks.trace_id
    picks['time'] = unix_seconds(picks.peak_time_utc)
    span=picks.time.max()-picks.time.min()
    if not 86000 < span < 86400:
        raise ValueError(f'Unexpected daily pick span: {span} seconds')
    records = []
    inventory=read_inventory(args.inventories[0])
    for additional in args.inventories[1:]:inventory += read_inventory(additional)
    for network in inventory:
        for station in network:
            identifier = f'{network.code}.{station.code}.'
            if identifier in set(picks.station):
                records.append(dict(id=identifier, latitude=station.latitude,
                                    longitude=station.longitude,elevation=station.elevation))
    stations = associator.transform_stations(pd.DataFrame(records))
    events, assignments = associator.associate(picks, stations)
    raw_events,raw_arrivals=len(events),len(assignments)
    # PyOcto can update residuals during refinement after matching. Enforce
    # the stated final tolerance and phase minimums on the returned catalog.
    assignments=assignments[assignments.residual.abs()<=.5].copy()
    counts=assignments.groupby(['event_idx','phase']).size().unstack(fill_value=0)
    keep=counts.index[(counts.get('P',0)>=4)&(counts.get('S',0)>=1)]
    events=events[events.idx.isin(keep)].copy()
    assignments=assignments[assignments.event_idx.isin(keep)].copy()
    events['picks']=events.idx.map(assignments.groupby('event_idx').size())
    events = associator.transform_events(events)
    events['origin_time_utc'] = pd.to_datetime(events.time,unit='s',utc=True)
    events['location_method'] = 'PyOcto approximate Tepp2014 Model F; not differential relocation'
    events.to_csv(ROOT/f'results/catalogs/{args.label}_associated_events.csv',index=False)
    assignments.to_csv(ROOT/f'results/catalogs/{args.label}_pick_assignments.csv',index=False)
    summary = dict(events=len(events),assigned_picks=len(assignments),
                   velocity_source_doi='10.1002/2013JB010227',
                   input_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
                                 [ROOT/'config/tepp2014_model_f.csv',args.picks,*args.inventories]},
                   raw_events_before_final_qc=raw_events,raw_arrivals_before_final_qc=raw_arrivals,
                   assigned_P=int((assignments.phase=='P').sum()),assigned_S=int((assignments.phase=='S').sum()),
                   median_absolute_residual_s=float(assignments.residual.abs().median()),
                   max_absolute_residual_s=float(assignments.residual.abs().max()),
                   model='Tepp et al. 2014 Table 1 Model F; top grid value at -2 km',
                   interpolation='piecewise linear',speed_scale=args.speed_scale,depth_datum='km below sea level',
                   elevation_correction=dict(method='PyOcto surface correction',
                                             vp_km_s=4.29*args.speed_scale,vs_km_s=2.38*args.speed_scale),
                   domain_lat=[-.90,-.76],domain_lon=[-91.22,-91.08],depth_km=[0,30],
                   minimum_P=4,minimum_S=1,minimum_total=5,minimum_both_phase_stations=0,
                   match_tolerance_s=.5,duplicate_time_s=2,location_node_km=1,
                   travel_time_grid_km=.1,time_slice_s=300,n_threads=16,pick_time_span_s=float(span),pyocto_version=pyocto.__version__,
                   station_count=len(stations),limitations=['VCH1 unavailable; nine stations acquired, SN02 gapped','Not the source model',
                                'No HypoInverse or HypoDD quality control','No magnitudes estimated',
                                'Candidate events are not the published enhanced catalog'])
    (ROOT/f'results/tables/{args.label}_association.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__ == '__main__':
    main()
