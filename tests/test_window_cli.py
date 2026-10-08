"""End-to-end window analysis on synthetic fixtures; no observed-event inference."""
import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
import numpy as np
import pandas as pd


class WindowCLI(unittest.TestCase):
    def test_classification_family_and_statistics(self):
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(dir=str(root/'.cache/tmp')) as directory:
            d=Path(directory);events=[];metadata=[];arrays={}
            n=500;fs=100;f=np.fft.rfftfreq(n,1/fs);spectrum=np.zeros(len(f),dtype=complex)
            spectrum[(f>=2)&(f<=5)]=5;spectrum[(f>=9)&(f<=15)]=1
            waveform=np.fft.irfft(spectrum,n=n)
            for i in range(12):
                event='synthetic_{}'.format(i);key=event+'__STA.Z.P'
                events.append(dict(event_id=event,origin_time='2018-06-26T00:{:02d}:00Z'.format(i*i//2+i),magnitude=i/10))
                metadata.append(dict(key=key,sampling_rate=fs,snr=10));arrays[key]=waveform
            # Use monotonically increasing seconds without minute overflow.
            times=pd.date_range('2018-06-26',periods=12,freq='2min',tz='UTC')
            for event,t in zip(events,times):event['origin_time']=t.isoformat()
            pd.DataFrame(events).to_csv(str(d/'events.csv'),index=False)
            pd.DataFrame(metadata).to_csv(str(d/'metadata.csv'),index=False)
            np.savez(str(d/'windows.npz'),**arrays)
            command=[sys.executable,str(root/'scripts/analyze_windows.py'),str(d/'events.csv'),str(d/'windows.npz'),str(d/'metadata.csv'),
                     '--output',str(d/'out'),'--max-lag-seconds','0','--pairing','preceding','--transform','linear','--ddof','0']
            subprocess.check_output(command,cwd=str(root),stderr=subprocess.STDOUT)
            result=pd.read_csv(str(d/'out/classified_catalog.csv'))
            self.assertEqual(set(result.type),{'LP'});self.assertEqual(set(result.family_id),{0})
            self.assertEqual(len(pd.read_csv(str(d/'out/moment_recurrence_pairs.csv'))),11)
            self.assertEqual(json.loads((d/'out/settings.json').read_text())['n_families'],1)


if __name__=='__main__':unittest.main()
