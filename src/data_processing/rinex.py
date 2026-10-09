"""Strict GPS RINEX 2 observation reader; timestamps returned in UTC."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import numpy as np
import pandas as pd


def read_observations(path):
    lines = iter(Path(path).read_text().splitlines())
    header = {}
    types = []
    for line in lines:
        label = line[60:].strip()
        if label == '# / TYPES OF OBSERV':
            types.extend(line[6:60].split())
        elif label == 'APPROX POSITION XYZ':
            header['approx_xyz_m'] = list(map(float, line[:60].split()))
        elif label == 'INTERVAL':
            header['interval_s'] = float(line[:10])
        elif label == 'LEAP SECONDS':
            header['gps_minus_utc_s'] = int(line[:6])
        elif label == 'TIME OF FIRST OBS':
            if line[48:51].strip() != 'GPS':
                raise ValueError('Only explicitly labelled GPS epochs supported')
        elif label == 'END OF HEADER':
            break
    if not types or 'gps_minus_utc_s' not in header:
        raise ValueError('Missing observation types or GPS/UTC offset')
    header['observation_types'] = types
    rows = []
    for line in lines:
        if not line.strip():
            continue
        flag, count = int(line[28:29]), int(line[29:32])
        if flag not in (0, 1):
            for _ in range(count):
                next(lines)
            continue
        year = int(line[1:3]); year += 2000 if year < 80 else 1900
        gps = datetime(year, int(line[4:6]), int(line[7:9]), int(line[10:12]),
                       int(line[13:15]), tzinfo=timezone.utc) + timedelta(seconds=float(line[15:26]))
        utc = gps - timedelta(seconds=header['gps_minus_utc_s'])
        satellites = line[32:68].ljust(36)
        for _ in range((count - 1) // 12):
            satellites += next(lines)[32:68].ljust(36)
        for i in range(count):
            satellite = satellites[3*i:3*i+3].strip()
            fields = ''.join(next(lines).ljust(80) for _ in range((len(types)+4)//5))
            row = dict(time_utc=utc, satellite=satellite, epoch_flag=flag)
            for j, observable in enumerate(types):
                field = fields[j*16:j*16+16]
                row[observable] = float(field[:14]) if field[:14].strip() else np.nan
                if observable.startswith('L'):
                    row[observable+'_lli'] = int(field[14]) if field[14:15].strip() else 0
            rows.append(row)
    frame = pd.DataFrame(rows)
    if frame.empty or frame.duplicated(['time_utc', 'satellite']).any():
        raise ValueError('Empty or duplicate epoch/satellite observations')
    if not frame.time_utc.is_monotonic_increasing:
        raise ValueError('Nonchronological observations')
    return header, frame
