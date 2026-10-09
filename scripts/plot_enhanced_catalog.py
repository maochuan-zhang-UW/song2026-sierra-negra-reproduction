#!/usr/bin/env python3
"""Partial main Figures 1–4 from the computed enhanced candidate catalog."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
COLORS={'LP':'#255e9a','VT':'#bd5732','unclassified':'gray'}

def save(fig,name):
    fig.tight_layout()
    for suffix in ('pdf','png'):fig.savefig(ROOT/f'results/figures/{name}.{suffix}',dpi=300,bbox_inches='tight')
    plt.close(fig)

def main():
    catalog=pd.read_csv(ROOT/'results/catalogs/enhanced_classified_catalog.csv')
    h=(catalog.time-1529971200)/3600
    fig,axes=plt.subplots(3,1,figsize=(10,9),sharex=True)
    for kind,color in COLORS.items():
        select=catalog.type==kind
        axes[0].scatter(h[select],catalog.frequency_index[select],s=7,color=color,label=f'{kind}: {select.sum()}')
        t=np.sort(h[select]);axes[2].step(t,np.arange(1,len(t)+1),where='post',color=color,label=kind)
    axes[0].axhline(-2,color='black',ls='--',lw=.8);axes[0].legend(ncol=3);axes[0].set_ylabel('Frequency index')
    for family,sub in catalog[catalog.family_id>=0].groupby('family_id'):
        color=COLORS['LP' if sub.frequency_index.mean()<-2 else 'VT']
        axes[1].scatter((sub.time-1529971200)/3600,np.full(len(sub),family),marker='|',s=60,color=color)
    axes[1].set_ylabel('Connected family');axes[1].set_ylim(-.5,max(.5,catalog.family_id.max()+.5))
    axes[2].set_ylabel('Cumulative candidates');axes[2].set_xlabel('26 June 2018 UTC hour');axes[2].legend(ncol=3)
    for ax in axes:
        for time in (9.25,17,19+40/60):ax.axvline(time,c='gray',ls=':',lw=.8)
        ax.set_xlim(0,24)
    fig.suptitle('Independent seven-station enhanced candidates; template FI inherited')
    save(fig,'enhanced_frequency_families')
    fig,axes=plt.subplots(2,2,figsize=(10,8),sharex=True,sharey=True)
    limits=(0,9.25,17,19+40/60,24)
    for number,ax in enumerate(axes.flat):
        phase=(h>=limits[number])&(h<limits[number+1])
        for kind,color in COLORS.items():
            rows=catalog[phase&(catalog.type==kind)]
            ax.scatter(rows.longitude,rows.latitude,s=8,c=color,label=f'{kind}: {len(rows)}',alpha=.6)
        ax.set_title(f'Phase {number+1}: {limits[number]:.2f}–{limits[number+1]:.2f} UTC h');ax.legend(fontsize=7)
        ax.set_xlabel('Longitude (degrees)');ax.set_ylabel('Latitude (degrees)');ax.set_aspect('equal')
    fig.suptitle('Approximate template locations; no differential relocation')
    save(fig,'enhanced_phase_maps')
    counts=[]
    for number in range(4):
        sub=catalog[(h>=limits[number])&(h<limits[number+1])]
        for kind in COLORS:counts.append(dict(phase=number+1,type=kind,events=int((sub.type==kind).sum())))
    pd.DataFrame(counts).to_csv(ROOT/'results/tables/enhanced_phase_class_counts.csv',index=False)

if __name__=='__main__':main()
