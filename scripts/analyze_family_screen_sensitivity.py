#!/usr/bin/env python3
"""Reuse actual signed network matrix for a permissive one-common-station screen."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from src.multiplet_clustering.families import connected_families
from src.statistical_analysis.statistics import recurrence
from src.earthquake_classification.frequency import classify
ROOT=Path(__file__).resolve().parents[1]

def main():
    catalog=pd.read_csv(ROOT/'results/catalogs/enhanced_classified_catalog.csv')
    archive=np.load(ROOT/'.cache/enhanced_families/network_similarity.npz')
    scores=archive['scores'];counts=archive['common_stations'];ids=archive['event_ids']
    pairs=[(ids[i],ids[j],float(scores[i,j])) for i in range(len(ids)) for j in range(i+1,len(ids)) if counts[i,j]>=1 and np.isfinite(scores[i,j])]
    families,negative=connected_families(ids,pairs,minimum_size=10,threshold=.7)
    catalog['family_id']=-1;rows=[]
    for number,family in enumerate(families):
        catalog.loc[catalog.event_id.isin(family),'family_id']=number
        sub=catalog[catalog.event_id.isin(family)].sort_values('time');intervals,periodicity=recurrence(sub.time.to_numpy())
        rows.append(dict(family_id=number,events=len(sub),family_type=classify(sub.frequency_index.mean()),mean_fi=sub.frequency_index.mean(),
                         first_origin_utc=sub.origin_time_utc.iloc[0],last_origin_utc=sub.origin_time_utc.iloc[-1],mean_recurrence_s=intervals.mean(),periodicity_ddof0=periodicity))
    catalog.to_csv(ROOT/'results/catalogs/enhanced_permissive_classified_catalog.csv',index=False)
    pd.DataFrame(rows).to_csv(ROOT/'results/tables/enhanced_permissive_family_statistics.csv',index=False)
    record=dict(common_stations_minimum=1,families=len(families),family_members=sum(map(len,families)),negative_candidates=len(negative),
                limitations='Permissive sensitivity only; some edges supported by one station, not source-confirmed membership')
    (ROOT/'results/tables/enhanced_permissive_family_execution.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))
if __name__=='__main__':main()
