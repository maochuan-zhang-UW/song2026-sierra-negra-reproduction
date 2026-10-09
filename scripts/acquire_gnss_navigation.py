#!/usr/bin/env python3
"""Download and verify GPS navigation data without recording credentials."""
import hashlib
import json
import subprocess
from pathlib import Path
import requests
import hatanaka
from scripts.acquire_gnss import ROOT


def main():
    token=subprocess.run([str(ROOT/'.venv/bin/es'),'user','get-access-token'],
                         capture_output=True,text=True,check=True).stdout.strip()
    if token.count('.') != 2 or any(c.isspace() for c in token):
        raise ValueError('No usable EarthScope token')
    records=[]
    for station in ('gv03','gv09'):
        url=f'https://data.earthscope.org/archive/gnss/rinex/nav/2018/177/{station}1770.18n.Z'
        response=requests.get(url,headers={'Authorization':'Bearer '+token},timeout=(10,60))
        response.raise_for_status()
        if response.content[:2] != b'\x1f\x9d':
            raise ValueError('Expected UNIX-compress navigation file')
        decoded=hatanaka.decompress(response.content)
        if b'N: GPS NAV DATA' not in decoded[:80]:
            raise ValueError('Unexpected RINEX navigation header')
        target=ROOT/f'data/raw/gnss/{station}1770.18n'
        target.with_suffix('.18n.Z').write_bytes(response.content)
        target.write_bytes(decoded)
        records.append(dict(url=url,status='validated_gps_navigation_header',bytes=len(decoded),
                            compressed_sha256=hashlib.sha256(response.content).hexdigest(),
                            rinex_sha256=hashlib.sha256(decoded).hexdigest()))
    (ROOT/'results/tables/gnss_navigation_provenance.json').write_text(json.dumps(records,indent=2)+'\n')
    print(json.dumps(records,indent=2))



if __name__ == '__main__':
    main()
