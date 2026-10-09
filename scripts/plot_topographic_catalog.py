#!/usr/bin/env python3
"""Retrieve a public numerical DSM and plot candidate map/depth counterpart."""
import hashlib,json,urllib.request
from pathlib import Path
import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import from_bounds
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
URL='https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_S01_00_W092_00_DEM/Copernicus_DSM_COG_10_S01_00_W092_00_DEM.tif'
NOTICE='produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018\nprovided under COPERNICUS by the European Union and ESA; all rights reserved'


def main():
    path=ROOT/'data/raw/copernicus_sierra_negra.tif'
    if not path.exists():urllib.request.urlretrieve(URL,path)
    bounds=(-91.22,-.90,-91.08,-.76)
    with rasterio.open(path) as source:
        if source.crs.to_epsg()!=4326:raise ValueError('Unexpected DSM coordinate frame')
        window=from_bounds(*bounds,transform=source.transform).round_offsets().round_lengths()
        data=source.read(1,window=window,masked=True)
        extent=rasterio.windows.bounds(window,source.transform)
        spacing=source.res;shape=source.shape
    if data.count()!=data.size or not np.isfinite(data).all():raise ValueError('Incomplete map DSM')
    catalog=pd.read_csv(ROOT/'results/catalogs/enhanced_classified_catalog.csv')
    stations=pd.read_csv(ROOT/'results/tables/acquired_station_metadata.csv')
    fig,axes=plt.subplots(1,2,figsize=(12,6),gridspec_kw={'width_ratios':[1.25,1]})
    west,south,east,north=extent
    image=axes[0].imshow(data,extent=(west,east,south,north),origin='upper',cmap='terrain')
    fig.colorbar(image,ax=axes[0],label='Copernicus surface elevation (m; EGM2008)')
    for kind,color in [('VT','#bd5732'),('LP','#255e9a')]:
        sub=catalog[catalog.type==kind]
        axes[0].scatter(sub.longitude,sub.latitude,s=7,c=color,alpha=.45,label=kind)
        axes[1].scatter(sub.latitude,sub.depth,s=7,c=color,alpha=.45,label=kind)
    axes[0].scatter(stations.longitude,stations.latitude,marker='^',c='black',s=35,label='Station metadata')
    for station in stations.itertuples():
        if west<station.longitude<east and south<station.latitude<north:axes[0].annotate(station.station,(station.longitude,station.latitude),fontsize=6,xytext=(3,3),textcoords='offset points')
    axes[0].set_xlim(west,east);axes[0].set_ylim(south,north);axes[0].set_xlabel('Longitude');axes[0].set_ylabel('Latitude');axes[0].legend(fontsize=7)
    axes[1].invert_yaxis();axes[1].set_xlabel('Latitude');axes[1].set_ylabel('Approximate depth (km below sea level)');axes[1].legend(fontsize=7)
    fig.suptitle('Main Figure 1 counterpart: numerical DSM and independent candidate locations')
    fig.text(.5,.015,NOTICE,ha='center',fontsize=6)
    fig.tight_layout(rect=(0,.08,1,.95))
    for suffix in ('pdf','png'):fig.savefig(ROOT/f'results/figures/enhanced_topographic_catalog.{suffix}',dpi=300,bbox_inches='tight')
    record=dict(source_url=URL,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),tile_shape=list(shape),spacing_degrees=list(spacing),map_bounds=list(bounds),
                map_elevation_min_m=float(data.min()),map_elevation_max_m=float(data.max()),map_samples=int(data.count()),
                type='Copernicus GLO-30 digital surface model, not reconstructed eruption topography',
                attribution=NOTICE,license_url='https://docs.sentinel-hub.com/api/latest/static/files/data/dem/resources/license/License-COPDEM-30.pdf',
                limitations=['DSM surface and EGM2008 datum not used to change station or source locations','Not original source topographic layer',
                             'Published fault traces and cross-section orientation unavailable','Event depths from approximate 1-D model, not HypoDD'])
    (ROOT/'results/tables/topographic_map_execution.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))
if __name__=='__main__':main()
