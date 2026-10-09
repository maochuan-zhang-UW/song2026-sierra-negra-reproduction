#!/usr/bin/env python3
"""Plot independent station support and declared shifted-time controls."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
def main():
    table=pd.read_csv(ROOT/'results/tables/heldout_station_validation.csv')
    table=table[table.criterion=='same_station_P_and_S']
    fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
    for ax,subset,title in zip(axes,['all','new'],['All candidates','Template additions']):
        rows=table[table.subset==subset].sort_values('tolerance_s')
        if rows.empty:
            raise ValueError(f'Unknown subset {subset}; available: {table.subset.unique()}')
        ax.plot(rows.tolerance_s,rows.supported,'o-',label='Observed P and S support')
        ax.plot(rows.tolerance_s,rows.null_mean,'o--',label='Shifted-time mean')
        ax.fill_between(rows.tolerance_s,rows.null_2_5_percentile,rows.null_97_5_percentile,alpha=.2,label='Shifted-time 95% range')
        ax.set(xlabel='Arrival tolerance (s)',ylabel='Candidates supported',title=title);ax.grid(alpha=.2)
    axes[0].legend(fontsize=8)
    fig.suptitle('Held-out SN02/SN06: P and S must agree at the same station')
    for suffix in ['png','pdf']:fig.savefig(ROOT/f'results/figures/heldout_station_validation.{suffix}',dpi=300)
    plt.close(fig)
if __name__=='__main__':main()
