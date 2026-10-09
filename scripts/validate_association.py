#!/usr/bin/env python3
"""Validate candidate association constraints and compare original-catalog times."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, FormatStrFormatter
from scripts.associate_approximate import unix_seconds

ROOT=Path(__file__).resolve().parents[1]


def main():
    events=pd.read_csv(ROOT/'results/catalogs/approximate_associated_events.csv')
    picks=pd.read_csv(ROOT/'results/catalogs/approximate_pick_assignments.csv')
    original=pd.read_csv(ROOT/'results/catalogs/original_20180626.csv')
    counts=picks.groupby(['event_idx','phase']).size().unstack(fill_value=0)
    assert (counts.P>=4).all() and (counts.S>=1).all()
    assert picks.residual.abs().max()<=.500001
    assert not events.idx.duplicated().any()
    assert not picks.duplicated(['event_idx','station','phase']).any()
    assert set(picks.event_idx)==set(events.idx)
    assert events.latitude.between(-.90,-.76).all()
    assert events.longitude.between(-91.22,-91.08).all()
    assert events.depth.between(0,30).all()
    times=unix_seconds(original.origin_time).to_numpy()
    differences=np.abs(events.time.to_numpy()[:,None]-times[None,:])
    nearest=differences.argmin(axis=1)
    table=pd.DataFrame(dict(candidate_id=events.idx,original_event_id=original.event_id.to_numpy()[nearest],
                            absolute_time_difference_s=differences.min(axis=1)))
    table.to_csv(ROOT/'results/tables/approximate_original_time_matches.csv',index=False)
    # Time proximity is only a candidate match: no identity or completeness claim.
    match=table[table.absolute_time_difference_s<=2]
    summary=dict(candidate_events=len(events),constraints_valid=True,
                 original_events=len(original),candidates_with_original_time_within_2s=len(match),
                 unique_original_events_with_candidate_time_within_2s=match.original_event_id.nunique(),
                 note='Time-only candidates; false detections and completeness unassessed',
                 minimum_depth_node_km=float(events.depth.min()),
                 fraction_at_minimum_depth_node=float((events.depth==events.depth.min()).mean()),
                 warning='Coarse depth nodes and many near-surface solutions limit depth interpretation')
    (ROOT/'results/tables/approximate_association_validation.json').write_text(json.dumps(summary,indent=2)+'\n')
    fig,axes=plt.subplots(1,3,figsize=(12,4),constrained_layout=True)
    points=axes[0].scatter(events.longitude,events.latitude,c=events.depth,s=8,cmap='viridis')
    axes[0].set_xlabel('Longitude');axes[0].set_ylabel('Latitude')
    axes[0].xaxis.set_major_locator(MaxNLocator(4))
    axes[0].xaxis.set_major_formatter(FormatStrFormatter('%.2f'))
    fig.colorbar(points,ax=axes[0],label='Approximate depth below sea level (km)')
    hours=(events.time-1529971200)/3600
    axes[1].hist(hours,bins=np.arange(25),histtype='step',label='associated candidates')
    axes[1].hist(original.utc_hour,bins=np.arange(25),histtype='step',label='original catalog')
    axes[1].legend(fontsize=8);axes[1].set_xlabel('Hour UTC');axes[1].set_ylabel('Events per hour')
    axes[2].hist(picks.residual,bins=np.linspace(-.5,.5,41))
    axes[2].set_xlabel('Arrival residual (s)');axes[2].set_ylabel('Assigned picks')
    fig.suptitle('Approximate 1-D association; no differential relocation or completeness estimate')
    for ext in ('pdf','png'):fig.savefig(ROOT/f'results/figures/approximate_association.{ext}',dpi=300)
    print(json.dumps(summary,indent=2))


if __name__ == '__main__':main()
