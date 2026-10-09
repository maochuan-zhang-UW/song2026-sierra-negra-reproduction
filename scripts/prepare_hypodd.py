#!/usr/bin/env python3
"""Write genuine phase differential inputs with published pairing criteria."""
import hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[1]


def main():
    settings=json.loads((ROOT/'config/hypodd_ct_pilot.json').read_text())
    events=pd.read_csv(ROOT/'results/catalogs/nine_station_associated_events.csv')
    arrivals=pd.read_csv(ROOT/'results/catalogs/nine_station_pick_assignments.csv')
    stations=pd.read_csv(ROOT/'results/tables/acquired_station_metadata.csv')
    model=pd.read_csv(ROOT/'config/tepp2014_model_f.csv')
    output=ROOT/'.cache/hypodd_ct';output.mkdir(exist_ok=True)
    origins=pd.Series(pd.to_datetime(events.origin_time_utc,utc=True).dt.round('10ms').map(lambda value:value.timestamp()).to_numpy(),index=events.idx)
    grouped={}
    for row in arrivals.itertuples():
        station=row.station.split('.')[1];key=(station,row.phase)
        event=grouped.setdefault(row.event_idx,{})
        if key in event:raise ValueError('Duplicate event/station/phase')
        event[key]=row.time-origins.loc[row.event_idx]
    pairs=sorted(cKDTree(events[['x','y','depth']].to_numpy()).query_pairs(settings['maximum_initial_pair_separation_km']))
    observations=0;accepted=0;phase_counts={'P':0,'S':0};ids=events.idx.to_numpy()
    with (output/'dt.ct').open('w') as file:
        for i,j in pairs:
            a,b=int(ids[i]),int(ids[j]);shared=sorted(set(grouped[a])&set(grouped[b]))
            if len(shared)<settings['minimum_common_station_phase_observations']:continue
            file.write(f'# {a+1} {b+1}\n');accepted+=1
            for station,phase in shared:
                file.write(f'{station} {grouped[a][(station,phase)]:.6f} {grouped[b][(station,phase)]:.6f} 1.0 {phase}\n')
                observations+=1;phase_counts[phase]+=1
    with (output/'event.sel').open('w') as file:
        for row in events.itertuples():
            # Use integer timestamp rounding, avoiding float hundredth truncation.
            time=pd.Timestamp(row.origin_time_utc).round('10ms')
            hhmmsscc=f'{time.hour:02d}{time.minute:02d}{time.second:02d}{time.microsecond//10000:02d}'
            residual=arrivals[arrivals.event_idx==row.idx].residual.to_numpy()
            rms=np.sqrt(np.mean(residual**2))
            file.write(f'{time:%Y%m%d} {hhmmsscc} {row.latitude:.7f} {row.longitude:.7f} {row.depth:.5f} -9 -9 -9 {rms:.6f} {row.idx+1}\n')
    used=set(arrivals.station.str.split('.').str[1])
    with (output/'station.sel').open('w') as file:
        for row in stations[stations.station.isin(used)].itertuples():
            file.write(f'{row.station} {row.latitude:.7f} {row.longitude:.7f} {row.elevation_m:.3f}\n')
    (output/'dt.cc').write_text('')
    controls=['hypoDD_2','dt.cc','dt.ct','event.sel','station.sel','hypoDD.loc','hypoDD.reloc','hypoDD.sta','hypoDD.res','hypoDD.src',
              f"2 3 {settings['station_centroid_maximum_distance_km']}",
              f"0 {settings['minimum_common_station_phase_observations']} -999 -999 -999",
              f"2 2 {settings['airquake_removal']} 1",
              f"{settings['iterations']} 0 0 -999 -999 {settings['P_weight']} {settings['S_weight']} -999 -999 {settings['damping']}",'1',
              ' '.join(map(str,model.depth))+' -9',
              ' '.join(map(str,model.vp))+' -9',
              ' '.join(f'{p/s:.8f}' for p,s in zip(model.vp,model.vs))+' -9','0']
    (output/'hypoDD.inp').write_text('\n'.join(controls)+'\n')
    record=dict(events=len(events),stations=len(used),event_pairs=accepted,differential_observations=observations,phase_counts=phase_counts,
                settings=settings,origin_time_file_precision_s=.01,
                input_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [output/'dt.ct',output/'event.sel',output/'station.sel',output/'hypoDD.inp']},
                note='Negative-nine metadata are missing-value placeholders, not estimated magnitudes or location uncertainties')
    (ROOT/'results/tables/hypodd_ct_input.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))

if __name__=='__main__':main()
