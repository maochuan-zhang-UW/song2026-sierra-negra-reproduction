"""Public original EQTransformer weights; thresholds are mandatory inputs.
Dependency-bound adapter: not executed in the offline run.
"""
def pick_stream(stream,p_threshold,s_threshold):
    if p_threshold is None or s_threshold is None:
        raise ValueError('Thresholds require supplement or documented sensitivity settings')
    import seisbench.models as sbm
    model=sbm.EQTransformer.from_pretrained('volpick')
    result=model.classify(stream,P_threshold=p_threshold,S_threshold=s_threshold,
                          batch_size=256,overlap=5500,blinding=(500,500),stacking='avg')
    # Overlap/blinding are public model example choices, not verified Song settings.
    return result.picks
