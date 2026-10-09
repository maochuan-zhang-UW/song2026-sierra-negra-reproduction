#!/usr/bin/env python3
"""Pick additional EC records on common gap-free segments; never fill gaps."""
import hashlib,json,time
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from obspy import read,read_inventory,UTCDateTime,Stream
import seisbench.models as sbm
from src.earthquake_detection.volpick import pick_stream

ROOT=Path(__file__).resolve().parents[1]


def common_segments(stream):
    stream=stream.copy().merge(method=0,fill_value=None).split()
    components='ZNE'
    boundaries=sorted(set(float(t) for tr in stream for t in [tr.stats.starttime,tr.stats.endtime+tr.stats.delta]))
    result=[]
    for a,b in zip(boundaries[:-1],boundaries[1:]):
        if b-a<60-1e-6:continue
        selected=[]
        for component in components:
            options=[tr for tr in stream.select(component=component)
                     if float(tr.stats.starttime)<=a+1e-6 and float(tr.stats.endtime+tr.stats.delta)>=b-1e-6]
            if len(options)!=1:break
            selected.append(options[0].slice(UTCDateTime(a),UTCDateTime(b)-options[0].stats.delta))
        if len(selected)==3:result.append(Stream(selected))
    return result


def main():
    torch.set_num_threads(8);model=sbm.EQTransformer.from_pretrained('volpick');model.eval()
    source=ROOT/'data/raw/EC_20180626.mseed';stream=read(source)
    inventory=read_inventory(ROOT/'data/raw/EC_responses.xml')
    for trace in stream:
        component=trace.stats.channel[-1]
        orientation=inventory.get_orientation(trace.id,trace.stats.starttime)
        if component in '12':
            expected=0 if component=='1' else 90
            if abs(orientation['azimuth']-expected)>1e-6 or abs(orientation['dip'])>1e-6:
                raise ValueError('Cannot alias unverified horizontal orientation')
            trace.stats.channel=trace.stats.channel[:-1]+('N' if component=='1' else 'E')
    origin=UTCDateTime('2018-06-26');rows=[];runs=[];started=time.monotonic()
    for station in sorted(set(tr.stats.station for tr in stream)):
        for hour in range(24):
            a=origin+hour*3600;b=a+3600
            segments=common_segments(stream.select(station=station).slice(a-30,b+30))
            kept=0
            for segment in segments:
                for trace in segment:
                    if trace.stats.sampling_rate!=100:raise ValueError('Expected native 100 Hz')
                    trace.detrend('linear');trace.detrend('demean')
                    trace.filter('bandpass',freqmin=2,freqmax=12,corners=4,zerophase=False)
                for pick in pick_stream(segment,.2,.2,model=model):
                    if not a<=pick.peak_time<b:continue
                    rows.append(dict(trace_id=pick.trace_id,phase=pick.phase,peak_time_utc=str(pick.peak_time),
                                     start_time_utc=str(pick.start_time),end_time_utc=str(pick.end_time),
                                     peak_probability=float(pick.peak_value)))
                    kept+=1
            runs.append(dict(station=station,hour=hour,common_segments=len(segments),picks=kept))
            print(station,hour,kept,'picks',flush=True)
    frame=pd.DataFrame(rows)
    if frame.duplicated(['trace_id','phase','peak_time_utc']).any():raise ValueError('Duplicate picks')
    frame.to_csv(ROOT/'results/catalogs/ec_volpick_picks.csv',index=False)
    combined=pd.concat([pd.read_csv(ROOT/'results/catalogs/volpick_picks.csv'),frame],ignore_index=True).sort_values('peak_time_utc')
    combined.to_csv(ROOT/'results/catalogs/combined_volpick_picks.csv',index=False)
    record=dict(status='complete',phase_counts=frame.phase.value_counts().to_dict(),runs=runs,
                elapsed_s=time.monotonic()-started,input_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                horizontal_aliases='HH1 -> HHN and HH2 -> HHE, verified 0/90 degree horizontal StationXML orientation',
                gap_policy='common finite three-component segments >=60 s; no interpolation',
                processing='same public Volpick checkpoint, 0.2 thresholds, 60-s windows and 50% overlap as 8G run',
                limitations='SN02 gaps and five-second model blind edges at each segment remain; VCH1 skipped')
    (ROOT/'results/tables/ec_volpick_execution.json').write_text(json.dumps(record,indent=2)+'\n')


if __name__=='__main__':main()
