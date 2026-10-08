"""Read the public Bell et al. event list without filtering locations or depths."""
from pathlib import Path
import pandas as pd
import numpy as np


def read_eventlist(path, date='2018-06-26'):
    records = []
    for line in Path(path).read_text().splitlines():
        p = line.split()
        if len(p) < 15 or p[0] != 'EVENT' or p[1] == 'EVENT_ID':
            continue
        if p[2] != date:
            continue
        records.append(dict(event_id=p[1], origin_time=p[2]+'T'+p[3]+'Z',
                            latitude=float(p[4]), latitude_error=float(p[5]),
                            longitude=float(p[6]), longitude_error=float(p[7]),
                            depth_catalog_km=float(p[8]), depth_error=float(p[9]),
                            rms_seconds=float(p[10]), azimuth_gap_deg=float(p[11]),
                            magnitude=float(p[12]), phase_pick_count=int(p[13]),
                            provenance='Bell et al. (2021); Zenodo 4389190; original catalog'))
    if not records:
        raise ValueError('No events found for requested date')
    df = pd.DataFrame(records)
    if df.event_id.duplicated().any():
        raise ValueError('Duplicate event IDs')
    df['origin_time'] = pd.to_datetime(df.origin_time, utc=True)
    numeric = df.select_dtypes(include=[np.number])
    if not np.isfinite(numeric.values).all():
        raise ValueError('Non-finite catalog quantities')
    if not df.latitude.between(-90, 90).all() or not df.longitude.between(-180, 180).all():
        raise ValueError('Invalid coordinates')
    df = df.sort_values('origin_time').reset_index(drop=True)
    day = pd.Timestamp(date, tz='UTC')
    df['utc_hour'] = (df.origin_time-day).dt.total_seconds()/3600
    df['phase'] = np.searchsorted([9.25, 17, 19+40/60], df.utc_hour, side='right')+1
    return df


def validate_catalog(df):
    required = ['event_id', 'origin_time', 'latitude', 'longitude', 'magnitude']
    for col in required:
        if col not in df or df[col].isna().any():
            raise ValueError('Missing required catalog field: '+col)
    if df.event_id.duplicated().any():
        raise ValueError('Duplicate event IDs')
    return True


def phase_boundary_sensitivity(df):
    """Recalculate counts for the two onset times explicitly reported in the article."""
    rows=[]
    for eruption in [19+35/60,19+40/60]:
        phases=np.searchsorted([9.25,17,eruption],df.utc_hour,side='right')+1
        row=dict(eruption_hour_utc=eruption)
        row.update({'phase{}'.format(i):int((phases==i).sum()) for i in range(1,5)})
        rows.append(row)
    return pd.DataFrame(rows)
