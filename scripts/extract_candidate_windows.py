#!/usr/bin/env python3
"""Extract real response-corrected P/Z and S/horizontal candidate windows."""
import hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd
from obspy import read,read_inventory,Trace
from src.data_processing.waveforms import preprocess,arrival_window

ROOT=Path(__file__).resolve().parents[1]


def main():
    picks=pd.read_csv(ROOT/'results/catalogs/approximate_pick_assignments.csv')
    inventory=read_inventory(ROOT/'data/raw/stations.xml')
    stream=read(ROOT/'data/raw/8G_20180626.mseed')
    destination=ROOT/'.cache/candidate_windows';destination.mkdir(exist_ok=True)
    arrays={};rows=[];padding_checks=[]
    for trace in stream:
        station=f'{trace.stats.network}.{trace.stats.station}.{trace.stats.location}'
        component=trace.stats.channel[-1]
        if component not in 'ZNE':raise ValueError('Unexpected component orientation')
        phase='P' if component=='Z' else 'S'
        selected=picks[(picks.station==station)&(picks.phase==phase)]
        # Cache exactly the same evalresp grid for repeated equal-length blocks.
        response=inventory.get_response(trace.id,trace.stats.starttime)
        original_evaluation=response.get_evalresp_response
        cache={}
        def cached_evaluation(delta,nfft,output='VEL',**kwargs):
            key=(delta,nfft,output)
            if key not in cache:
                cache[key]=original_evaluation(delta,nfft,output=output,**kwargs)
            return tuple(x.copy() for x in cache[key])
        response.get_evalresp_response=cached_evaluation
        fs=trace.stats.sampling_rate
        def padded_velocity(elapsed,halfwidth):
            center=round(elapsed*fs);half=round(halfwidth*fs)
            block=Trace(trace.data[center-half:center+half].copy(),header=trace.stats.copy())
            if len(block.data)!=2*half:raise ValueError('Incomplete padded context')
            block.stats.starttime=trace.stats.starttime+(center-half)/fs
            block.stats.response=response
            block.detrend('linear')
            block.remove_response(output='VEL',pre_filt=(.5,1,22,24),water_level=None,
                                  taper=True,taper_fraction=.05)
            processed=preprocess(block.data,fs,order=4,zero_phase=True,target_rate=50,band=(2,20))
            sample=(elapsed*fs-(center-half))*50/fs
            return processed,sample
        for pick in selected.itertuples():
            elapsed=pd.Timestamp(pick.peak_time_utc).timestamp()-float(trace.stats.starttime)
            if elapsed<64 or elapsed>len(trace.data)/fs-64:continue
            data,sample=padded_velocity(elapsed,32)
            signal=arrival_window(data,50,sample,1,5)
            noise=arrival_window(data,50,sample,11,5)
            near_noise=arrival_window(data,50,sample,6,5)
            rms=lambda x:float(np.sqrt(np.mean((x-x.mean())**2)))
            snr=rms(signal)/rms(noise) if rms(noise)>0 else np.nan
            snr_near=rms(signal)/rms(near_noise) if rms(near_noise)>0 else np.nan
            key=f'candidate_{pick.event_idx:04d}__{trace.stats.station}.{component}.{phase}'
            if len(padding_checks)<63 and len([r for r in padding_checks if r['channel']==trace.id])<3:
                alternate,alternate_sample=padded_velocity(elapsed,64)
                longer=arrival_window(alternate,50,alternate_sample,1,5)
                from src.earthquake_classification.frequency import frequency_index
                padding_checks.append(dict(channel=trace.id,key=key,ncc_64_vs_128=float(np.corrcoef(signal,longer)[0,1]),
                                           fi_difference=float(frequency_index(signal,50)-frequency_index(longer,50))))
            arrays[key]=signal.astype('float32')
            rows.append(dict(key=key,event_idx=pick.event_idx,station=trace.stats.station,
                             component=component,phase=phase,sampling_rate=50,snr=snr,
                             snr_near_noise=snr_near,pick_time_utc=pick.peak_time_utc,units='m/s'))
        print(trace.id,len(selected),'assigned windows',flush=True)
    np.savez_compressed(destination/'windows.npz',**arrays)
    pd.DataFrame(padding_checks).to_csv(ROOT/'results/tables/candidate_padding_validation.csv',index=False)
    pd.DataFrame(rows).to_csv(ROOT/'results/tables/candidate_window_metadata.csv',index=False)
    settings=dict(windows=len(rows),sample_rate_hz=50,band_hz=[2,20],filter_order=4,
                  zero_phase=True,response_output='VEL',response_prefilter_hz=[.5,1,22,24],
                  water_level=None,day_end_exclusion_s=64,context_duration_s=64,response_taper_fraction=.05,window_relative_arrival_s=[-1,4],
                  noise_relative_arrival_s=[-11,-6],alternative_noise_s=[-6,-1],
                  snr='demeaned signal RMS / demeaned noise RMS',
                  waveform_sha256=hashlib.sha256((ROOT/'data/raw/8G_20180626.mseed').read_bytes()).hexdigest(),
                  note='Independent response stabilization, filter order, noise/SNR convention; no magnitudes estimated')
    (ROOT/'results/tables/candidate_window_processing.json').write_text(json.dumps(settings,indent=2)+'\n')


if __name__=='__main__':main()
