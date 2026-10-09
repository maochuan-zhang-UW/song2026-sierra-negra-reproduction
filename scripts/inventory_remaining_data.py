#!/usr/bin/env python3
"""Validate additional acquired records; inventory gaps without filling them."""
import hashlib,json,re
from pathlib import Path
import numpy as np
import pandas as pd
from obspy import read,read_inventory,UTCDateTime
from src.visualization.figures import save
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
raw=ROOT/'data/raw';tables=ROOT/'results/tables'
origin=UTCDateTime('2018-06-26');end=origin+86400-.01
stream=read(str(raw/'8G_20180626.mseed'))+read(str(raw/'EC_20180626.mseed'))
stream.trim(origin,end);stream.merge(method=0,fill_value=None)
coverage=[]
for tr in stream:
    if tr.stats.sampling_rate!=100:raise ValueError('Unexpected sample rate')
    coverage.append(dict(channel_id=tr.id,observed_seconds=np.ma.count(tr.data)/100,
                         day_fraction=np.ma.count(tr.data)/8640000))
pd.DataFrame(coverage).to_csv(tables/'acquired_waveform_coverage.csv',index=False)
station_coverage=[]
for network,station in sorted(set((t.stats.network,t.stats.station) for t in stream)):
    selected=stream.select(network=network,station=station)
    if len(selected)!=3:raise ValueError('Expected three acquired channels')
    if any(t.stats.starttime!=origin or t.stats.npts!=8640000 for t in selected):
        raise ValueError('Daily sample grids differ')
    valid=np.logical_and.reduce([~np.ma.getmaskarray(t.data) for t in selected])
    station_coverage.append(dict(network=network,station=station,
                                 common_three_component_seconds=int(valid.sum())/100,
                                 common_day_fraction=float(valid.mean())))
pd.DataFrame(station_coverage).to_csv(tables/'acquired_station_coverage.csv',index=False)
inv=read_inventory(str(raw/'stations.xml'))+read_inventory(str(raw/'EC_responses.xml'))
stations=[];orientations=[]
for network in inv:
    for station in network:
        stations.append(dict(network=network.code,station=station.code,latitude=station.latitude,
                             longitude=station.longitude,elevation_m=station.elevation))
        for channel in station:
            key='{}.{}.{}.{}'.format(network.code,station.code,channel.location_code,channel.code)
            if key in {t.id for t in stream}:
                orientations.append(dict(channel_id=key,azimuth_degrees=channel.azimuth,
                                         dip_degrees=channel.dip,metadata_source='EarthScope FDSN StationXML'))
pd.DataFrame(stations).to_csv(tables/'acquired_station_metadata.csv',index=False)
pd.DataFrame(orientations).to_csv(tables/'acquired_channel_orientations.csv',index=False)
gnss=[]
for code,doi in [('GV03','10.7283/MEWP-QZ75'),('GV09','10.7283/XZAA-W505')]:
    text=(raw/(code+'_doi.html')).read_text()
    match=re.search(r'Point\(s\) \(Lat Lon\):\s*(-?[\d.]+)\s+(-?[\d.]+)',text)
    if match is None:raise ValueError('GNSS coordinates not found')
    gnss.append(dict(station=code,latitude=float(match[1]),longitude=float(match[2]),
                     provenance='https://www.unavco.org/data/doi/'+doi,
                     coordinate_note='Rounded DOI landing-page coordinates; datum not independently verified'))
pd.DataFrame(gnss).to_csv(tables/'gnss_station_coordinates.csv',index=False)
source=raw/'VCH1_Cat_v1.txt';expected='6260c8ddf90ecb9dfe0a946193dc2ec3'
if hashlib.md5(source.read_bytes()).hexdigest()!=expected:raise ValueError('VCH1 archive checksum differs')
cat=pd.read_csv(source,sep=r'\s+')
sub=cat[cat.DATE=='2018-06-26'].copy()
sub['source_row']=sub.index+2
sub['provenance']='Bell archive VCH1 catalog; separate from located IGUANA catalog'
sub.to_csv(ROOT/'results/catalogs/vch1_original_20180626.csv',index=False)
if not np.isfinite(sub.MAG).all():raise ValueError('Invalid VCH1 magnitudes')

catalog=pd.read_csv(ROOT/'results/catalogs/original_20180626.csv')
fig,ax=plt.subplots(figsize=(7,7))
points=ax.scatter(catalog.longitude,catalog.latitude,c=catalog.utc_hour,s=12,cmap='viridis',vmin=0,vmax=24)
acquired={(t.stats.network,t.stats.station) for t in stream}
for row in stations:
    present=(row['network'],row['station']) in acquired
    ax.scatter(row['longitude'],row['latitude'],marker='v',s=50,
               facecolor='black' if present else 'white',edgecolor='black')
    ax.annotate(row['station'],(row['longitude'],row['latitude']),xytext=(3,3),textcoords='offset points',fontsize=8)
for row in gnss:
    ax.scatter(row['longitude'],row['latitude'],marker='s',s=60,facecolor='white',edgecolor='red')
    ax.annotate(row['station'],(row['longitude'],row['latitude']),xytext=(3,-10),textcoords='offset points',color='red',fontsize=8)
ax.set(xlim=(-91.22,-90.96),ylim=(-.89,-.60),xlabel='Longitude (degrees east)',ylabel='Latitude (degrees north)',
       title='Original events and verified station metadata')
ax.set_aspect(1/np.cos(np.deg2rad(-.8)))
ax.text(.02,.02,'Filled triangles: acquired seismic records\nOpen triangles: metadata only\nRed squares: GNSS DOI coordinates',transform=ax.transAxes,fontsize=8)
fig.colorbar(points,ax=ax,label='Hour UTC on 26 June 2018')
save(fig,ROOT/'results/figures/fig01_all_stations')
checks={}
for name in ['EC_20180626.mseed','EC_responses.xml','VCH1_Cat_v1.txt','gnss_doi.html','GV03_doi.html','GV09_doi.html']:
    p=raw/name;checks[name]=dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
summary=dict(acquired_station_count=len(station_coverage),acquired_channel_count=len(stream),
             station_coverage=station_coverage,vch1_full_file_md5_verified=True,
             vch1_date_event_count=len(sub),files=checks,
             note='Additional data retrieval and inventory only; existing 8G-only candidate picks are unchanged. EC orientation aliases and common-component gaps require explicit handling before picking.')
(tables/'remaining_data_inventory.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:summary[k] for k in ['acquired_station_count','acquired_channel_count','vch1_date_event_count','station_coverage']},indent=2))
