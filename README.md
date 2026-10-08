# Song (2026) Sierra Negra reproduction

**Status: partial, data-limited reproduction.** Actual computations use 219 June 26, 2018 events recovered from Bell et al.'s public original catalog. No enhanced catalog, measured LP/VT classifications, observational families, GNSS solutions, or published regressions have been produced. GitHub publication is blocked by absent authentication and local network restrictions.

The project implements and tests core numerical methods, generates partial main Figures 1, 2, and 4 and an original conceptual Figure 6, and compiles an assessment report. Figures 3 and 5 and the supplement remain unreproduced. Synthetic tests are never presented as volcanic observations.

- [Compiled report](report/main.pdf) and [LaTeX source](report/main.tex)
- [Assessment and figure inventory](docs/reproducibility.md)
- [Limitations and continuation requirements](docs/limitations.md)
- [Comparison table](results/tables/comparison.csv)
- [Original catalog](results/catalogs/original_20180626.csv), [phase statistics](results/tables/original_phase_statistics.csv), [provenance](results/tables/catalog_provenance.json)
- [Executed analysis notebook with saved figures](report/analysis.ipynb)

Study: Song et al. (2026), Nature Communications 17:2040, https://doi.org/10.1038/s41467-026-68645-4. Original data: Bell et al. (2021), https://doi.org/10.1038/s41467-021-21596-4; https://doi.org/10.5281/zenodo.4389190. Network: 8G (2018–2019), https://doi.org/10.7914/SN/8G_2018. Volpick: https://github.com/zhong-yy/volpick.

## Rebuild available products offline

The original CSV and figure data are committed. The usable local environment is Python 3.6.8 with versions in `environment/requirements.txt`; it is already installed on this host. For a fresh install, provision these historical versions in a compatible environment. Optional waveform dependencies need a separate modern Python environment; they are not validated here.

```bash
cd /data/data1/mczhang8-scratch/song2026-sierra-negra-reproduction
source scripts/env.sh
bash scripts/build.sh
python3 -m unittest discover -s tests -v
python3 scripts/rebuild_from_csv.py
python3 scripts/make_notebook.py
(cd report && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex)
```

All caches, compilation outputs, and temporary files are redirected under this repository on `/data`. Raw datasets are ignored. The executed historical dependency versions are recorded; do not silently update them for comparison runs.

## Acquire sources when network access is available

```bash
source scripts/env.sh
python3 scripts/acquire.py
python3 scripts/analyze.py --catalog data/raw/IGUANA_Cat_V1.eventlist
```

`acquire.py` records failures and refuses HTML masquerading as PDFs or catalogs. In the present run every direct download failed. The recovered raw text subset exists locally but is ignored; the committed derived CSV supports independent offline figure regeneration. Verify the full event-list MD5 against `8935d6cc8189ff1991ba966666aacd66` before treating a later acquisition as identical.

In an environment with ObsPy installed, `scripts/acquire_waveforms.py` requests one-hour 8G chunks and response metadata and records station-level failures/gaps. It does not retrieve the separately administered EC records. Waveform collection, model downloads, picking, association and relocation have not run. Review the supplement and fill unresolved settings in `config/paper.json` before scientific execution.

`src/earthquake_detection/volpick.py` exposes original public EQTransformer weights with mandatory P/S thresholds. `scripts/analyze_windows.py --help` describes classification/clustering/recurrence on supplied real, preprocessed five-second velocity windows, requiring explicit lag, interval pairing, regression transform, and standard-deviation choices. It writes measured/inherited FI provenance and candidate anti-repeaters requiring manual review. It is not an integrated association/relocation pipeline. Template correlation and detection kernels are in `src/template_matching/`; family and statistics routines are small standalone functions.

## Files and provenance

`config/paper.json` separates known settings from unresolved nulls. Figure generation uses observations from the original catalog only. Source locations, negative depths, and low magnitudes are preserved. Source depth datum is unresolved. Phase boundaries use the paper's rounded times; the actual main earthquake at 09:15:32.299 is included in phase 2. Map zooms count omitted locations explicitly. Published count inconsistencies are retained in the comparison table.

`AGENTS.md` and `brad-lipovsky-academic-style-guide.md` were recovered from the user-specified https://github.com/bradlipovsky/vdv-damage repository using browser text. The style guide includes all 338 source lines. These externally authored instructions retain their original attribution; the MIT license applies to original project code only.

## Publish after authentication and connectivity are restored

```bash
gh auth status
gh repo create song2026-sierra-negra-reproduction --public --source=. --remote=origin --push
gh repo view --json url
git ls-remote origin refs/heads/main
```

Do not commit raw waveforms, tokens, SSH credentials, checkpoint weights, or caches. Repository creation and push have not succeeded in this session; a local Git repository is prepared for continuation.
