#!/usr/bin/env python3
"""Execute available catalog analyses; missing waveform results remain null."""
import argparse,csv,hashlib,json,platform
from pathlib import Path
import numpy as np
from src.data_processing.catalog import read_eventlist,validate_catalog,phase_boundary_sensitivity
from src.visualization.figures import catalog_figures,conceptual_figure
ROOT=Path(__file__).resolve().parents[1]


def run(path):
    df=read_eventlist(path);validate_catalog(df)
    df.to_csv(str(ROOT/'results/catalogs/original_20180626.csv'),index=False)
    boundaries=np.array([0,9.25,17,19+40/60,24])
    rows=[]
    for i,(a,b) in enumerate(zip(boundaries[:-1],boundaries[1:]),1):
        sub=df[df.phase==i]
        rows.append(dict(phase=i,start_hour_utc=a,end_hour_utc=b,event_count=len(sub),
                         duration_hours=b-a,rate_per_hour=len(sub)/(b-a),
                         median_magnitude=float(sub.magnitude.median())))
    import pandas as pd
    pd.DataFrame(rows).to_csv(str(ROOT/'results/tables/original_phase_statistics.csv'),index=False)
    shock=df.loc[df.magnitude.idxmax()]
    stats=dict(n_original_events=len(df),minimum_magnitude=float(df.magnitude.min()),
               maximum_magnitude=float(df.magnitude.max()),median_magnitude=float(df.magnitude.median()),
               maximum_magnitude_event_id=shock.event_id,maximum_magnitude_event_utc=str(shock.origin_time),
               original_depth_reference='Not verified; preserve source values; do not interpret as below surface',
               phase_counts={str(i):int((df.phase==i).sum()) for i in range(1,5)},
               note='No enhanced events, LP/VT labels, families, or GNSS solutions were computed')
    (ROOT/'results/tables/summary.json').write_text(json.dumps(stats,indent=2)+'\n')
    comparison=[
        ('Located machine-learning events','694',None,'Waveforms, model inference, association and relocation not executed'),
        ('Templates','669',None,'Template selections unavailable'),
        ('Additional template detections','1241',None,'Continuous waveforms unavailable locally'),
        ('Enhanced total (694+1241)','1935',None,'219 original events are not an enhanced reproduction'),
        ('VT events (Results)','1224',None,'Results and Methods disagree by 10 VT events'),
        ('VT events (Methods)','1214',None,'Methods sum with 711 LP is 1925, not 1935'),
        ('LP events','711',None,'No FI windows available'),
        ('Families / member events','29 / 714',None,'No waveform similarities computed for observations'),
        ('Phase-2 LP families','5',None,'Membership unavailable'),
        ('Anticorrelated LP pairs','11',None,'Manual inspection and waveforms required'),
        ('VT moment/recurrence R squared','0.70',None,'Family data and regression convention unavailable'),
        ('LP moment/recurrence R squared','0.07',None,'Family data and regression convention unavailable'),
        ('Recurrence/periodicity Pearson r','0.03',None,'Family times unavailable'),
        ('TDF earthquake UTC (minute precision)','09:15','09:15:32.299','Original maximum-magnitude event; nominal difference +32.299 seconds'),
        ('Magma intrusion UTC','~17:00',None,'Timeline annotation from publication, not independently measured'),
        ('Eruption UTC','19:35-19:40',None,'Publication timing range; no tremor processed')]
    with (ROOT/'results/tables/comparison.csv').open('w') as f:
        writer=csv.writer(f);writer.writerow(['quantity','published_value','reproduced_value','difference','explanation'])
        for q,p,r,e in comparison:writer.writerow([q,p,'' if r is None else r,'not computed' if r is None else '+32.299 s',e])
    phase_boundary_sensitivity(df).to_csv(str(ROOT/'results/tables/phase_boundary_sensitivity.csv'),index=False)
    catalog_figures(df,ROOT/'results/figures');conceptual_figure(ROOT/'results/figures')
    provenance=dict(source_url='https://zenodo.org/records/4389190/files/IGUANA_Cat_V1.eventlist?download=1',
                    source_doi='10.5281/zenodo.4389190',source_publication='Bell et al. (2021)',
                    recovery='Browser text, complete consecutive source rows 348-566 inclusive; neighboring rows 347 and 567 are other dates',
                    input_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                    full_archive_md5='8935d6cc8189ff1991ba966666aacd66',
                    full_archive_checksum_verified=False,subset_event_count=len(df),
                    limitation='Browser recovery is not byte-identical archival download; full MD5 awaits network access',
                    python=platform.python_version(),numpy=np.__version__)
    (ROOT/'results/tables/catalog_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print(json.dumps(stats,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--catalog',type=Path);args=parser.parse_args()
    choices=[args.catalog] if args.catalog else [ROOT/'data/raw/IGUANA_Cat_V1.eventlist',ROOT/'data/IGUANA_20180626.eventlist']
    path=next((p for p in choices if p and p.exists()),None)
    if path is None:
        raise SystemExit('No raw catalog: run scripts/acquire.py or rebuild from the committed original CSV with scripts/rebuild_from_csv.py')
    run(path)
