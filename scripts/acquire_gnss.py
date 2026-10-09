#!/usr/bin/env python3
"""Authenticated candidate RINEX retrieval; reject login HTML and preserve failures."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
from datetime import datetime,timezone
import requests
ROOT=Path(__file__).resolve().parents[1]
FILES={code:'https://data.earthscope.org/archive/gnss/rinex/obs/2018/177/'+code.lower()+'1770.18d.Z' for code in ['GV03','GV09']}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--plan',action='store_true',help='List candidate files without authentication or downloads')
    args=parser.parse_args()
    if args.plan:
        print(json.dumps(dict(candidate_urls=FILES,note='File existence is unverified; paths follow the official daily archive layout.'),indent=2));return
    records=[]
    token=None
    try:
        result=subprocess.run([str(ROOT/'.venv/bin/es'),'user','get-access-token'],
                              capture_output=True,text=True,timeout=20,env=dict(os.environ,NO_COLOR='1'))
        if result.returncode==0:
            candidate=result.stdout.strip()
            if candidate.count('.')==2 and not any(c.isspace() for c in candidate):token=candidate
    except (OSError,subprocess.TimeoutExpired):pass
    for station,url in FILES.items():
        record=dict(station=station,url=url,attempt_utc=datetime.now(timezone.utc).isoformat())
        if token is None:
            record.update(status='blocked',reason='No usable EarthScope access token; authenticate using .venv/bin/es login')
            records.append(record);continue
        target=ROOT/'data/raw/gnss'/(station.lower()+'1770.18d.Z')
        target.parent.mkdir(parents=True,exist_ok=True);temporary=target.with_suffix('.part')
        try:
            # Requests strips Authorization on cross-host redirects; no token is printed or recorded.
            with requests.get(url,headers={'Authorization':'Bearer '+token},stream=True,timeout=(10,60)) as response:
                response.raise_for_status()
                with temporary.open('wb') as output:
                    for chunk in response.iter_content(1024*1024):output.write(chunk)
            if temporary.read_bytes()[:2]!=b'\x1f\x9d':
                raise ValueError('Response is not UNIX-compress data; possible login page or unexpected encoding')
            temporary.replace(target)
            record.update(status='downloaded_compressed_unparsed',bytes=target.stat().st_size,
                          sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                          note='Compression header checked; RINEX content, epoch coverage and PPP not validated yet')
        except Exception as error:
            if temporary.exists():temporary.unlink()
            # Do not include request headers, tokens, or provider error bodies.
            record.update(status='failed',error_type=type(error).__name__)
        records.append(record)
    path=ROOT/'results/tables/gnss_acquisition_attempts.json'
    previous=json.loads(path.read_text()) if path.exists() else []
    path.write_text(json.dumps(previous+records,indent=2)+'\n')
    print(json.dumps(records,indent=2))
    if any(r['status']!='downloaded_compressed_unparsed' for r in records):raise SystemExit(1)


if __name__=='__main__':main()
