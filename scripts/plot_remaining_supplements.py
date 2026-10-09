#!/usr/bin/env python3
"""Partial S2/S3/S4/S7 counterparts on actual independent candidate products."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
COLORS={'LP':'#255e9a','VT':'#bd5732'}

def save(fig,name):
    fig.tight_layout()
    for suffix in ('pdf','png'):fig.savefig(ROOT/f'results/figures/{name}.{suffix}',dpi=300,bbox_inches='tight')
    plt.close(fig)

def main():
    cat=pd.read_csv(ROOT/'results/catalogs/enhanced_classified_catalog.csv')
    lp=cat[cat.type=='LP'];vt=cat[cat.frequency_index>0]
    def xyz(sub):return np.column_stack([(sub.longitude+91.15)*111.32*np.cos(np.deg2rad(-.83)),(sub.latitude+.83)*111.32,sub.depth])
    distance,_=cKDTree(xyz(vt)).query(xyz(lp))
    pd.DataFrame({'LP_event_id':lp.event_id,'nearest_typical_VT_3d_km':distance}).to_csv(ROOT/'results/tables/LP_typical_VT_distances.csv',index=False)
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for sub,kind in [(lp,'LP'),(vt,'VT')]:axes[0].scatter((sub.time-1529971200)/3600,sub.depth,s=7,c=COLORS[kind],label=kind)
    axes[0].invert_yaxis();axes[0].set_xlabel('UTC hour');axes[0].set_ylabel('Approximate depth (km below sea level)');axes[0].legend()
    axes[1].hist(distance,bins=30,color='gray');axes[1].set_xlabel('Nearest typical VT 3D distance (km)');axes[1].set_ylabel('LP candidates')
    fig.suptitle('S2 counterpart: inherited approximate locations; typical VT FI > 0')
    save(fig,'supp_spatial_LP_VT')
    families=pd.read_csv(ROOT/'results/tables/enhanced_permissive_family_statistics.csv')
    membership=pd.read_csv(ROOT/'results/catalogs/enhanced_permissive_classified_catalog.csv')
    meta=pd.read_csv(ROOT/'results/tables/enhanced_window_metadata.csv')
    archive=np.load(ROOT/'.cache/enhanced_windows/windows.npz')
    fig,axes=plt.subplots(1,2,figsize=(10,8),sharex=True)
    for ax,kind in zip(axes,['LP','VT']):
        stats=families[families.family_type==kind].sort_values('events',ascending=False)
        number=int(stats.iloc[0].family_id)
        sub=membership[membership.family_id==number].sort_values('time')
        rows=meta[(meta.event_idx.isin(sub.idx))&(meta.station=='SN12')&(meta.component=='Z')&(meta.snr>=2)].iloc[:20]
        if len(rows):
            reference=archive[rows.iloc[0].key].astype(float)
            for i,row in enumerate(rows.itertuples()):
                y=archive[row.key].astype(float)
                # Choose maximum positive coefficient, preserving polarity.
                options=[]
                for lag in range(-10,11):
                    lo=max(0,-lag);hi=min(len(y),len(y)-lag)
                    options.append((np.corrcoef(reference[lo:hi],y[lo+lag:hi+lag])[0,1],lag))
                score,lag=max(options)
                ax.plot(np.arange(len(y))/50-1-lag/50,y/np.max(abs(y))*.35+i,lw=.6,c=COLORS[kind])
        ax.set_title(f'{kind} permissive family {number}');ax.set_xlabel('Relative P time (s)');ax.set_ylabel('SN12 normalized waveform + offset')
    fig.suptitle('Independent S3 examples; source family identities unavailable')
    save(fig,'supp_family_waveforms')
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for kind,color in COLORS.items():
        sub=families[families.family_type==kind]
        axes[0].hist(sub.periodicity_ddof0,bins=np.linspace(0,2,11),alpha=.5,color=color,label=kind)
        axes[1].scatter(sub.mean_recurrence_s,sub.periodicity_ddof0,c=color,label=kind)
    axes[0].axvline(1,c='black',ls='--');axes[0].set_xlabel('Periodicity (mean/std, ddof=0)');axes[0].set_ylabel('Families');axes[0].legend()
    axes[1].set_xlabel('Mean recurrence (s)');axes[1].set_ylabel('Periodicity');axes[1].legend()
    fig.suptitle('S4 counterpart: permissive memberships; Pearson r = -0.421')
    save(fig,'supp_family_periodicity')
    before=pd.read_csv(ROOT/'results/catalogs/candidate_magnitude_catalog.csv');after=pd.read_csv(ROOT/'results/catalogs/enhanced_magnitude_catalog.csv')
    fig,axes=plt.subplots(1,3,figsize=(13,4));records=[]
    for label,frame,color in [('Before',before,'#92b5cf'),('After',after,'#255e9a')]:
        time=(frame.time-1529971200)/3600
        axes[0].step(np.sort(time),np.arange(1,len(time)+1),where='post',label=label,c=color)
        for ax,phase,select in [(axes[1],'Phases 1–2',time<17),(axes[2],'Phases 3–4',time>=17)]:
            magnitude=frame.loc[select,'approximate_ml'].dropna().to_numpy()
            edges=np.arange(np.floor(magnitude.min()*10)/10,np.ceil(magnitude.max()*10)/10+.1001,.1)
            counts,_=np.histogram(magnitude,edges);centers=(edges[:-1]+edges[1:])/2
            mode=float(centers[np.argmax(counts)])
            ax.step(centers,counts,where='mid',label=label,c=color);ax.axvline(mode,c=color,ls='--')
            ax.set_title(phase);ax.set_xlabel('Approximate ML');ax.set_ylabel('Frequency');ax.legend(fontsize=8)
            records.append(dict(catalog=label,phase=phase,estimated_magnitudes=len(magnitude),uncorrected_max_curvature_ML=mode,bin_width=.1))
    axes[0].axvline(17,c='black',ls='--');axes[0].set_xlabel('UTC hour');axes[0].set_ylabel('Cumulative candidates');axes[0].legend()
    fig.suptitle('S7 counterpart: approximate samples; histogram mode is not proven completeness')
    save(fig,'supp_before_after_matching')
    pd.DataFrame(records).to_csv(ROOT/'results/tables/magnitude_histogram_modes.csv',index=False)

if __name__=='__main__':main()
