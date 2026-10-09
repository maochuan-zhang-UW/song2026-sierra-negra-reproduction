#!/usr/bin/env python3
"""Decompress and validate acquired GPS RINEX without interpreting positions."""
import hashlib
import json
from pathlib import Path
import hatanaka
import pandas as pd
from src.data_processing.rinex import read_observations

ROOT = Path(__file__).resolve().parents[1]


def main():
    summaries = []
    for station in ('GV03', 'GV09'):
        stem = station.lower()+'1770.18'
        source = ROOT/'data/raw/gnss'/(stem+'d.Z')
        target = ROOT/'data/raw/gnss'/(stem+'o')
        target.write_bytes(hatanaka.decompress(source.read_bytes()))
        header, obs = read_observations(target)
        epochs = obs.groupby('time_utc').agg(satellites=('satellite','size'))
        dual = obs[['L1','L2','C1','P2']].notna().all(axis=1)
        epochs['dual_frequency_satellites'] = obs.assign(dual=dual).groupby('time_utc').dual.sum()
        epochs['gps_hour'] = ((epochs.index-pd.Timestamp('2018-06-25T23:59:42Z')).total_seconds()/3600)
        epochs.to_csv(ROOT/'results/tables'/(station.lower()+'_rinex_epochs.csv'))
        gaps = epochs.index.to_series().diff().dt.total_seconds()
        record = dict(station=station,status='validated_rinex_observations',**header,
                      compressed_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                      rinex_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                      epochs=len(epochs),expected_daily_epochs=2880,
                      daily_epoch_fraction=len(epochs)/2880,
                      first_epoch_utc=epochs.index[0].isoformat(),last_epoch_utc=epochs.index[-1].isoformat(),
                      internal_gaps_over_30s=int((gaps>30.001).sum()),
                      maximum_internal_spacing_s=float(gaps.max()),
                      min_satellites=int(epochs.satellites.min()),
                      median_satellites=float(epochs.satellites.median()),
                      min_dual_frequency_satellites=int(epochs.dual_frequency_satellites.min()),
                      loss_of_lock_flags=int(((obs.L1_lli%2==1)|(obs.L2_lli%2==1)).sum()))
        summaries.append(record)
    (ROOT/'results/tables/gnss_rinex_validation.json').write_text(json.dumps(summaries,indent=2)+'\n')
    print(json.dumps(summaries,indent=2))


if __name__ == '__main__':
    main()
