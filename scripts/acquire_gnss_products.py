#!/usr/bin/env python3
"""Retrieve public ESA precise products for independent PPP."""
import gzip
import hashlib
import json
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]


def main():
    records=[]
    for suffix in ('05M_ORB.SP3','30S_CLK.CLK'):
        name='ESA0MGNFIN_20181770000_01D_'+suffix+'.gz'
        url='https://navigation-office.esa.int/products/gnss-products/2007/'+name
        response=requests.get(url,timeout=(10,90));response.raise_for_status()
        decoded=gzip.decompress(response.content)
        target=ROOT/'data/raw/gnss'/name
        target.write_bytes(response.content)
        # RTKLIB 2.4.2 has a case-sensitive SP3 suffix bug; use lowercase.
        target.with_suffix('').with_suffix('.'+suffix.split('.')[-1].lower()).write_bytes(decoded)
        records.append(dict(url=url,compressed_sha256=hashlib.sha256(response.content).hexdigest(),
                            decoded_bytes=len(decoded),sha256=hashlib.sha256(decoded).hexdigest()))
    # ESA clocks state IGS20 antenna calibration in their header.
    url='https://files.igs.org/pub/station/general/igs20.atx'
    response=requests.get(url,timeout=(10,90));response.raise_for_status()
    if b'ANTEX VERSION / SYST' not in response.content[:100]:
        raise ValueError('Invalid antenna calibration header')
    (ROOT/'data/raw/gnss/igs20.atx').write_bytes(response.content)
    records.append(dict(url=url,bytes=len(response.content),sha256=hashlib.sha256(response.content).hexdigest()))
    (ROOT/'results/tables/gnss_precise_products.json').write_text(json.dumps(records,indent=2)+'\n')
    print(json.dumps(records,indent=2))


if __name__ == '__main__':
    main()
