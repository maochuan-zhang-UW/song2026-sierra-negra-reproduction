"""Figures use only actual original-catalog observations or labelled interpretations."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse,Polygon

TIMES=[9.25,17,19+40/60]
COLORS=['#2471a3','#d4ac0d','#d35400']


def save(fig,path):
    fig.savefig(str(path)+'.pdf',dpi=300,bbox_inches='tight')
    fig.savefig(str(path)+'.png',dpi=300,bbox_inches='tight')
    plt.close(fig)


def boundaries(ax):
    for t,c in zip(TIMES,COLORS):ax.axvline(t,color=c,ls='--',lw=1)
    ax.set_xlim(0,24);ax.set_xticks(np.arange(0,25,3));ax.set_xlabel('26 June 2018, hour UTC')


def catalog_figures(df,directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    fig,axes=plt.subplots(1,3,figsize=(12,4))
    for ax in axes[:2]:
        sc=ax.scatter(df.longitude,df.latitude,c=df.utc_hour,s=14,cmap='viridis',vmin=0,vmax=24)
        ax.set_xlabel('Longitude (degrees east)');ax.set_ylabel('Latitude (degrees north)')
        ax.grid(alpha=.2)
    axes[0].set_title('(a) All catalog locations', fontsize=10)
    axes[1].set_title('(b) Caldera vicinity (zoom)', fontsize=10)
    axes[1].set_xlim(-91.21,-91.07);axes[1].set_ylim(-.88,-.75)
    shock=df.loc[df.magnitude.idxmax()]
    axes[1].scatter(shock.longitude,shock.latitude,marker='*',s=180,c='cyan',edgecolor='k')
    axes[2].scatter(df.latitude,df.depth_catalog_km,c=df.utc_hour,s=14,cmap='viridis',vmin=0,vmax=24)
    axes[2].invert_yaxis();axes[2].set_xlabel('Latitude (degrees north)');axes[2].set_ylabel('Catalog depth (km)')
    axes[2].set_title('(c) Latitude/depth projection', fontsize=10)
    fig.colorbar(sc,ax=axes.tolist(),label='Hour UTC',shrink=.75)
    fig.suptitle('Figure 1 partial: original catalog; station, fault and terrain layers unavailable',fontsize=10)
    save(fig,directory/'fig01_original_catalog')

    fig,axes=plt.subplots(2,1,figsize=(9,6),sharex=True)
    axes[0].step(np.r_[0,df.utc_hour,24],np.r_[0,np.arange(1,len(df)+1),len(df)],where='post',color='k')
    axes[0].set_ylabel('Cumulative original events')
    axes[1].scatter(df.utc_hour,df.magnitude,s=12,c='k');axes[1].set_ylabel('Original catalog magnitude')
    for ax in axes:boundaries(ax);ax.grid(alpha=.2)
    fig.suptitle('Figure 2 partial: Bell et al. original catalog; GNSS and enhanced catalog unavailable',fontsize=10)
    fig.tight_layout();save(fig,directory/'fig02_original_timeline')

    fig,axes=plt.subplots(2,2,figsize=(10,8),sharex=True,sharey=True)
    for phase,ax in enumerate(axes.ravel(),1):
        sub=df[df.phase==phase]
        sc=ax.scatter(sub.longitude,sub.latitude,c=sub.utc_hour,s=20,cmap='viridis',vmin=0,vmax=24)
        inside=sub.longitude.between(-91.21,-91.07)&sub.latitude.between(-.88,-.75)
        ax.set_title('Phase {}: {} events; {} outside zoom'.format(phase,len(sub),int((~inside).sum())))
        ax.set_xlim(-91.21,-91.07);ax.set_ylim(-.88,-.75);ax.grid(alpha=.2)
        ax.set_xlabel('Longitude (degrees east)');ax.set_ylabel('Latitude (degrees north)')
    fig.colorbar(sc,ax=axes.ravel().tolist(),label='Hour UTC',shrink=.7)
    fig.suptitle('Figure 4 partial: original events colored by time; FI and GNSS unavailable',fontsize=10)
    save(fig,directory/'fig04_original_phase_maps')


def conceptual_figure(directory):
    fig,axes=plt.subplots(1,4,figsize=(15,4),sharey=True)
    names=['09:15 UTC\nFault earthquake','~11:15 to 17:00 UTC\nLP observations','~17:00 UTC\nIntrusion inferred','19:35 to 19:40 UTC\nEruption onset']
    for i,ax in enumerate(axes):
        ax.set_xlim(0,10);ax.set_ylim(-3,.8);ax.axis('off');ax.set_title(names[i],fontsize=10)
        ax.plot([0,2,3,7,8,10],[0,0,-.25,-.25,0,0],color='saddlebrown',lw=2)
        ax.add_patch(Ellipse((5,-2),6,.4,color='tomato',alpha=.8))
        ax.text(5,-2.5,'Sill-like reservoir (~2 km)',ha='center',fontsize=8)
        ax.plot([2.3,3.5],[-.1,-1.9],c='k',lw=2)
        if i==0:
            ax.scatter(2.8,-.8,c='gold',edgecolor='k',marker='*',s=180)
            ax.annotate('Slip',xy=(2.3,-.3),xytext=(.4,-1.2),arrowprops={'arrowstyle':'->'},fontsize=9)
        if i==1:
            ax.scatter([2.7,3,3.2],[-.7,-1,-1.4],c='royalblue',s=35)
            ax.text(6.5,-.9,'Reported LP sources\nFluid pressurization\nis a hypothesis',ha='center',fontsize=9)
        if i>=2:
            ax.plot([3.2,2.5,1.8],[-1.9,-.9,0],color='red',lw=4)
            ax.text(6,-.9,'Reservoir drainage\nand magma ascent',ha='center',fontsize=9)
        if i==3:
            ax.plot([1.8,1.4,.7],[0,.4,.2],color='red',lw=3)
    fig.suptitle('Figure 6: original conceptual interpretation; no numerical simulation; geometry not to scale',fontsize=11,y=1.02)
    fig.subplots_adjust(top=.80)
    save(fig,Path(directory)/'fig06_conceptual_sequence')
