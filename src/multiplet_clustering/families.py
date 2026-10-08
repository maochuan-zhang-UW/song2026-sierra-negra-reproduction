"""Connected components with positive edges; negative edges remain review candidates."""
import numpy as np
from src.template_matching.matching import pair_ncc


def network_similarity(event_a,event_b,maximum_lag_samples):
    # Keys encode station, component, and phase. No missing channels become zeroes.
    common=sorted(set(event_a)&set(event_b))
    scores=[pair_ncc(event_a[k],event_b[k],maximum_lag_samples)[0] for k in common]
    valid=[v for v in scores if np.isfinite(v)]
    return (float(np.mean(valid)),len(valid)) if valid else (float('nan'),0)


def connected_families(event_ids,edges,minimum_size=10,threshold=0.7):
    ids=list(event_ids)
    if len(ids)!=len(set(ids)):
        raise ValueError('Duplicate event IDs')
    parent={i:i for i in ids}
    def root(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]];i=parent[i]
        return i
    anti=[]
    for a,b,r in edges:
        if a not in parent or b not in parent:
            raise ValueError('Unknown event in edge')
        if not np.isfinite(r):continue
        if r > threshold:parent[root(a)]=root(b)
        if r < -threshold:anti.append((a,b,r))
    groups={}
    for i in ids:groups.setdefault(root(i),[]).append(i)
    families=[sorted(g) for g in groups.values() if len(g)>=minimum_size]
    return sorted(families,key=lambda g:g[0]),anti
