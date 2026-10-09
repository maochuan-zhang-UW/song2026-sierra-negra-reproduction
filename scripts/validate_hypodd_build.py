#!/usr/bin/env python3
"""Execute the unchanged author example and quantify reference differences."""
import json,shutil,subprocess
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def main():
    source=ROOT/'.cache/HypoDD';folder=ROOT/'.cache/hypodd-example';folder.mkdir(exist_ok=True)
    reference=source/'examples/example1'
    for name in ['dt.cc','dt.ct','event.sel','station.sel','hypoDD.inp']:shutil.copyfile(reference/name,folder/name)
    with (folder/'execution.log').open('w') as log:
        result=subprocess.run([str(source/'src/hypoDD/hypoDD'),'hypoDD.inp'],cwd=folder,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode or 'Program hypoDD finished' not in (folder/'execution.log').read_text(errors='replace'):raise RuntimeError('Author example did not finish')
    old=np.loadtxt(reference/'hypoDD.reloc');new=np.loadtxt(folder/'hypoDD.reloc')
    old=old[np.argsort(old[:,0])];new=new[np.argsort(new[:,0])]
    if old.shape!=new.shape or not np.array_equal(old[:,0],new[:,0]) or not np.isfinite(new).all():raise ValueError('Author example IDs or finite output disagree')
    record=dict(source_revision=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip(),example='author example1, unchanged inputs',events=len(new),
                max_horizontal_cartesian_difference_m=float(np.hypot(*(new[:,4:6]-old[:,4:6]).T).max()),
                max_depth_difference_m=float(abs(new[:,3]-old[:,3]).max()*1000),max_origin_seconds_field_difference_s=float(abs(new[:,15]-old[:,15]).max()))
    (ROOT/'results/tables/hypodd_author_example.json').write_text(json.dumps(record,indent=2)+'\n');print(record)
if __name__=='__main__':main()
