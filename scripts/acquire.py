#!/usr/bin/env python3
"""Fetch public source files atomically and record actual failures and checksums."""
import argparse,hashlib,json,urllib.request
from pathlib import Path
from datetime import datetime
ROOT=Path(__file__).resolve().parents[1]
URLS={
 'IGUANA_Cat_V1.eventlist':'https://zenodo.org/records/4389190/files/IGUANA_Cat_V1.eventlist',
 'GV01-gv02_gv04_filled.baseline':'https://zenodo.org/records/4389190/files/GV01-gv02_gv04_filled.baseline',
 'article.pdf':'https://www.nature.com/articles/s41467-026-68645-4.pdf',
 'supplement.pdf':'https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-026-68645-4/MediaObjects/41467_2026_68645_MOESM1_ESM.pdf',
 '8G_20180626.mseed':'https://service.iris.edu/fdsnws/dataselect/1/query?net=8G&sta=*&loc=*&cha=HH?&start=2018-06-26T00:00:00&end=2018-06-27T00:00:00',
 'PAYG_stations.xml':'https://service.iris.edu/fdsnws/station/1/query?net=IU&sta=PAYG&loc=00&cha=BHZ&start=1999-12-22&end=2018-06-27&level=response&format=xml',
 'stations.xml':'https://service.iris.edu/fdsnws/station/1/query?network=8G&starttime=2018-06-26&endtime=2018-06-27&level=response&format=xml'
}
for date in ['2018-06-26','2005-10-22','2005-04-16','1999-12-22']:
    URLS['PAYG_'+date+'.mseed']='https://service.iris.edu/fdsnws/dataselect/1/query?net=IU&sta=PAYG&loc=00&cha=BHZ&start='+date+'T00:00:00&end='+date+'T23:59:59.99'


def fetch(name,url):
    target=ROOT/'data/raw'/name;target.parent.mkdir(parents=True,exist_ok=True)
    temp=target.with_suffix(target.suffix+'.part')
    record=dict(name=name,url=url,attempt_utc=datetime.utcnow().isoformat()+'Z')
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Song2026-reproducibility/0.1'})
        with urllib.request.urlopen(req,timeout=30) as response, temp.open('wb') as out:
            if response.status!=200:raise RuntimeError('Unexpected HTTP response')
            while True:
                chunk=response.read(1024*1024)
                if not chunk:break
                out.write(chunk)
        if not temp.stat().st_size:raise ValueError('Empty response')
        if name.endswith('.pdf') and not temp.read_bytes().startswith(b'%PDF'):
            raise ValueError('Response is not a PDF (possible access challenge)')
        if name.endswith('.eventlist') and b'EVENT EVENT_ID' not in temp.read_bytes()[:1000]:
            raise ValueError('Not a recognized earthquake catalog')
        temp.replace(target)
        record.update(status='downloaded',bytes=target.stat().st_size,
                      sha256=hashlib.sha256(target.read_bytes()).hexdigest())
    except Exception as e:
        if temp.exists():temp.unlink()
        record.update(status='failed',error=str(e))
    return record


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--only',choices=list(URLS));args=parser.parse_args()
    selected={args.only:URLS[args.only]} if args.only else URLS
    records=[fetch(k,v) for k,v in selected.items()]
    (ROOT/'results/tables/acquisition_attempts.json').write_text(json.dumps(records,indent=2)+'\n')
    print(json.dumps(records,indent=2))
    if any(r['status']=='failed' for r in records):raise SystemExit(1)
