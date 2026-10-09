#!/usr/bin/env python3
"""Actual family recurrence/periodicity correlation and family bootstrap sensitivity."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import pearsonr
ROOT=Path(__file__).resolve().parents[1]

def main():
    stats=pd.read_csv(ROOT/'results/tables/enhanced_permissive_family_statistics.csv')
    x=stats.mean_recurrence_s.to_numpy();y=stats.periodicity_ddof0.to_numpy()
    fit=pearsonr(x,y);fisher=fit.confidence_interval();rng=np.random.default_rng(20261009);sample=[]
    for _ in range(5000):
        index=rng.integers(0,len(x),len(x))
        if np.ptp(x[index]) and np.ptp(y[index]):sample.append(float(pearsonr(x[index],y[index]).statistic))
    interval=np.percentile(sample,[2.5,97.5])
    catalog=pd.read_csv(ROOT/'results/catalogs/enhanced_classified_catalog.csv')
    measurable=catalog[(catalog.direct_window_type=='LP')&(catalog.fi_stations>=4)].sort_values('time')
    record=dict(screen='permissive one common station; >=10 member families',families=len(stats),family_types=stats.family_type.value_counts().to_dict(),
                mean_recurrence_periodicity_pearson_r=float(fit.statistic),p_value=float(fit.pvalue),
                fisher_approximate_95_percent=[float(fisher.low),float(fisher.high)],family_bootstrap_95_percent=[float(v) for v in interval],bootstrap_replicates=5000,random_seed=20261009,
                first_direct_LP_at_least_four_P_stations=measurable.origin_time_utc.iloc[0] if len(measurable) else None,
                limitations=['Family membership is screen-sensitive','Bootstrap conditional on these 14 computed families',
                             'Missed events, station and magnitude errors not represented','First qualifying spectrum is not physical onset'])
    (ROOT/'results/tables/family_periodicity_execution.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))
if __name__=='__main__':main()
