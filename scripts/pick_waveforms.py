#!/usr/bin/env python3
"""Run the public Volpick model on actual 8G records; output picks, not events."""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from obspy import read,UTCDateTime
import seisbench.models as sbm
from src.earthquake_detection.volpick import pick_stream
ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--station',default='*')
    parser.add_argument('--start-hour',type=int,default=0)
    parser.add_argument('--end-hour',type=int,default=24)
    parser.add_argument('--threads',type=int,default=8)
    args=parser.parse_args()
    torch.set_num_threads(args.threads)
    model=sbm.EQTransformer.from_pretrained('volpick')
    model.eval()
    print('Public model loaded; processing',args.station,flush=True)
    source=ROOT/'data/raw/8G_20180626.mseed'
    stream=read(str(source)).select(station=args.station)
    stations=sorted(set(t.stats.station for t in stream))
    if not stations:raise ValueError('No requested stations')
    origin=UTCDateTime('2018-06-26')
    rows=[];runs=[]
    dest=ROOT/'results/catalogs/volpick_picks.csv'
    start=time.monotonic()
    source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
    for station in stations:
        for hour in range(args.start_hour,args.end_hour):
            a=origin+hour*3600;b=a+3600
            # Padding retains picker context; each peak belongs to one half-open hour.
            st=stream.select(station=station).slice(a-30,b+30)
            st.merge(method=0,fill_value=None)
            st=st.split()
            if not len(st):
                runs.append(dict(station=station,hour=hour,status='no_data'));continue
            for tr in st:
                tr.detrend('linear');tr.detrend('demean')
                # Archived 8G records are already 100 Hz. Refuse untested resampling.
                if tr.stats.sampling_rate!=100:raise ValueError('Expected 100 Hz 8G data')
                tr.filter('bandpass',freqmin=2,freqmax=12,corners=4,zerophase=False)
            picks=pick_stream(st,.2,.2,model=model)
            kept=0
            for pick in picks:
                if not a<=pick.peak_time<b:continue
                rows.append(dict(trace_id=pick.trace_id,phase=pick.phase,
                                 peak_time_utc=str(pick.peak_time),start_time_utc=str(pick.start_time),
                                 end_time_utc=str(pick.end_time),peak_probability=float(pick.peak_value)))
                kept+=1
            runs.append(dict(station=station,hour=hour,status='processed',picks=kept))
            pd.DataFrame(rows,columns=['trace_id','phase','peak_time_utc','start_time_utc','end_time_utc','peak_probability']).to_csv(dest,index=False)
            (ROOT/'results/tables/volpick_execution.json').write_text(json.dumps(dict(
                status='in_progress',runs=runs,model='EQTransformer.from_pretrained(volpick)',
                inference='Direct model pre/forward/post; average finite overlap; SeisBench picks_from_annotations',
                model_default_args=model.default_args,model_args=model.get_model_args(),
                input_sha256=source_hash,
                settings=dict(P_threshold=.2,S_threshold=.2,overlap_samples=3000,batch_size=64,
                              filter_hz=[2,12],filter_corners=4,filter_zero_phase=False,
                              blinding=[500,500],stacking='avg',threads=args.threads),
                deviations='Public checkpoint version not established as Song checkpoint; filter order/phase, normalization, edge blinding and stacking not specified by supplement. No association or relocation performed.',
                elapsed_seconds=time.monotonic()-start),indent=2,default=str)+'\n')
            print(station,hour,kept,'picks',flush=True)
    metadata=json.loads((ROOT/'results/tables/volpick_execution.json').read_text())
    metadata.update(status='complete',pick_count=len(rows),phase_counts=pd.DataFrame(rows).phase.value_counts().to_dict())
    (ROOT/'results/tables/volpick_execution.json').write_text(json.dumps(metadata,indent=2)+'\n')


if __name__=='__main__':main()
