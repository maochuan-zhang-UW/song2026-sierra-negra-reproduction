#!/usr/bin/env python3
"""Response-correct continuous hour blocks with real 30-s padding each side."""
import json,multiprocessing
from pathlib import Path
import numpy as np
from obspy import read,read_inventory,Trace
from src.data_processing.waveforms import preprocess

ROOT=Path(__file__).resolve().parents[1]
TRACES={};INVENTORY=None


def channel_blocks(identifier):
    trace=TRACES[identifier];fs=trace.stats.sampling_rate
    response=INVENTORY.get_response(trace.id,trace.stats.starttime)
    original=response.get_evalresp_response;cache={}
    def cached(delta,nfft,output='VEL',**kwargs):
        key=(delta,nfft,output)
        if key not in cache:cache[key]=original(delta,nfft,output=output,**kwargs)
        return tuple(x.copy() for x in cache[key])
    response.get_evalresp_response=cached
    records=[]
    for hour in range(24):
        start=max(0,hour*3600-30);end=min(86400,(hour+1)*3600+30)
        block=Trace(trace.data[round(start*fs):round(end*fs)].copy(),header=trace.stats.copy())
        block.stats.starttime=trace.stats.starttime+start;block.stats.response=response
        block.detrend('linear')
        block.remove_response(output='VEL',pre_filt=(.5,1,22,24),water_level=None,taper=True,taper_fraction=.01)
        data=preprocess(block.data,fs,4,True,target_rate=50,band=(2,20))
        key=trace.stats.station+'.'+trace.stats.channel[-1]
        destination=ROOT/f'.cache/matching_velocity/hour_{hour:02d}';destination.mkdir(parents=True,exist_ok=True)
        np.save(destination/(key+'.npy'),data)
        records.append(dict(hour=hour,channel=key,start_offset_s=start,samples=len(data),sampling_rate=50))
    print(identifier,'24 padded hour blocks',flush=True)
    return records


def main():
    global TRACES,INVENTORY
    TRACES={t.id:t for t in read(ROOT/'data/raw/8G_20180626.mseed')}
    INVENTORY=read_inventory(ROOT/'data/raw/stations.xml')
    with multiprocessing.get_context('fork').Pool(8) as pool:
        records=sum(pool.map(channel_blocks,list(TRACES)),[])
    import pandas as pd
    pd.DataFrame(records).to_csv(ROOT/'results/tables/matching_velocity_blocks.csv',index=False)
    settings=dict(sample_rate_hz=50,band_hz=[2,20],prefilter_hz=[.5,1,22,24],filter_order=4,zero_phase=True,
                  response='VEL, no water level',block_origin_duration_s=3600,real_padding_s=30,
                  response_taper_fraction=.01,workers=8,
                  note='Independent response settings; hour blocks have 30 seconds real context on each side, clipped at day edges')
    (ROOT/'results/tables/matching_preprocessing.json').write_text(json.dumps(settings,indent=2)+'\n')


if __name__=='__main__':main()
