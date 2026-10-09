#!/usr/bin/env python3
"""Measure new detections on actual velocity traces; retain inherited FI separately."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from src.earthquake_classification.frequency import frequency_index,classify
ROOT=Path(__file__).resolve().parents[1]


def main():
    seed=pd.read_csv(ROOT/'results/catalogs/candidate_classified_catalog.csv')
    new=pd.read_csv(ROOT/'results/catalogs/template_matched_candidate_events.csv')
    seedmeta=pd.read_csv(ROOT/'results/tables/candidate_window_metadata.csv')
    seedtime=seed.set_index('idx').time
    windows={};records=[];summaries=[];arrays={}
    for row in new.itertuples():
        event_idx=int(seed.idx.max())+1+row.Index
        hour=int((row.time-1529971200)//3600)
        origin=1529971200+max(0,hour*3600-30)
        eligible=seedmeta[(seedmeta.event_idx==row.template_idx)&(seedmeta.snr>=2)]
        fis=[]
        for channel in eligible.itertuples():
            cache_key=(hour,channel.station,channel.component)
            if cache_key not in arrays:
                arrays[cache_key]=np.load(ROOT/f'.cache/matching_velocity/hour_{hour:02d}/{channel.station}.{channel.component}.npy',mmap_mode='r')
            data=arrays[cache_key]
            arrival=row.time+pd.Timestamp(channel.pick_time_utc).timestamp()-seedtime.loc[row.template_idx]
            start=round((arrival-1-origin)*50)
            signal=np.array(data[start:start+250],dtype=np.float32)
            noises=[]
            for offset in (-11,-6):
                noise_start=round((arrival+offset-origin)*50)
                noise=np.array(data[noise_start:noise_start+250])
                if len(noise)!=250:raise ValueError('Noise window extends beyond real padding')
                numerator=np.sqrt(np.mean((signal-signal.mean())**2))
                denominator=np.sqrt(np.mean((noise-noise.mean())**2))
                noises.append(numerator/denominator if denominator else np.nan)
            if len(signal)!=250 or not np.isfinite(signal).all():raise ValueError('Invalid matched window')
            key=f'{row.event_id}__{channel.station}.{channel.component}.{channel.phase}'
            windows[key]=signal
            records.append(dict(key=key,event_idx=event_idx,station=channel.station,component=channel.component,phase=channel.phase,
                                sampling_rate=50,snr=noises[0],snr_near_noise=noises[1],pick_time_utc=pd.Timestamp(arrival,unit='s',tz='UTC'),units='m/s',arrival_provenance='inherited template phase offset'))
            if channel.phase=='P' and noises[0]>=2:
                fi=frequency_index(signal,50)
                if np.isfinite(fi):fis.append(fi)
        measured=float(np.mean(fis)) if fis else np.nan
        summaries.append(dict(event_id=row.event_id,idx=event_idx,measured_frequency_index=measured,measured_type=classify(measured),measured_fi_stations=len(fis)))
    new=new.drop(columns=['idx','measured_frequency_index','measured_type','measured_fi_stations'],errors='ignore')
    new=new.merge(pd.DataFrame(summaries),on='event_id',validate='1:1')
    new.to_csv(ROOT/'results/catalogs/template_matched_candidate_events.csv',index=False)
    combined=pd.concat([seed,new],ignore_index=True).sort_values('time')
    combined.to_csv(ROOT/'results/catalogs/enhanced_candidate_catalog.csv',index=False)
    metadata=pd.concat([seedmeta,pd.DataFrame(records)],ignore_index=True)
    metadata.to_csv(ROOT/'results/tables/enhanced_window_metadata.csv',index=False)
    archive=np.load(ROOT/'.cache/candidate_windows/windows.npz')
    windows.update({key:archive[key] for key in archive.files})
    destination=ROOT/'.cache/enhanced_windows';destination.mkdir(exist_ok=True)
    np.savez_compressed(destination/'windows.npz',**windows)
    eligible=new[new.measured_type!='unclassified']
    record=dict(new_events=len(new),combined_candidates=len(combined),new_windows=len(records),
                inherited_counts=new.type.value_counts().to_dict(),measured_counts=new.measured_type.value_counts().to_dict(),
                comparable_events=len(eligible),inherited_measured_agreement=int((eligible.type==eligible.measured_type).sum()),
                velocity_processing='hourly real-padded response-corrected 2-20 Hz continuous blocks',
                limitations=['Detection arrivals inherited, not repicked','Primary classifications inherited from template per publication',
                             'Direct FI uses available qualifying template channels, not all acquired channels','Locations inherited; events not visually confirmed'])
    (ROOT/'results/tables/matched_window_execution.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))

if __name__=='__main__':main()
