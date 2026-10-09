#!/usr/bin/env python3
"""Classify and cluster REAL supplied event windows; no automatic fake inputs.
NPZ arrays have keys <event_id>__<station.component.phase>; CSV rows have
key,sampling_rate,snr. FI uses only vertical P windows. Filtered velocity
windows must already span [-1,+4] s around the documented picks.
"""
import argparse,itertools,json
from pathlib import Path
import numpy as np
import pandas as pd
from src.earthquake_classification.frequency import frequency_index,event_frequency_index,classify
from src.multiplet_clustering.families import network_similarity,connected_families
from src.statistical_analysis.statistics import recurrence,moment_recurrence_pairs,regression

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('catalog',type=Path);p.add_argument('windows',type=Path);p.add_argument('metadata',type=Path)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--max-lag-seconds',type=float,required=True)
p.add_argument('--pairing',choices=['preceding','following'],required=True)
p.add_argument('--transform',choices=['linear','log10'],required=True)
p.add_argument('--ddof',type=int,choices=[0,1],required=True)
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
catalog=pd.read_csv(str(a.catalog));meta=pd.read_csv(str(a.metadata)).set_index('key')
if catalog.event_id.duplicated().any() or meta.index.duplicated().any():raise ValueError('Duplicate IDs or window keys')
archive=np.load(str(a.windows),allow_pickle=False)
windows={i:{} for i in catalog.event_id};fis={i:[] for i in catalog.event_id};snrs={i:[] for i in catalog.event_id}
rates=set()
for key in archive.files:
    event,channel=key.split('__',1)
    if event not in windows or key not in meta.index:raise ValueError('Unknown event or missing window metadata')
    data=np.asarray(archive[key]);row=meta.loc[key];fs=float(row.sampling_rate);rates.add(fs)
    if data.ndim!=1 or len(data)!=round(5*fs) or not np.isfinite(data).all():raise ValueError('Invalid five-second window')
    if float(row.snr)<2:continue
    windows[event][channel]=data
    if channel.endswith('.Z.P'):
        fis[event].append(frequency_index(data,fs));snrs[event].append(float(row.snr))
if len(rates)!=1:raise ValueError('Resample windows to one explicitly documented sample rate')
fs=rates.pop();lag=round(a.max_lag_seconds*fs)
catalog['frequency_index']=[event_frequency_index(fis[i],snrs[i]) for i in catalog.event_id]
catalog['fi_provenance']='measured from supplied velocity windows'
# Template detections inherit FI and family linkage only when explicit template IDs exist.
if 'template_id' in catalog:
    indexed=catalog.set_index('event_id')
    for index,row in catalog.iterrows():
        if pd.notna(row.template_id):
            if row.template_id not in indexed.index:raise ValueError('Unknown template ID')
            catalog.loc[index,'frequency_index']=indexed.loc[row.template_id,'frequency_index']
            catalog.loc[index,'fi_provenance']='inherited from template'
catalog['type']=[classify(fi) for fi in catalog.frequency_index]
edges=[]
for left,right in itertools.combinations(catalog.event_id,2):
    r,n=network_similarity(windows[left],windows[right],lag)
    if n:edges.append((left,right,r))
if 'template_id' in catalog:
    edges.extend((row.event_id,row.template_id,1.0) for row in catalog.itertuples() if pd.notna(row.template_id))
families,anti=connected_families(catalog.event_id,edges)
catalog['family_id']=-1;statistics=[];paired=[]
for family_id,events in enumerate(families):
    catalog.loc[catalog.event_id.isin(events),'family_id']=family_id
    sub=catalog[catalog.event_id.isin(events)].sort_values('origin_time')
    seconds=pd.to_datetime(sub.origin_time,utc=True).astype('datetime64[ns, UTC]').astype('int64').values/1e9
    intervals,periodicity=recurrence(seconds,ddof=a.ddof)
    statistics.append(dict(family_id=family_id,n_events=len(sub),mean_fi=float(sub.frequency_index.mean()),
                           type=classify(sub.frequency_index.mean()),mean_recurrence_seconds=float(intervals.mean()),
                           periodicity=periodicity,ddof=a.ddof))
    tr,moment=moment_recurrence_pairs(seconds,sub.magnitude.values,a.pairing)
    paired.extend(dict(family_id=family_id,recurrence_seconds=float(t),moment_nm=float(m)) for t,m in zip(tr,moment))
catalog.to_csv(str(a.output/'classified_catalog.csv'),index=False)
pd.DataFrame(statistics).to_csv(str(a.output/'family_statistics.csv'),index=False)
pd.DataFrame(anti,columns=['event_a','event_b','ncc']).to_csv(str(a.output/'anti_candidates_NEED_MANUAL_REVIEW.csv'),index=False)
pd.DataFrame(paired).to_csv(str(a.output/'moment_recurrence_pairs.csv'),index=False)
settings=dict(max_lag_seconds=a.max_lag_seconds,pairing=a.pairing,transform=a.transform,ddof=a.ddof,
              n_families=len(families),warning='Anti candidates need manual review; use family/phase subsets for published regressions. Common-channel averaging is an independent convention, not verified station-weighting.')
(a.output/'settings.json').write_text(json.dumps(settings,indent=2)+'\n')
print(json.dumps(settings,indent=2))
