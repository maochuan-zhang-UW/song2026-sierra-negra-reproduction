#!/usr/bin/env python3
"""Reapply stricter declared thresholds to actual stored full-day peak scores."""
import bisect,json
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]

def main():
    raw=pd.read_csv(ROOT/'results/catalogs/raw_template_peaks.csv')
    audit=pd.read_csv(ROOT/'results/tables/template_detection_audit.csv')
    raw=raw.merge(audit[['hour','template_idx','median_absolute_ncc']],on=['hour','template_idx'],validate='m:1')
    known=np.sort(pd.read_csv(ROOT/'results/catalogs/candidate_classified_catalog.csv').time.to_numpy())
    pos=np.searchsorted(known,raw.time)
    distance=np.minimum(abs(raw.time.to_numpy()-known[np.minimum(pos,len(known)-1)]),abs(raw.time.to_numpy()-known[np.maximum(pos-1,0)]))
    raw=raw[distance>2]
    rows=[]
    for multiplier in (9,12,15):
        for minimum in (.4,.5,.6,.7):
            selected=raw[raw.network_ncc>=np.maximum(minimum,multiplier*raw.median_absolute_ncc)]
            times=[]
            for event in selected.sort_values('network_ncc',ascending=False).itertuples():
                i=bisect.bisect_left(times,event.time)
                if (i and event.time-times[i-1]<2) or (i<len(times) and times[i]-event.time<2):continue
                bisect.insort(times,event.time)
            rows.append(dict(MAD_multiplier=multiplier,minimum_network_NCC=minimum,additional_candidates=len(times)))
    frame=pd.DataFrame(rows)
    if frame.iloc[0].additional_candidates!=json.loads((ROOT/'results/tables/template_matching_execution.json').read_text())['additional_candidates']:raise ValueError('Baseline reapplication does not agree')
    frame.to_csv(ROOT/'results/tables/template_threshold_sensitivity.csv',index=False)
    print(frame.to_string(index=False))
if __name__=='__main__':main()
