#!/usr/bin/env python3
"""Independent supplemental counterparts from computed waveform measurements."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]

def save(fig,name):
    fig.tight_layout()
    for suffix in ('pdf','png'):fig.savefig(ROOT/f'results/figures/{name}.{suffix}',dpi=300,bbox_inches='tight')
    plt.close(fig)

def main():
    cat=pd.read_csv(ROOT/'results/catalogs/enhanced_classified_catalog.csv')
    detections=pd.read_csv(ROOT/'results/catalogs/template_matched_candidate_events.csv')
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    values=cat.frequency_index.dropna()
    axes[0].hist(values,bins=np.linspace(-7,2,46),color='gray');axes[0].axvline(-2,c='black',ls='--');axes[0].set_xlabel('Frequency index');axes[0].set_ylabel('Candidate count')
    family_sizes=cat[cat.family_id>=0].groupby('family_id').size()
    axes[1].bar(np.arange(len(family_sizes)),family_sizes.to_numpy(),color='#255e9a');axes[1].set_xlabel('Connected family');axes[1].set_ylabel('Members')
    fig.suptitle('Independent FI and family-size distributions; inherited detection FI')
    save(fig,'supp_candidate_distributions')
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    valid=detections[np.isfinite(detections.measured_frequency_index)]
    axes[0].scatter(valid.frequency_index,valid.measured_frequency_index,s=8,alpha=.4)
    axes[0].axvline(-2,c='gray',ls='--');axes[0].axhline(-2,c='gray',ls='--')
    limits=[min(valid.frequency_index.min(),valid.measured_frequency_index.min()),max(valid.frequency_index.max(),valid.measured_frequency_index.max())]
    axes[0].plot(limits,limits,c='black',lw=.8);axes[0].set_xlabel('Template FI');axes[0].set_ylabel('Detection measured FI')
    axes[1].hist(detections.network_ncc,bins=30,color='gray');axes[1].set_xlabel('Network NCC');axes[1].set_ylabel('Additional candidates')
    fig.suptitle('Independent S8 counterpart: direct versus inherited spectral properties')
    save(fig,'supp_template_fi_comparison')
    magnitudes=pd.read_csv(ROOT/'results/catalogs/enhanced_magnitude_catalog.csv')
    fig,ax=plt.subplots(figsize=(10,4))
    for kind,color in [('VT','#bd5732'),('LP','#255e9a')]:
        sub=magnitudes[magnitudes.type==kind]
        ax.scatter((sub.time-1529971200)/3600,sub.approximate_ml,s=7,color=color,label=kind)
    for hour in (9.25,17,19+40/60):ax.axvline(hour,c='gray',ls=':')
    ax.set_xlabel('26 June 2018 UTC hour');ax.set_ylabel('Approximate local magnitude');ax.legend();ax.set_xlim(0,24)
    ax.set_title('Main Figure 2 counterpart: independent magnitudes; missing estimates omitted')
    save(fig,'enhanced_magnitude_timeline')

if __name__=='__main__':main()
