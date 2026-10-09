#!/usr/bin/env python3
"""Plot computed candidate properties and signed waveform review panels."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from src.template_matching.matching import pair_ncc
ROOT=Path(__file__).resolve().parents[1]

def save(fig,name):
    for suffix in ('pdf','png'):fig.savefig(ROOT/f'results/figures/{name}.{suffix}',dpi=300,bbox_inches='tight')
    plt.close(fig)

def main():
    cat=pd.read_csv(ROOT/'results/catalogs/candidate_classified_catalog.csv')
    hour=(cat.time-1529971200)/3600
    fig,axes=plt.subplots(3,1,figsize=(10,9),sharex=True)
    for kind,color in [('VT','#bd5732'),('LP','#255e9a'),('unclassified','gray')]:
        select=cat.type==kind
        axes[0].scatter(hour[select],cat.frequency_index[select],s=12,label=f'{kind}: {select.sum()}',color=color)
    axes[0].axhline(-2,c='black',ls='--',lw=.8);axes[0].set_ylabel('Frequency index');axes[0].legend()
    family=cat.family_id>=0
    axes[1].scatter(hour[family],cat.family_id[family],marker='|',s=170,c='#255e9a')
    axes[1].set_ylabel('Family');axes[1].set_yticks([0]);axes[1].set_ylim(-.7,.7)
    for kind,color in [('VT','#bd5732'),('LP','#255e9a')]:
        times=np.sort(hour[cat.type==kind]);axes[2].step(times,np.arange(1,len(times)+1),where='post',label=kind,color=color)
    axes[2].set_ylabel('Cumulative candidates');axes[2].set_xlabel('26 June 2018, UTC hour');axes[2].legend()
    for ax in axes:
        for t in (9.25,17,19+40/60):ax.axvline(t,c='gray',ls=':',lw=.8)
        ax.set_xlim(0,24)
    fig.suptitle('Seven-station candidate analysis; before template expansion')
    save(fig,'candidate_frequency_families')
    pairs=pd.read_csv(ROOT/'results/catalogs/candidate_anticorrelations_NEED_REVIEW.csv')
    meta=pd.read_csv(ROOT/'results/tables/candidate_window_metadata.csv')
    archive=np.load(ROOT/'.cache/candidate_windows/windows.npz')
    rows=[]
    for pair in pairs.itertuples():
        a=int(pair.event_a.split('_')[1]);b=int(pair.event_b.split('_')[1])
        left=meta[(meta.event_idx==a)&(meta.snr>=2)];right=meta[(meta.event_idx==b)&(meta.snr>=2)]
        common=left.merge(right,on=['station','component','phase'],suffixes=('_a','_b'))
        fig,axes=plt.subplots(len(common),1,figsize=(10,max(4,len(common)*1.15)),sharex=True,squeeze=False)
        for ax,row in zip(axes[:,0],common.itertuples()):
            x=archive[row.key_a];y=archive[row.key_b];score,lag=pair_ncc(x,y,10)
            t=np.arange(len(x))/50-1
            ax.plot(t,x/np.max(np.abs(x)),color='#255e9a',lw=.8,label=pair.event_a)
            ax.plot(t-lag/50,y/np.max(np.abs(y)),color='#bd5732',lw=.8,label=pair.event_b)
            ax.set_ylabel(f'{row.station}\n{row.component}/{row.phase}',fontsize=8)
            ax.text(.99,.78,f'NCC {score:.3f}; lag {lag/50:+.2f} s',ha='right',transform=ax.transAxes,fontsize=8)
            ax.set_ylim(-1.2,1.2)
            rows.append(dict(event_a=pair.event_a,event_b=pair.event_b,station=row.station,component=row.component,phase=row.phase,ncc=score,lag_s=lag/50))
        axes[0,0].legend(loc='upper left',fontsize=7,ncol=2)
        axes[-1,0].set_xlabel('Time relative to phase pick (s); second trace shifted to best signed NCC')
        fig.suptitle(f'{pair.event_a} / {pair.event_b}: network NCC {pair.signed_network_ncc:.3f}\nPolarity preserved; normalized amplitudes; visual-review candidates')
        save(fig,f'negative_pair_{a:04d}_{b:04d}')
    pd.DataFrame(rows).to_csv(ROOT/'results/tables/negative_pair_channel_scores.csv',index=False)

if __name__=='__main__':main()
