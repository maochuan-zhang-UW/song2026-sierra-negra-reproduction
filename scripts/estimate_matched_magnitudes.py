#!/usr/bin/env python3
"""Explicit independent PCA/TLS amplitude-ratio approximation for detections."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from src.template_matching.matching import pair_ncc
from src.statistical_analysis.statistics import seismic_moment
ROOT=Path(__file__).resolve().parents[1]


def pca_ratio(template,detection,lag):
    n=len(template);lo=max(0,-lag);hi=min(n,n-lag)
    x=template[lo:hi].astype(float);y=detection[lo+lag:hi+lag].astype(float)
    x-=x.mean();y-=y.mean()
    _,vectors=np.linalg.eigh(np.cov(np.vstack([x,y])))
    vector=vectors[:,-1]
    return float(vector[1]/vector[0]) if vector[0] else np.nan


def main():
    seeds=pd.read_csv(ROOT/'results/catalogs/candidate_magnitude_catalog.csv').set_index('idx')
    catalog=pd.read_csv(ROOT/'results/catalogs/enhanced_candidate_catalog.csv')
    meta=pd.read_csv(ROOT/'results/tables/enhanced_window_metadata.csv')
    windows=np.load(ROOT/'.cache/enhanced_windows/windows.npz')
    rows=[]
    for event in catalog[catalog.template_idx.notna()].itertuples():
        template_idx=int(event.template_idx)
        a=meta[(meta.event_idx==template_idx)&(meta.phase=='P')&(meta.snr>=2)]
        b=meta[(meta.event_idx==event.idx)&(meta.phase=='P')&(meta.snr>=2)]
        common=a.merge(b,on=['station','component','phase'],suffixes=('_a','_b'))
        for pair in common.itertuples():
            x=windows[pair.key_a];y=windows[pair.key_b];ncc,lag=pair_ncc(x,y,10)
            if ncc<=0:continue
            alpha=pca_ratio(x,y,lag)
            if not np.isfinite(alpha) or alpha<=0:continue
            rows.append(dict(event_idx=event.idx,template_idx=template_idx,station=pair.station,ncc=ncc,lag_s=lag/50,amplitude_ratio=alpha,
                             relative_ml=float(seeds.loc[template_idx].approximate_ml+.7*np.log10(alpha))))
    stations=pd.DataFrame(rows)
    stations.to_csv(ROOT/'results/tables/matched_relative_station_magnitudes.csv',index=False)
    summary=stations.groupby('event_idx').relative_ml.agg(['median','count','std'])
    catalog['approximate_ml']=catalog.idx.map(seeds.approximate_ml)
    catalog['magnitude_stations']=catalog.idx.map(seeds.magnitude_stations)
    matched=catalog.template_idx.notna()
    catalog.loc[matched,'approximate_ml']=catalog.loc[matched,'idx'].map(summary['median'])
    catalog.loc[matched,'magnitude_stations']=catalog.loc[matched,'idx'].map(summary['count'])
    catalog['approximate_moment_Nm']=seismic_moment(catalog.approximate_ml.to_numpy())
    catalog['magnitude_provenance']=np.where(matched,'independent PCA amplitude ratio to approximate template ML','response-corrected Wood–Anderson station median')
    catalog.to_csv(ROOT/'results/catalogs/enhanced_magnitude_catalog.csv',index=False)
    record=dict(estimated_events=int(catalog.approximate_ml.notna().sum()),total_candidates=len(catalog),station_ratios=len(stations),
                relative_formula='ML_detection = ML_template + 0.7 log10(alpha)',
                ratio='dominant eigenvector detection/template slope of centered two-waveform covariance; signed best lag within 0.2 s; positive NCC only',
                aggregation='median station relative ML; available SNR>=2 P/Z waveforms',
                limitations=['Independent PCA formulation; original implementation unavailable','Approximate absolute template magnitudes',
                             'Correlation-defined detections not visually confirmed','No unpublished ratio or correlation quality thresholds imposed'])
    (ROOT/'results/tables/matched_magnitude_execution.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))

if __name__=='__main__':main()
