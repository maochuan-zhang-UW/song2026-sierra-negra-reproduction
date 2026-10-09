#!/usr/bin/env python3
"""Execute notebook cells in-process through IPython; save rich outputs intact.
No kernel sockets are needed on this restricted host. Errors abort creation.
"""
import os,json,sys
from pathlib import Path
import nbformat
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output
ROOT=Path(__file__).resolve().parents[1]
os.chdir(str(ROOT));sys.path.insert(0,str(ROOT))
nb=nbformat.v4.new_notebook()
nb.metadata.kernelspec=dict(display_name='Python 3',language='python',name='python3')
nb.metadata.language_info=dict(name='python',version=sys.version.split()[0])
nb.cells.append(nbformat.v4.new_markdown_cell('# Original-catalog analysis\n\nActual archived Bell et al. observations, not the enhanced Song catalog. Outputs are computed and retained. Raw 8G, EC and PAYG waveforms have been acquired; S5 uses independently processed ground velocity. An independent 1543-candidate template-expanded catalog and GNSS processing are available; source memberships and exact regression agreement remain unverified.'))
codes=["from pathlib import Path\nimport os, sys\nROOT = Path.cwd()\nif ROOT.name == 'report': ROOT = ROOT.parent\nos.chdir(str(ROOT))\nsys.path.insert(0, str(ROOT))\nos.environ['MPLCONFIGDIR'] = str(ROOT / '.cache/matplotlib')\nimport pandas as pd\nfrom src.visualization.figures import catalog_figures, conceptual_figure\ndf = pd.read_csv('results/catalogs/original_20180626.csv')\nprint('Original events:', len(df))\nprint(df.groupby('phase').size())\ncatalog_figures(df, 'results/figures')\nconceptual_figure('results/figures')"]
for name in ['fig01_original_catalog','fig02_original_timeline','fig04_original_phase_maps','fig06_conceptual_sequence']:
    codes.append("from IPython.display import Image, display\ndisplay(Image(filename='results/figures/{}.png'))".format(name))
codes.append("coverage = pd.read_csv('results/tables/waveform_coverage.csv')\nprint('Acquired channels:', len(coverage))\nprint(coverage.groupby('day_fraction').size())\nprint(pd.read_csv('results/tables/stations.csv').to_string(index=False))")
codes.append("combined = pd.read_csv('results/tables/acquired_station_coverage.csv')\nprint('Combined acquired station coverage:')\nprint(combined.to_string(index=False))\nprint('EC observations are picked; nine-station association is a separate coverage experiment.')")
for name in ['fig01_all_stations','figS05_payg_dayplots','phase_pick_counts']:
    codes.append("from IPython.display import Image, display\ndisplay(Image(filename='results/figures/{}.png'))".format(name))
codes.append("import json\nexecution = json.loads(Path('results/tables/volpick_execution.json').read_text())\nprint('Picking status:', execution['status'])\nprint('Candidate phase counts:', execution['phase_counts'])\nprint('These are phase picks, not associated earthquake events.')")
codes.append("print('Separate VCH1 original entries:', len(pd.read_csv('results/catalogs/vch1_original_20180626.csv')))\nprint('VCH1 entries are not merged with the located catalog.')")
for name in ['gnss_independent_ppp','gnss_relative_baseline','approximate_association']:
    codes.append("from IPython.display import Image, display\ndisplay(Image(filename='results/figures/{}.png'))".format(name))
codes.append("import json\nprint(json.dumps(json.loads(Path('results/tables/gnss_ppp_analysis.json').read_text()), indent=2))\nprint('Independent PPP; original GIPSY settings differ. VCH1 skipped; GV03 lacks earthquake interval.')")
codes.append("print(json.dumps(json.loads(Path('results/tables/approximate_association.json').read_text()), indent=2))\nprint('Approximate associations, not original relocated enhanced catalog.')")
codes.append("print(json.dumps(json.loads(Path('results/tables/velocity_sensitivity.json').read_text()), indent=2))")
for name in ['enhanced_frequency_families','enhanced_phase_maps','enhanced_magnitude_timeline','enhanced_permissive_moment_recurrence','supp_template_fi_comparison','gnss_intrusion_bend','enhanced_topographic_catalog','supp_candidate_distributions','supp_spatial_LP_VT','supp_family_waveforms','supp_family_periodicity','supp_before_after_matching']:
    codes.append("from IPython.display import Image, display\ndisplay(Image(filename='results/figures/{}.png'))".format(name))
for name in ['template_matching_execution','matched_window_execution','nine_station_association','enhanced_family_execution','enhanced_permissive_family_execution','matched_magnitude_execution','observed_permissive_recurrence_execution','gnss_bend_execution','family_periodicity_execution','topographic_map_execution','template_control_execution']:
    codes.append("print(json.dumps(json.loads(Path('results/tables/{}.json').read_text()), indent=2))".format(name))
codes.append("print(pd.read_csv('results/tables/template_threshold_sensitivity.csv').to_string(index=False))")
shell=InteractiveShell.instance()
for count,code in enumerate(codes,1):
    with capture_output() as captured:
        result=shell.run_cell(code,store_history=True)
    if result.error_before_exec or result.error_in_exec:
        raise RuntimeError('Notebook execution failed')
    outputs=[]
    if captured.stdout:outputs.append(nbformat.v4.new_output('stream',name='stdout',text=captured.stdout))
    if captured.stderr:outputs.append(nbformat.v4.new_output('stream',name='stderr',text=captured.stderr))
    for output in captured.outputs:
        outputs.append(nbformat.v4.new_output('display_data',data=output.data,metadata=output.metadata))
    nb.cells.append(nbformat.v4.new_code_cell(code,execution_count=count,outputs=outputs))
nbformat.validate(nb)
nbformat.write(nb,str(ROOT/'report/analysis.ipynb'))
print('Executed {} cells; saved notebook with figure outputs'.format(len(codes)))
