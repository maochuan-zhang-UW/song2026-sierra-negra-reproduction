#!/usr/bin/env python3
"""Validate seven-station candidates against EC picks and within-hour time controls."""
import json,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from obspy import read
from pyproj import Geod
from scripts.pick_ec_waveforms import common_segments
from scripts.associate_approximate import unix_seconds
from src.data_processing.travel_times import load_travel_times,nearest_pick
ROOT=Path(__file__).resolve().parents[1]
ZERO=1529971200.


def availability(times,segments):
    result=np.zeros(len(times),dtype=bool)
    for start,end in segments:result|=(times>=start+5)&(times<=end-5)
    return result


def supports(origin,predictions,pick_times,coverage,tolerance):
    phase_matches={};available={};residuals={};both=[]
    for station in ('SN02','SN06'):
        for phase in ('P','S'):
            key=station+'_'+phase
            predicted=origin+predictions[key]
            residuals[key]=nearest_pick(predicted,pick_times[key])
            available[key]=availability(predicted,coverage[station])
            phase_matches[key]=available[key]&(abs(residuals[key])<=tolerance)
        ordered=predictions[station+'_S']+residuals[station+'_S']>predictions[station+'_P']+residuals[station+'_P']
        both.append(phase_matches[station+'_P']&phase_matches[station+'_S']&ordered)
    counts=sum(phase_matches.values())
    return dict(any_phase=counts>=1,at_least_two_phases=counts>=2,same_station_P_and_S=both[0]|both[1],
                both_stations_P_and_S=both[0]&both[1]),residuals,available


def main():
    catalog=pd.read_csv(ROOT/'results/catalogs/enhanced_classified_catalog.csv')
    picks=pd.read_csv(ROOT/'results/catalogs/ec_volpick_picks.csv')
    picks['time']=unix_seconds(picks.peak_time_utc)
    stations=pd.read_csv(ROOT/'results/tables/acquired_station_metadata.csv').set_index('station')
    travel=load_travel_times(ROOT/'.cache/approximate_tt.bin');geod=Geod(ellps='WGS84')
    predictions={};pick_times={};coverage={}
    waveforms=read(ROOT/'data/raw/EC_20180626.mseed')
    for tr in waveforms:
        if tr.stats.channel.endswith('1'):tr.stats.channel=tr.stats.channel[:-1]+'N'
        elif tr.stats.channel.endswith('2'):tr.stats.channel=tr.stats.channel[:-1]+'E'
    for station in ('SN02','SN06'):
        coverage[station]=[(float(segment[0].stats.starttime),float(segment[0].stats.endtime))
                           for segment in common_segments(waveforms.select(station=station))]
        row=stations.loc[station]
        _,_,distance=geod.inv(catalog.longitude.to_numpy(),catalog.latitude.to_numpy(),np.full(len(catalog),row.longitude),np.full(len(catalog),row.latitude))
        for phase,speed in [('P',4.29),('S',2.38)]:
            key=station+'_'+phase
            predictions[key]=travel[phase](np.column_stack([distance/1000,catalog.depth]))+row.elevation_m/1000/speed
            pick_times[key]=picks[(picks.trace_id=='EC.'+station+'.')&(picks.phase==phase)].time.to_numpy()
    origin=catalog.time.to_numpy();rows=[];rng=np.random.default_rng(20261009)
    # Shared within-hour offsets preserve candidate clustering; each null replicate has 24 offsets.
    shifts=rng.uniform(60,3540,(500,24));hour=np.floor((origin-ZERO)/3600).astype(int);within=(origin-ZERO)%3600
    controls=ZERO+hour[None,:]*3600+(within[None,:]+shifts[:,hour])%3600
    for tolerance in (.2,.5,1,2):
        real,residuals,available=supports(origin,predictions,pick_times,coverage,tolerance)
        null={key:[] for key in real}
        for shifted in controls:
            support,_,_=supports(shifted,predictions,pick_times,coverage,tolerance)
            for key in null:null[key].append(support[key])
        for subset,mask in [('all',np.ones(len(catalog),dtype=bool)),('new',catalog.template_idx.notna().to_numpy()),('seeds',catalog.template_idx.isna().to_numpy())]:
            for criterion in real:
                count=int(real[criterion][mask].sum())
                values=np.array([support[mask].sum() for support in null[criterion]])
                rows.append(dict(subset=subset,tolerance_s=tolerance,criterion=criterion,candidates=int(mask.sum()),supported=count,
                                 null_mean=float(values.mean()),null_2_5_percentile=float(np.percentile(values,2.5)),null_97_5_percentile=float(np.percentile(values,97.5)),
                                 empirical_upper_tail_p=float((1+(values>=count).sum())/(len(values)+1))))
        if tolerance==.5:
            for key,value in residuals.items():catalog[key+'_arrival_residual_s']=value;catalog[key+'_available']=available[key]
            for key,value in real.items():catalog['heldout_'+key]=value
    catalog.to_csv(ROOT/'results/catalogs/heldout_validated_candidates.csv',index=False)
    summary=pd.DataFrame(rows);summary.to_csv(ROOT/'results/tables/heldout_station_validation.csv',index=False)
    record=dict(method='EC stations excluded from seven-station template construction; predict arrivals with same FMM approximation and elevation correction',
                controls='500 within-hour shared-catalog time shifts; independent offset per UTC hour; 60..3540 seconds circular',seed=20261009,
                primary_tolerance_s=.5,secondary_tolerances_s=[.2,1,2],gap_policy='real common three-component segments; exclude 5-second blind edges',
                input_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'results/catalogs/ec_volpick_picks.csv',ROOT/'results/catalogs/enhanced_classified_catalog.csv',ROOT/'.cache/approximate_tt.bin']},
                limitations=['Pick model shared across networks but observed waveforms independent','Approximate inherited locations affect arrival residuals',
                             'Missing heldout support is not proof of false detection','Time control assumes approximate stationarity within each hour',
                             'No heldout-trained tuning or manual earthquake labels','No calibrated earthquake false-positive rate'])
    (ROOT/'results/tables/heldout_station_execution.json').write_text(json.dumps(record,indent=2)+'\n')
    print(summary[(summary.tolerance_s==.5)&(summary.criterion=='same_station_P_and_S')].to_string(index=False))

if __name__=='__main__':main()
