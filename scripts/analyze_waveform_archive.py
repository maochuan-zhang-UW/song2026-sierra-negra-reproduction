#!/usr/bin/env python3
"""Inventory actual waveforms and reproduce PAYG day plots from response metadata."""
import json, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from obspy import read, read_inventory, UTCDateTime
from src.visualization.figures import save
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
raw=ROOT/'data/raw'


def main():
    stream=read(str(raw/'8G_20180626.mseed'))
    rows=[]
    for trace in stream:
        s=trace.stats
        rows.append(dict(channel_id=trace.id,start_utc=str(s.starttime),end_utc=str(s.endtime),
                         sample_rate_hz=s.sampling_rate,sample_count=s.npts,
                         duration_seconds=s.npts/s.sampling_rate))
    pd.DataFrame(rows).to_csv(ROOT/'results/tables/waveform_segments.csv',index=False)
    coverage=[]
    for channel in sorted(set(t.id for t in stream)):
        selected=stream.select(id=channel).slice(UTCDateTime('2018-06-26'),UTCDateTime('2018-06-27')-.01)
        # Merge overlaps only; do not interpolate or replace missing samples.
        selected.merge(method=0,fill_value=None)
        n=sum(int(np.ma.count(t.data)) for t in selected)
        fs=selected[0].stats.sampling_rate
        coverage.append(dict(channel_id=channel,sample_rate_hz=fs,
                             observed_seconds=n/fs,day_fraction=n/fs/86400))
    pd.DataFrame(coverage).to_csv(ROOT/'results/tables/waveform_coverage.csv',index=False)
    inv=read_inventory(str(raw/'stations.xml'))
    stations=[]
    for net in inv:
        for station in net:
            stations.append(dict(network=net.code,station=station.code,latitude=station.latitude,
                                 longitude=station.longitude,elevation_m=station.elevation))
    pd.DataFrame(stations).to_csv(ROOT/'results/tables/stations.csv',index=False)
    # Separate map with actual metadata; no inferred fault/terrain layers.
    catalog=pd.read_csv(ROOT/'results/catalogs/original_20180626.csv')
    fig,ax=plt.subplots(figsize=(7,6))
    scatter=ax.scatter(catalog.longitude,catalog.latitude,c=catalog.utc_hour,s=12,vmin=0,vmax=24,cmap='viridis')
    for station in stations:
        ax.scatter(station['longitude'],station['latitude'],marker='v',color='black',s=45)
        ax.annotate(station['station'],(station['longitude'],station['latitude']),xytext=(3,3),textcoords='offset points',fontsize=8)
    ax.set(xlim=(-91.22,-91.06),ylim=(-.89,-.60),xlabel='Longitude (degrees east)',ylabel='Latitude (degrees north)',
           title='Original events and archived 8G station metadata')
    ax.set_aspect(1/np.cos(np.deg2rad(-.8)))
    fig.colorbar(scatter,ax=ax,label='Hour UTC on 26 June 2018')
    save(fig,ROOT/'results/figures/fig01_stations')

    dates=['2018-06-26','2005-10-22','2005-04-16','1999-12-22']
    response=read_inventory(str(raw/'PAYG_stations.xml'))
    fig,axes=plt.subplots(2,2,figsize=(12,9),sharex=True,sharey=True)
    processing=[]
    for date,ax in zip(dates,axes.flat):
        st=read(str(raw/('PAYG_'+date+'.mseed')))
        st.merge(method=0,fill_value=None)
        gaps=st.get_gaps()
        # Process contiguous segments independently, with no artificial gap filling.
        st=st.split()
        for tr in st:
            tr.detrend('linear');tr.detrend('demean')
            tr.remove_response(inventory=response,output='VEL',pre_filt=(.01,.02,8,9),water_level=None)
        scale=float(np.percentile(np.concatenate([np.abs(t.data) for t in st]),99))
        origin=UTCDateTime(date)
        for row in range(48):
            ax.axhline(row,color='0.8',linewidth=.3,zorder=0)
            window=st.slice(origin+row*1800,origin+(row+1)*1800-0.001)
            for tr in window:
                # Min/max per one-second bin preserves short earthquake peaks.
                fs=tr.stats.sampling_rate; size=int(round(fs))
                n=len(tr.data)//size
                if not n: continue
                samples=tr.data[:n*size].reshape(n,size)
                lo=samples.min(axis=1);hi=samples.max(axis=1)
                minute=((tr.stats.starttime-origin-row*1800)+np.arange(n))/60
                ax.vlines(minute,row-.4*hi/scale,row-.4*lo/scale,
                          color=['black','red','green','blue'][row%4],linewidth=.35,rasterized=True)
        ax.set_title('IU.PAYG.00.BHZ '+date,fontsize=10)
        ax.set(xlim=(0,30),ylim=(48,-1),xticks=np.arange(0,31,5),yticks=np.arange(0,49,10),
               yticklabels=['{:02d}:00'.format(h) for h in range(0,25,5)],xlabel='Minute within each 30-minute row',ylabel='UTC')
        ax.text(.02,.02,'Scale: {:.2g} m/s per 0.4 row'.format(scale),transform=ax.transAxes,fontsize=8)
        processing.append(dict(date=date,velocity_scale_m_per_s=scale,pre_filter_hz=[.01,.02,8,9],
                               water_level=None,display_scale_percentile=99,observed_seconds=sum(t.stats.npts/t.stats.sampling_rate for t in st),gaps=gaps))
    fig.suptitle('Supplementary Figure 5: independently processed PAYG ground velocity',fontsize=12)
    fig.tight_layout();save(fig,ROOT/'results/figures/figS05_payg_dayplots')
    (ROOT/'results/tables/payg_processing.json').write_text(json.dumps(processing,indent=2,default=str)+'\n')
    sources={}
    for p in sorted(raw.iterdir()):
        if p.is_file() and p.suffix in ('.mseed','.xml','.pdf','.eventlist','.json'):
            sources[p.name]=dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    (ROOT/'results/tables/raw_file_checksums.json').write_text(json.dumps(sources,indent=2)+'\n')
    print('Inventory:',len(rows),'segments;',len(coverage),'channels. PAYG:',len(processing),'days.')


if __name__=='__main__':main()
