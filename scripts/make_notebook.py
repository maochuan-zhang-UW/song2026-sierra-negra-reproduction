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
nb.cells.append(nbformat.v4.new_markdown_cell('# Original-catalog analysis\n\nActual archived Bell et al. observations, not the enhanced Song catalog. Outputs are computed and retained. Continuous-waveform and GNSS results are unavailable.'))
codes=["from pathlib import Path\nimport os, sys\nROOT = Path.cwd()\nif ROOT.name == 'report': ROOT = ROOT.parent\nos.chdir(str(ROOT))\nsys.path.insert(0, str(ROOT))\nos.environ['MPLCONFIGDIR'] = str(ROOT / '.cache/matplotlib')\nimport pandas as pd\nfrom src.visualization.figures import catalog_figures, conceptual_figure\ndf = pd.read_csv('results/catalogs/original_20180626.csv')\nprint('Original events:', len(df))\nprint(df.groupby('phase').size())\ncatalog_figures(df, 'results/figures')\nconceptual_figure('results/figures')"]
for name in ['fig01_original_catalog','fig02_original_timeline','fig04_original_phase_maps','fig06_conceptual_sequence']:
    codes.append("from IPython.display import Image, display\ndisplay(Image(filename='results/figures/{}.png'))".format(name))
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
