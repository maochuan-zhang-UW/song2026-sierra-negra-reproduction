#!/usr/bin/env python3
"""Classify real candidate waveforms and quantify signed repeating families."""
import argparse,json,multiprocessing
from pathlib import Path
import numpy as np
import pandas as pd
from src.earthquake_classification.frequency import frequency_index,classify
from src.template_matching.matching import pairwise_ncc
from src.multiplet_clustering.families import connected_families
from src.statistical_analysis.statistics import recurrence

ROOT=Path(__file__).resolve().parents[1]


def network_matrix(channel_matrices,metadata,event_ids,snr_column):
    n=len(event_ids);lookup={event:i for i,event in enumerate(event_ids)}
    total=np.zeros((n,n));stations=np.zeros((n,n),dtype=int)
    for station,sub in metadata.groupby('station'):
        numerator=np.zeros((n,n));channels=np.zeros((n,n),dtype=int)
        for component,rows in sub.groupby(['component','phase']):
            key=station+'.'+'.'.join(component)
            indices=np.array([lookup[e] for e in rows.event_idx])
            eligible=np.isfinite(rows[snr_column])&(rows[snr_column]>=2)
            valid=eligible.to_numpy()[:,None]&eligible.to_numpy()[None,:]
            scores=channel_matrices[key]
            valid &= np.isfinite(scores)
            numerator[np.ix_(indices,indices)]+=np.where(valid,scores,0)
            channels[np.ix_(indices,indices)]+=valid
        valid=channels>0
        mean=np.zeros((n,n));np.divide(numerator,channels,out=mean,where=valid)
        total+=mean;stations+=valid
    result=np.full((n,n),np.nan)
    np.divide(total,stations,out=result,where=stations>0)
    return result,stations


def correlate_channel(task):
    key,data=task
    return key,len(data),{lag:pairwise_ncc(data,lag) for lag in (0,10)}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--enhanced',action='store_true')
    args=parser.parse_args()
    prefix='enhanced' if args.enhanced else 'candidate'
    catalog=pd.read_csv(ROOT/('results/catalogs/enhanced_candidate_catalog.csv' if args.enhanced else 'results/catalogs/approximate_associated_events.csv'))
    inherited=catalog.set_index('idx').frequency_index.to_dict() if args.enhanced else {}
    is_inherited=catalog.set_index('idx').fi_provenance.fillna('').str.startswith('inherited').to_dict() if args.enhanced else {}
    metadata=pd.read_csv(ROOT/f'results/tables/{prefix}_window_metadata.csv')
    archive=np.load(ROOT/f'.cache/{prefix}_windows/windows.npz',allow_pickle=False)
    ids=catalog.idx.to_list();names=dict(zip(ids,catalog.event_id)) if args.enhanced else {i:f'candidate_{i:04d}' for i in ids}
    catalog['event_id']=catalog.idx.map(names)
    fi_rows=[]
    for row in metadata[metadata.phase=='P'].itertuples():
        waveform=archive[row.key]
        fi_rows.append(dict(event_idx=row.event_idx,station=row.station,frequency_index=frequency_index(waveform,50),
                            alternate_band_fi=frequency_index(waveform,50,low=(2,5),high=(8,16)),
                            snr=row.snr,snr_near_noise=row.snr_near_noise))
    station_fi=pd.DataFrame(fi_rows)
    station_fi.to_csv(ROOT/f'results/tables/{prefix}_station_frequency_indices.csv',index=False)
    rng=np.random.default_rng(20261009)
    summaries=[]
    for event in ids:
        rows=station_fi[station_fi.event_idx==event]
        valid=rows[(rows.snr>=2)&np.isfinite(rows.frequency_index)]
        values=valid.frequency_index.to_numpy()
        direct_fi=float(values.mean()) if len(values) else np.nan
        fi=inherited[event] if is_inherited.get(event,False) else direct_fi
        near=rows[(rows.snr_near_noise>=2)&np.isfinite(rows.frequency_index)]
        alternate=float(near.frequency_index.mean()) if len(near) else np.nan
        interval=np.percentile(rng.choice(values,(1000,len(values)),replace=True).mean(axis=1),[2.5,97.5]) if len(values)>=3 else [np.nan,np.nan]
        summaries.append(dict(idx=event,frequency_index=fi,type=classify(fi),direct_window_fi=direct_fi,direct_window_type=classify(direct_fi),fi_stations=len(values),
                              fi_station_bootstrap_low=interval[0],fi_station_bootstrap_high=interval[1],
                              near_noise_type=classify(alternate),near_noise_fi=alternate,
                              alternate_band_type=classify(valid.alternate_band_fi.mean()),
                              threshold_minus_1_8_type=classify(fi,-1.8),threshold_minus_2_2_type=classify(fi,-2.2)))
    summary_frame=pd.DataFrame(summaries)
    catalog=catalog.drop(columns=[c for c in summary_frame.columns if c!='idx' and c in catalog])
    catalog=catalog.merge(summary_frame,on='idx',validate='1:1')
    destination=ROOT/f'.cache/{prefix}_families';destination.mkdir(exist_ok=True)
    channel_sets={0:{},10:{}}
    tasks=[]
    for (station,component,phase),rows in metadata.groupby(['station','component','phase']):
        data=np.array([archive[key] for key in rows.key])
        tasks.append(('.'.join([station,component,phase]),data))
    with multiprocessing.get_context('fork').Pool(8) as pool:
        for key,count,matrices in pool.imap_unordered(correlate_channel,tasks):
            for lag in channel_sets:channel_sets[lag][key]=matrices[lag]
            print(key,count,'windows correlated',flush=True)
    sensitivity=[];main_score=None;main_counts=None;main_families=None
    for lag in (0,10):
        for noise in ('snr','snr_near_noise'):
            scores,counts=network_matrix(channel_sets[lag],metadata,ids,noise)
            for minimum in (1,4):
                pairs=[(names[ids[i]],names[ids[j]],float(scores[i,j])) for i in range(len(ids)) for j in range(i+1,len(ids))
                       if counts[i,j]>=minimum and np.isfinite(scores[i,j])]
                families,anti=connected_families(catalog.event_id,pairs,minimum_size=10,threshold=.7)
                row=dict(lag_seconds=lag/50,noise_snr=noise,minimum_common_stations=minimum,
                         families=len(families),family_events=sum(map(len,families)),
                         positive_edges=sum(r>.7 for _,_,r in pairs),negative_candidates=len(anti))
                sensitivity.append(row)
                if lag==10 and noise=='snr' and minimum==4:
                    main_score,main_counts,main_families=scores,counts,families
                    pd.DataFrame(anti,columns=['event_a','event_b','signed_network_ncc']).to_csv(
                        ROOT/f'results/catalogs/{prefix}_anticorrelations_NEED_REVIEW.csv',index=False)
                    np.savez_compressed(destination/'network_similarity.npz',scores=scores,common_stations=counts,event_ids=catalog.event_id.to_numpy(dtype=str))
    catalog['family_id']=-1;familystats=[];interval_rows=[]
    for number,family in enumerate(main_families):
        catalog.loc[catalog.event_id.isin(family),'family_id']=number
        sub=catalog[catalog.event_id.isin(family)].sort_values('time')
        intervals,periodicity=recurrence(sub.time.to_numpy(),ddof=0)
        _,sample_periodicity=recurrence(sub.time.to_numpy(),ddof=1)
        mean_fi=float(sub.frequency_index.mean())
        familystats.append(dict(family_id=number,events=len(sub),family_type=classify(mean_fi),mean_fi=mean_fi,
                                LP_members=int((sub.type=='LP').sum()),VT_members=int((sub.type=='VT').sum()),
                                first_origin_utc=sub.origin_time_utc.iloc[0],last_origin_utc=sub.origin_time_utc.iloc[-1],
                                mean_recurrence_s=float(intervals.mean()),periodicity_ddof0=periodicity,
                                periodicity_ddof1=sample_periodicity))
        interval_rows.extend(dict(family_id=number,preceding_event=a,following_event=b,interval_s=float(t)) for a,b,t in
                             zip(sub.event_id.iloc[:-1],sub.event_id.iloc[1:],intervals))
    catalog.to_csv(ROOT/f'results/catalogs/{prefix}_classified_catalog.csv',index=False)
    pd.DataFrame(familystats,columns=['family_id','events','family_type','mean_fi','LP_members','VT_members',
                                    'first_origin_utc','last_origin_utc','mean_recurrence_s','periodicity_ddof0','periodicity_ddof1']).to_csv(ROOT/f'results/tables/{prefix}_family_statistics.csv',index=False)
    pd.DataFrame(interval_rows,columns=['family_id','preceding_event','following_event','interval_s']).to_csv(ROOT/f'results/tables/{prefix}_recurrence_intervals.csv',index=False)
    pd.DataFrame(sensitivity).to_csv(ROOT/f'results/tables/{prefix}_family_sensitivity.csv',index=False)
    record=dict(events=len(catalog),class_counts=catalog.type.value_counts().to_dict(),families=len(main_families),
                family_events=sum(map(len,main_families)),primary_minimum_common_stations=4,
                primary_max_lag_s=.2,NCC_threshold=.7,minimum_family_size=10,
                station_weighting='mean component scores within station, then equal mean across common stations',
                limitations=['Template classifications inherited; independent direct FI also provided' if args.enhanced else 'No template-expanded events','Approximate locations only','No manual waveform labels or calibration events',
                             'Noise windows, SNR and lag convention are independent choices',
                             'Minimum four common stations is an independent quality screen',
                             'Anticorrelations require visual review','No magnitudes or moment-recurrence fit'])
    (ROOT/f'results/tables/{prefix}_family_execution.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))


if __name__=='__main__':main()
