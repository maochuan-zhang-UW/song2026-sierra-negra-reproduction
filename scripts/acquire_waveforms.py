#!/usr/bin/env python3
"""One-hour chunks, response metadata, no raw data committed. Requires ObsPy.
Downloads IGUANA only; IGEPN EC data require the provider's separate access route.
"""
from pathlib import Path
import hashlib,json
from obspy import UTCDateTime
from obspy.clients.fdsn import Client
ROOT=Path(__file__).resolve().parents[1]
client=Client('IRIS');start=UTCDateTime('2018-06-26');end=start+86400
raw=ROOT/'data/raw/waveforms';raw.mkdir(parents=True,exist_ok=True)
inv=client.get_stations(network='8G',station='*',channel='*',starttime=start,endtime=end,level='response')
inv.write(str(raw/'stations.xml'),format='STATIONXML')
manifest=[]
for network in inv:
    for station in network:
        for hour in range(24):
            a=start+hour*3600;b=a+3600
            record=dict(network=network.code,station=station.code,start=str(a),end=str(b))
            try:
                stream=client.get_waveforms(network.code,station.code,'*','BH?,HH?',a,b)
                target=raw/('{}-{}-{:02d}.mseed'.format(network.code,station.code,hour))
                stream.write(str(target),format='MSEED')
                record.update(status='downloaded',sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                              gaps=stream.get_gaps())
            except Exception as e:record.update(status='failed',error=str(e))
            manifest.append(record)
            (raw/'manifest.json').write_text(json.dumps(manifest,indent=2,default=str)+'\n')
if not any(r['status']=='downloaded' for r in manifest):raise SystemExit('No waveforms downloaded')
