"""Read the native PyOcto FMM table; travel-time units are s, grid units km."""
import struct
from pathlib import Path
import numpy as np
from scipy.interpolate import RegularGridInterpolator


def load_travel_times(path):
    with Path(path).open('rb') as file:
        nx,nz,spacing=struct.unpack('iid',file.read(16))
        data=np.frombuffer(file.read(),dtype=np.float64)
    if nx<2 or nz<2 or spacing<=0 or len(data)!=2*nx*nz:
        raise ValueError('Invalid PyOcto travel-time table')
    arrays=data.reshape(2,nx,nz)
    coordinates=(np.arange(nx)*spacing,np.arange(nz)*spacing)
    return {phase:RegularGridInterpolator(coordinates,values,bounds_error=True)
            for phase,values in zip(('P','S'),arrays)}


def nearest_pick(query,picks):
    """Return nearest pick minus predicted arrival, in seconds; absent picks -> NaN."""
    query=np.asarray(query,dtype=float);picks=np.sort(np.asarray(picks,dtype=float))
    if not np.isfinite(query).all() or not np.isfinite(picks).all():raise ValueError('Finite times required')
    if not len(picks):return np.full(query.shape,np.nan)
    index=np.searchsorted(picks,query)
    left=picks[np.maximum(index-1,0)]-query
    right=picks[np.minimum(index,len(picks)-1)]-query
    return np.where(abs(left)<=abs(right),left,right)
