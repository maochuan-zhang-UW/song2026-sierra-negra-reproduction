#!/usr/bin/env python3
"""Check unresolved public access routes without storing login cookies or tokens.
HTTP 404 means this query returned no records; login HTML is never an observation.
"""
import concurrent.futures
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.parse import urlparse
import requests

ROOT = Path(__file__).resolve().parents[1]
QUERIES = {
    '8G SN01/SN03/SN08 all channels': 'https://service.iris.edu/fdsnws/dataselect/1/query?net=8G&sta=SN01,SN03,SN08&loc=*&cha=*&start=2018-06-26&end=2018-06-27&nodata=404',
    'EC SN09/SN10 all channels': 'https://service.earthscope.org/fdsnws/dataselect/1/query?net=EC&sta=SN09,SN10&loc=*&cha=*&start=2018-06-26&end=2018-06-27&nodata=404',
    'VCH1 EarthScope all networks': 'https://service.earthscope.org/fdsnws/dataselect/1/query?sta=VCH1&loc=*&cha=*&start=2018-06-26&end=2018-06-27&nodata=404',
    'GV03 daily RINEX': 'https://data.earthscope.org/archive/gnss/rinex/obs/2018/177/gv031770.18d.Z',
    'GV09 daily RINEX': 'https://data.earthscope.org/archive/gnss/rinex/obs/2018/177/gv091770.18d.Z',
    'IGEPN waveform portal': 'https://data.igepn.edu.ec/download/login2.php',
}


def check(item):
    name, url = item
    record = dict(resource=name, url=url, checked_utc=datetime.now(timezone.utc).isoformat())
    try:
        with requests.get(url, timeout=(10, 25), stream=True, allow_redirects=True) as response:
            prefix = next(response.iter_content(4096), b'')
            final = urlparse(response.url)
            record.update(http_status=response.status_code,
                          content_type=response.headers.get('Content-Type', ''),
                          final_host=final.netloc, final_path=final.path)
            if response.status_code == 404:
                interpretation = 'No records returned for this query; not proof of permanent unavailability'
            elif 'login' in response.url or 'auth' in final.netloc or b'password' in prefix.lower():
                interpretation = 'Provider login required; no observation data retrieved'
            else:
                interpretation = 'Response requires format validation; no observation data assumed'
            record['interpretation'] = interpretation
    except requests.RequestException as error:
        record['error'] = str(error)
    return record


if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(check, QUERIES.items()))
    target = ROOT / 'results/tables' / ('access_recheck_' + datetime.now(timezone.utc).strftime('%Y%m%d') + '.json')
    target.write_text(json.dumps(records, indent=2) + '\n')
    print(json.dumps(records, indent=2))
