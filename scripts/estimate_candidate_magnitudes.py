#!/usr/bin/env python3
"""Approximate local magnitudes from actual unbandpassed Wood–Anderson records."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from obspy import read,read_inventory,Trace
from obspy.signal.invsim import WOODANDERSON
from obspy.geodetics import gps2dist_azimuth
from src.statistical_analysis.statistics import seismic_moment
ROOT=Path(__file__).resolve().parents[1]


def main():
    catalog=pd.read_csv(ROOT/'results/catalogs/candidate_classified_catalog.csv').set_index('idx')
    picks=pd.read_csv(ROOT/'results/catalogs/approximate_pick_assignments.csv')
    meta=pd.read_csv(ROOT/'results/tables/candidate_window_metadata.csv')
    eligible=set(zip(meta[meta.snr>=2].event_idx,meta[meta.snr>=2].station,meta[meta.snr>=2].component))
    inventory=read_inventory(ROOT/'data/raw/stations.xml');stream=read(ROOT/'data/raw/8G_20180626.mseed')
    rows=[]
    for trace in stream:
        component=trace.stats.channel[-1]
        if component not in 'NE':continue
        selected=picks[(picks.station==f'{trace.stats.network}.{trace.stats.station}.{trace.stats.location}')&(picks.phase=='S')]
        response=inventory.get_response(trace.id,trace.stats.starttime)
        evaluation=response.get_evalresp_response;cache={}
        def cached(delta,nfft,output='VEL',**kwargs):
            key=(delta,nfft,output)
            if key not in cache:cache[key]=evaluation(delta,nfft,output=output,**kwargs)
            return tuple(x.copy() for x in cache[key])
        response.get_evalresp_response=cached
        coordinates=inventory.get_coordinates(trace.id,trace.stats.starttime)
        fs=trace.stats.sampling_rate
        for pick in selected.itertuples():
            if (pick.event_idx,trace.stats.station,component) not in eligible:continue
            elapsed=pd.Timestamp(pick.peak_time_utc).timestamp()-float(trace.stats.starttime)
            center=round(elapsed*fs);half=round(32*fs)
            if elapsed<64 or elapsed>len(trace.data)/fs-64:continue
            block=Trace(trace.data[center-half:center+half].copy(),header=trace.stats.copy())
            block.stats.starttime=trace.stats.starttime+(center-half)/fs;block.stats.response=response
            block.detrend('linear')
            block.remove_response(output='VEL',pre_filt=(.5,1,22,24),water_level=None,taper=True,taper_fraction=.05)
            block.simulate(paz_simulate=WOODANDERSON,simulate_sensitivity=True,zero_mean=True,taper=True,taper_fraction=.05)
            start=round(elapsed*fs-(center-half)-fs)
            signal=block.data[start:start+round(5*fs)]
            amplitude_mm=float(np.ptp(signal)*1000)
            event=catalog.loc[pick.event_idx]
            distance=gps2dist_azimuth(event.latitude,event.longitude,coordinates['latitude'],coordinates['longitude'])[0]/1000
            if amplitude_mm<=0 or distance<=0:continue
            rows.append(dict(event_idx=pick.event_idx,station=trace.stats.station,component=component,peak_to_peak_mm=amplitude_mm,epicentral_distance_km=distance))
        print(trace.id,len(rows),'cumulative WA measurements',flush=True)
    components=pd.DataFrame(rows)
    components.to_csv(ROOT/'results/tables/candidate_wood_anderson_components.csv',index=False)
    stations=components.groupby(['event_idx','station']).agg(amplitude_pp_mm=('peak_to_peak_mm','mean'),horizontal_components=('component','nunique'),epicentral_distance_km=('epicentral_distance_km','first')).reset_index()
    stations=stations[stations.horizontal_components==2].copy()
    r=stations.epicentral_distance_km
    stations['local_magnitude']=np.log10(stations.amplitude_pp_mm)+np.log10(r/100)+.00301*(r-100)+3
    stations.to_csv(ROOT/'results/tables/candidate_station_magnitudes.csv',index=False)
    aggregate=stations.groupby('event_idx').local_magnitude.agg(['median','count','std']).rename(columns={'median':'approximate_ml','count':'magnitude_stations','std':'station_magnitude_std'})
    catalog=catalog.join(aggregate)
    catalog['approximate_moment_Nm']=seismic_moment(catalog.approximate_ml.to_numpy())
    catalog.reset_index().to_csv(ROOT/'results/catalogs/candidate_magnitude_catalog.csv',index=False)
    record=dict(events=int(catalog.approximate_ml.notna().sum()),total_candidates=len(catalog),
                wa_poles_rad_s=[[-6.283,4.7124],[-6.283,-4.7124]],wa_zeros=[0],wa_gain=1,wa_sensitivity=2080,
                amplitude='mean two horizontal peak-to-peak amplitudes in mm; require both components SNR>=2',
                event_magnitude='median station ML; published Bakun–Joyner equation with epicentral R in km',
                stabilization_prefilter_hz=[.5,1,22,24],additional_bandpass=None,window_relative_S_s=[-1,4],
                sensitivity_zero_to_peak_magnitude_shift=float(-np.log10(2)),sensitivity_2800_gain_magnitude_shift=float(np.log10(2800/2080)),
                limitations=['Approximate epicentral locations','Source Wood–Anderson sensitivity and amplitude units unspecified',
                             'Peak-to-peak convention follows supplement; standard zero-to-peak convention differs',
                             'No source clipping/spike quality-control implementation available','Independent response stabilization and SNR gate',
                             'Seismic moment uses published empirical ML-to-Mw relation, not spectral moment inversion'])
    (ROOT/'results/tables/candidate_magnitude_execution.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))

if __name__=='__main__':main()
