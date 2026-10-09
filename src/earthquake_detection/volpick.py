"""Direct public-model inference, avoiding the stalled asynchronous stream wrapper."""
import numpy as np


def annotate_contiguous(model,stream,batch_size=64,overlap=3000,blinding=(500,500)):
    """Use the model's own preprocessing, forward and postprocessing methods.

    Require three common, gap-free 100-Hz channels. Average valid overlapping
    probabilities; leave uncovered edge samples NaN. No waveform gaps are filled.
    """
    import torch
    from obspy import Stream,Trace
    if len(stream)!=3:raise ValueError('Require three common components')
    traces=[]
    for component in model.component_order:
        selected=stream.select(component=component)
        if len(selected)!=1:raise ValueError('Missing or duplicate component')
        traces.append(selected[0])
    reference=traces[0].stats
    for trace in traces:
        if trace.stats.sampling_rate!=100 or trace.stats.starttime!=reference.starttime or trace.stats.npts!=reference.npts:
            raise ValueError('Component sample grids differ')
        if np.ma.isMaskedArray(trace.data) or not np.isfinite(trace.data).all():
            raise ValueError('Inference requires contiguous finite data')
    data=np.stack([t.data for t in traces]).astype(np.float32)
    n=data.shape[1];width=model.in_samples
    if n<width:raise ValueError('Less than a model window of data')
    starts=list(range(0,n-width+1,width-overlap))
    if starts[-1]!=n-width:starts.append(n-width)
    total=np.zeros((n,3),dtype=np.float64);count=np.zeros((n,3),dtype=np.int32)
    with torch.inference_mode():
        for offset in range(0,len(starts),batch_size):
            positions=starts[offset:offset+batch_size]
            batch=torch.from_numpy(np.stack([data[:,s:s+width] for s in positions]))
            normalized=model.annotate_batch_pre(batch,{})
            output=model.annotate_batch_post(model(normalized),None,{'blinding':blinding}).cpu().numpy()
            for position,prediction in zip(positions,output):
                valid=np.isfinite(prediction)
                total[position:position+width]+=np.where(valid,prediction,0)
                count[position:position+width]+=valid
    averaged=np.full_like(total,np.nan)
    np.divide(total,count,out=averaged,where=count>0)
    annotations=Stream()
    for i,phase in enumerate(['Detection']+list(model.phases)):
        header=dict(network=reference.network,station=reference.station,location=reference.location,
                    channel='EQTransformer_'+phase,starttime=reference.starttime,sampling_rate=100)
        annotations+=Trace(averaged[:,i].astype(np.float32),header=header)
    return annotations


def pick_stream(stream,p_threshold,s_threshold,model=None):
    if p_threshold is None or s_threshold is None:
        raise ValueError('Explicit phase thresholds required')
    if model is None:
        import seisbench.models as sbm
        model=sbm.EQTransformer.from_pretrained('volpick');model.eval()
    annotations=annotate_contiguous(model,stream)
    picks=[]
    for phase,threshold in [('P',p_threshold),('S',s_threshold)]:
        picks.extend(model.picks_from_annotations(annotations.select(channel='EQTransformer_'+phase),threshold,phase))
    return picks
