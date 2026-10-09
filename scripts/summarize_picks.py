#!/usr/bin/env python3
"""Summarize actually executed candidate phase picks, separately from earthquakes."""
import json,hashlib,csv
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from src.visualization.figures import save
ROOT=Path(__file__).resolve().parents[1]
meta=json.loads((ROOT/'results/tables/volpick_execution.json').read_text())
if meta['status']!='complete':raise SystemExit('Wait for completed picking before summarizing')
picks=pd.read_csv(ROOT/'results/catalogs/volpick_picks.csv')
picks['peak_time_utc']=pd.to_datetime(picks.peak_time_utc,utc=True,format="ISO8601")
picks=picks.sort_values(['peak_time_utc','trace_id','phase'])
picks.to_csv(ROOT/'results/catalogs/volpick_picks.csv',index=False,date_format="%Y-%m-%dT%H:%M:%S.%fZ")
picks['hour_utc']=picks.peak_time_utc.dt.hour
hourly=picks.groupby(['hour_utc','phase']).size().unstack(fill_value=0).reindex(range(24),fill_value=0)
hourly.to_csv(ROOT/'results/tables/candidate_pick_hourly_counts.csv')
station=picks.groupby(['trace_id','phase']).size().unstack(fill_value=0)
station.to_csv(ROOT/'results/tables/candidate_pick_station_counts.csv')
fig,axes=plt.subplots(2,1,figsize=(9,7))
hourly.plot(ax=axes[0],marker='o');axes[0].set(xlabel='Hour UTC on 26 June 2018',ylabel='Candidate phase picks',xlim=(0,23))
station.plot.bar(ax=axes[1]);axes[1].set(xlabel='Acquired station',ylabel='Candidate phase picks')
fig.suptitle('Public Volpick execution: seven 8G stations; picks are not earthquakes')
fig.tight_layout();save(fig,ROOT/'results/figures/phase_pick_counts')
checkpoint={}
for p in (ROOT/'.cache/seisbench/models/v3/eqtransformer').glob('volpick*'):
    checkpoint[p.name]=dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    if '.json' in p.name:checkpoint[p.name]['config']=json.loads(p.read_text())
(ROOT/'results/tables/volpick_checkpoint.json').write_text(json.dumps(checkpoint,indent=2)+'\n')
comparison=ROOT/'results/tables/comparison.csv'
with comparison.open() as f:rows=list(csv.DictReader(f))
rows=[r for r in rows if not r['quantity'].startswith('Candidate ')]
counts=picks.phase.value_counts().to_dict()
for phase,published in [('P',13144),('S',12196)]:
    actual=int(counts.get(phase,0))
    rows.append(dict(quantity='Candidate '+phase+' picks',published_value=published,reproduced_value=actual,
                     difference=actual-published,explanation='Seven acquired 8G stations only; exact original checkpoint unverified; independent filtering/edge/stacking choices. Not associated arrivals or earthquake counts.'))
with comparison.open('w') as f:
    writer=csv.DictWriter(f,fieldnames=['quantity','published_value','reproduced_value','difference','explanation'],lineterminator='\n');writer.writeheader();writer.writerows(rows)
print(json.dumps(dict(candidate_phase_counts=counts,stations=len(station),processed_station_hours=len(meta['runs']),elapsed_seconds=meta['elapsed_seconds']),indent=2))
