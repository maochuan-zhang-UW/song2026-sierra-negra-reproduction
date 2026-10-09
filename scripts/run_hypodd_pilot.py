#!/usr/bin/env python3
"""Run the real HypoDD pilot; alternate policy retains but freezes negative steps."""
import argparse,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--keep-shallow-events',action='store_true');args=parser.parse_args()
    baseline=ROOT/'.cache/hypodd_ct';folder=baseline
    if args.keep_shallow_events:
        folder=ROOT/'.cache/hypodd_ct_keep';folder.mkdir(exist_ok=True)
        for name in ['dt.cc','dt.ct','event.sel','station.sel']:
            path=folder/name
            if not path.exists():path.symlink_to(baseline/name)
        controls=(baseline/'hypoDD.inp').read_text().replace('\n2 2 1 1\n','\n2 2 0 1\n')
        (folder/'hypoDD.inp').write_text(controls)
    with (folder/'execution.log').open('w') as log:
        result=subprocess.run([str(ROOT/'.cache/HypoDD/src/hypoDD/hypoDD'),'hypoDD.inp'],cwd=folder,stdout=log,stderr=subprocess.STDOUT)
    completed='Program hypoDD finished' in (folder/'execution.log').read_text(errors='replace')
    if result.returncode or not completed or not (folder/'hypoDD.reloc').stat().st_size:raise RuntimeError('HypoDD did not complete with nonempty output')
    print(json.dumps(dict(folder=str(folder),completed=completed,policy='freeze negative depth steps' if args.keep_shallow_events else 'remove negative depth events')))
if __name__=='__main__':main()
