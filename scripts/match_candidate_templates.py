#!/usr/bin/env python3
"""Run actual full-day network template matching; retain self-detection audit."""
import argparse,json,multiprocessing
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from src.template_matching.batch_fft import correlation_context,correlate_templates

ROOT=Path(__file__).resolve().parents[1]
CATALOG=None;METADATA=None;WINDOWS=None;TEMPLATES=None;NULL_CONTROL=False


def match_hour(hour):
    ids=TEMPLATES.idx.to_list();lookup={event:i for i,event in enumerate(ids)}
    scores=np.zeros((len(ids),180000));audit=[];detections=[]
    groups=METADATA.groupby(['station','component','phase'])
    for (station,component,phase),rows in groups:
        path=ROOT/f'.cache/matching_velocity/hour_{hour:02d}/{station}.{component}.npy'
        continuous=np.load(path,mmap_mode='r')
        context=correlation_context(continuous,250)
        for start in range(0,len(rows),16):
            batch=rows.iloc[start:start+16]
            waveforms=np.array([WINDOWS[key] for key in batch.key])
            coefficients=correlate_templates(context,waveforms)
            indices=np.array([lookup[event] for event in batch.event_idx])
            offset=30*50 if hour else 0
            origins=offset+batch.pick_offset_samples.to_numpy()
            position=origins[:,None]+np.arange(180000)[None,:]
            valid=(position>=0)&(position<coefficients.shape[1])
            # Only the true day edges can lack context; detections exclude 64 s there.
            aligned=np.take_along_axis(coefficients,np.clip(position,0,coefficients.shape[1]-1),axis=1)
            scores[indices]+=np.where(valid,aligned,0)*batch.station_weight.to_numpy()[:,None]
    for i,event in enumerate(ids):
        score=scores[i];mad=float(np.nanmedian(np.abs(score)));threshold=max(9*mad,.4)
        finite_score=np.where(np.isfinite(score),score,-np.inf)
        peaks,_=find_peaks(np.r_[-np.inf,finite_score,-np.inf],height=threshold,distance=100)
        peaks=peaks-1
        template=TEMPLATES[TEMPLATES.idx==event].iloc[0]
        origin_hour=(template.time-1529971200)/3600
        self_ncc=None;self_time_error=None
        if int(origin_hour)==hour:
            index=round((template.time-1529971200-hour*3600)*50)
            lo=max(0,index-100);hi=min(len(score),index+101)
            best=lo+int(np.argmax(finite_score[lo:hi]))
            self_ncc=float(score[best]);self_time_error=float((hour*3600+best/50)-(template.time-1529971200))
        audit.append(dict(hour=hour,template_idx=event,median_absolute_ncc=mad,threshold_ncc=threshold,
                          peaks=len(peaks),self_ncc=self_ncc,self_time_error_s=self_time_error))
        for peak in peaks:
            time=hour*3600+peak/50
            if not 64<=time<86400-64:continue
            detections.append(dict(template_idx=event,time=1529971200+time,network_ncc=float(score[peak]),
                                   threshold_ncc=threshold,stations=int(template.template_stations),hour=hour))
    destination=ROOT/('.cache/template_control' if NULL_CONTROL else '.cache/template_detections');destination.mkdir(exist_ok=True)
    pd.DataFrame(detections,columns=['template_idx','time','network_ncc','threshold_ncc','stations','hour']).to_csv(destination/f'hour_{hour:02d}.csv',index=False)
    pd.DataFrame(audit).to_csv(destination/f'audit_{hour:02d}.csv',index=False)
    print(hour,len(detections),'raw template peaks',flush=True)
    return len(detections)


def main():
    global CATALOG,METADATA,WINDOWS,TEMPLATES,NULL_CONTROL
    parser=argparse.ArgumentParser();parser.add_argument('--null-control',action='store_true');args=parser.parse_args();NULL_CONTROL=args.null_control
    CATALOG=pd.read_csv(ROOT/'results/catalogs/candidate_classified_catalog.csv')
    METADATA=pd.read_csv(ROOT/'results/tables/candidate_window_metadata.csv')
    METADATA=METADATA[(METADATA.snr>=2)&np.isfinite(METADATA.snr)].copy()
    counts=METADATA.groupby('event_idx').station.nunique()
    ids=counts[counts>=4].index
    if NULL_CONTROL:
        selected=[]
        for kind in ('LP','VT'):
            subset=CATALOG[CATALOG.idx.isin(ids)&(CATALOG.type==kind)].idx.to_numpy()
            selected.extend(subset[np.linspace(0,len(subset)-1,min(10,len(subset)),dtype=int)])
        ids=pd.Index(selected)
    METADATA=METADATA[METADATA.event_idx.isin(ids)].copy()
    TEMPLATES=CATALOG[CATALOG.idx.isin(ids)].copy()
    TEMPLATES['template_stations']=TEMPLATES.idx.map(counts)
    TEMPLATES.to_csv(ROOT/('results/catalogs/selected_control_templates.csv' if NULL_CONTROL else 'results/catalogs/selected_candidate_templates.csv'),index=False)
    channels=METADATA.groupby(['event_idx','station']).size()
    times=CATALOG.set_index('idx').time
    METADATA['station_weight']=[1/(counts[row.event_idx]*channels.loc[(row.event_idx,row.station)]) for row in METADATA.itertuples()]
    METADATA['pick_offset_samples']=[round((pd.Timestamp(row.pick_time_utc).timestamp()-1-times.loc[row.event_idx])*50) for row in METADATA.itertuples()]
    archive=np.load(ROOT/'.cache/candidate_windows/windows.npz',allow_pickle=False)
    WINDOWS={key:archive[key].astype(float) for key in METADATA.key}
    if NULL_CONTROL:
        rng=np.random.default_rng(20261009)
        for key,waveform in WINDOWS.items():
            spectrum=np.fft.rfft(waveform);phase=np.exp(1j*rng.uniform(0,2*np.pi,len(spectrum)))
            phase[0]=1;phase[-1]=1
            WINDOWS[key]=np.fft.irfft(spectrum*phase,n=len(waveform))
    if METADATA.pick_offset_samples.abs().max()>1250:raise ValueError('Template offsets exceed real hour padding')
    with multiprocessing.get_context('fork').Pool(12) as pool:pool.map(match_hour,range(24))
    destination=ROOT/('.cache/template_control' if NULL_CONTROL else '.cache/template_detections')
    raw=pd.concat([pd.read_csv(destination/f'hour_{h:02d}.csv') for h in range(24)],ignore_index=True)
    audit=pd.concat([pd.read_csv(destination/f'audit_{h:02d}.csv') for h in range(24)],ignore_index=True)
    if NULL_CONTROL:
        audit.to_csv(ROOT/'results/tables/template_control_audit.csv',index=False)
        raw.to_csv(ROOT/'results/catalogs/template_control_peaks.csv',index=False)
        record=dict(control='20 templates, 10 LP and 10 VT, independently phase-randomized per channel while preserving individual Fourier amplitude spectra',
                    seed=20261009,templates=len(TEMPLATES),station_hours=168,raw_control_peaks=len(raw),
                    thresholds='same positive max(9*MAD,0.4) as actual search',
                    limitations=['Tests waveform-shape specificity, not earthquake false-positive rate','Independent channel phases remove network coherence',
                                 'A smaller control library than real 447 templates; counts not directly scaled'])
        (ROOT/'results/tables/template_control_execution.json').write_text(json.dumps(record,indent=2)+'\n')
        print(json.dumps(record,indent=2));return
    audit.to_csv(ROOT/'results/tables/template_detection_audit.csv',index=False)
    raw.to_csv(ROOT/'results/catalogs/raw_template_peaks.csv',index=False)
    original=np.sort(CATALOG.time.to_numpy())
    position=np.searchsorted(original,raw.time.to_numpy())
    distance=np.minimum(np.abs(raw.time.to_numpy()-original[np.minimum(position,len(original)-1)]),
                        np.abs(raw.time.to_numpy()-original[np.maximum(position-1,0)]))
    new=raw[distance>2].copy()
    # Highest-score-first suppression gives a two-second exclusion in either direction.
    kept=[];times=[]
    import bisect
    for row in new.sort_values('network_ncc',ascending=False).itertuples():
        index=bisect.bisect_left(times,row.time)
        if (index and row.time-times[index-1]<2) or (index<len(times) and times[index]-row.time<2):continue
        bisect.insort(times,row.time);kept.append(row.Index)
    new=new.loc[kept].sort_values('time').reset_index(drop=True)
    new['event_id']=[f'matched_{i:05d}' for i in range(len(new))]
    inherited=CATALOG[['idx','latitude','longitude','depth','frequency_index','type','event_id']].rename(
        columns={'idx':'template_idx','event_id':'template_event_id'})
    new=new.merge(inherited,on='template_idx',validate='m:1')
    new['origin_time_utc']=pd.to_datetime(new.time,unit='s',utc=True)
    new['fi_provenance']='inherited from template; not directly measured'
    new['location_method']='co-located with approximate template; not independently located'
    new.to_csv(ROOT/'results/catalogs/template_matched_candidate_events.csv',index=False)
    self_rows=audit[audit.self_ncc.notna()]
    record=dict(templates=len(TEMPLATES),raw_template_peaks=len(raw),additional_candidates=len(new),
                additional_classes=new.type.value_counts().to_dict(),
                self_recovered=int((self_rows.self_ncc>=self_rows.threshold_ncc).sum()),
                self_audited=len(self_rows),minimum_self_ncc=float(self_rows.self_ncc.min()),
                maximum_self_time_error_s=float(self_rows.self_time_error_s.abs().max()),
                MAD='median(abs(network mean NCC)); EQcorrscan documented convention',
                thresholds='positive score >= max(9*MAD, 0.4)',peak_separation_s=2,
                known_event_exclusion_s=2,network_weighting='equal stations; mean available components within each',
                limitations=['Seven stations only','Approximate template locations','No undocumented spike rejection recreated',
                             'Unvalidated additional candidates are not confirmed earthquakes','No magnitudes',
                             'All 536 known candidates excluded, not only selected templates'])
    (ROOT/'results/tables/template_matching_execution.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))


if __name__=='__main__':main()
