#!/usr/bin/env python3
"""Independent OLS/RANSAC fits of computed family moments and recurrence."""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression,RANSACRegressor
from src.statistical_analysis.statistics import moment_recurrence_pairs,regression
ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--permissive',action='store_true');args=parser.parse_args()
    screen='enhanced_permissive' if args.permissive else 'enhanced'
    output='observed_permissive' if args.permissive else 'observed'
    families=pd.read_csv(ROOT/f'results/catalogs/{screen}_classified_catalog.csv')
    magnitudes=pd.read_csv(ROOT/'results/catalogs/enhanced_magnitude_catalog.csv')
    families=families.merge(magnitudes[['idx','approximate_ml','approximate_moment_Nm']],on='idx',validate='1:1')
    families.to_csv(ROOT/f'results/catalogs/{screen}_analysis_catalog.csv',index=False)
    stats=pd.read_csv(ROOT/f'results/tables/{screen}_family_statistics.csv').set_index('family_id')
    rows=[]
    for family,sub in families[families.family_id>=0].groupby('family_id'):
        kind=stats.loc[family].family_type
        # Published phase comparison: LP before intrusion; VT after intrusion.
        subset=sub[sub.time<1529971200+17*3600] if kind=='LP' else sub[sub.time>=1529971200+17*3600]
        subset=subset.sort_values('time')
        for pairing in ('preceding','following'):
            # Do not bridge missing-magnitude events to fabricate longer intervals.
            for a,b in zip(subset.iloc[:-1].itertuples(),subset.iloc[1:].itertuples()):
                ml=b.approximate_ml if pairing=='preceding' else a.approximate_ml
                if not np.isfinite(ml):continue
                from src.statistical_analysis.statistics import seismic_moment
                rows.append(dict(family_id=int(family),family_type=kind,pairing=pairing,preceding_event=a.event_id,following_event=b.event_id,
                                 recurrence_s=float(b.time-a.time),moment_Nm=float(seismic_moment(ml))))
    pairs=pd.DataFrame(rows,columns=['family_id','family_type','pairing','preceding_event','following_event','recurrence_s','moment_Nm'])
    pairs.to_csv(ROOT/f'results/tables/{output}_moment_recurrence_pairs.csv',index=False)
    fits=[];fig,axes=plt.subplots(1,2,figsize=(11,4.5),sharey=True)
    for ax,kind in zip(axes,['LP','VT']):
        for pairing in ('preceding','following'):
            points=pairs[(pairs.family_type==kind)&(pairs.pairing==pairing)]
            if len(points)<4:continue
            x=np.log10(points.recurrence_s.to_numpy());y=np.log10(points.moment_Nm.to_numpy())
            fit=regression(points.recurrence_s,points.moment_Nm,'log10')
            fits.append(dict(family_type=kind,pairing=pairing,estimator='OLS',**fit))
            estimator=RANSACRegressor(estimator=LinearRegression(),min_samples=2,max_trials=1000,random_state=20261009)
            estimator.fit(x[:,None],y)
            predictions=estimator.predict(x[:,None]);mask=estimator.inlier_mask_
            denominator=np.sum((y-y.mean())**2)
            fits.append(dict(family_type=kind,pairing=pairing,estimator='RANSAC independent settings',slope=float(estimator.estimator_.coef_[0]),intercept=float(estimator.estimator_.intercept_),
                             r_squared=float(1-np.sum((y-predictions)**2)/denominator) if denominator else np.nan,
                             inlier_r_squared=float(estimator.score(x[mask,None],y[mask])),inliers=int(mask.sum()),n=len(points),transform='log10'))
            if pairing=='preceding':
                ax.scatter(x,y,s=12,alpha=.55)
                grid=np.linspace(x.min(),x.max(),100)
                ax.plot(grid,estimator.predict(grid[:,None]),label='Independent RANSAC')
                ax.plot(grid,fit['slope']*grid+fit['intercept'],ls='--',label='OLS')
        ax.set_title(f'{kind}: '+('before' if kind=='LP' else 'after')+' 17:00 UTC');ax.set_xlabel('log10 recurrence time (s)')
        if ax.get_legend_handles_labels()[0]:ax.legend(fontsize=8)
    axes[0].set_ylabel('log10 approximate seismic moment (N m)')
    fig.suptitle('Candidate families; independent magnitudes and estimator controls')
    fig.tight_layout()
    for suffix in ('pdf','png'):fig.savefig(ROOT/f'results/figures/{screen}_moment_recurrence.{suffix}',dpi=300,bbox_inches='tight')
    plt.close(fig)
    pd.DataFrame(fits).to_csv(ROOT/f'results/tables/{output}_recurrence_regressions.csv',index=False)
    record=dict(common_station_screen=1 if args.permissive else 4,fits=fits,comparison_windows='LP before 17:00; VT after 17:00 UTC',primary_pairing='preceding',
                ransac=dict(min_samples=2,max_trials=1000,random_state=20261009,residual_threshold='sklearn default MAD of y'),
                limitations=['Family membership and approximate magnitudes independently computed','Original RANSAC controls unavailable',
                             'R squared all points distinguished from R squared inliers','OLS jackknife event pairs not independent family uncertainty',
                             'Low family count or missing VT family prevents validating the published contrasting populations'])
    (ROOT/f'results/tables/{output}_recurrence_execution.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))

if __name__=='__main__':main()
