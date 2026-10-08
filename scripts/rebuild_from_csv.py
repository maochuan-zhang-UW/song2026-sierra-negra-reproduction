#!/usr/bin/env python3
"""Regenerate figures from committed derived observations, without network access."""
from pathlib import Path
import pandas as pd
from src.data_processing.catalog import phase_boundary_sensitivity
from src.visualization.figures import catalog_figures,conceptual_figure
ROOT=Path(__file__).resolve().parents[1]
df=pd.read_csv(str(ROOT/'results/catalogs/original_20180626.csv'))
phase_boundary_sensitivity(df).to_csv(str(ROOT/'results/tables/phase_boundary_sensitivity.csv'),index=False)
catalog_figures(df,ROOT/'results/figures');conceptual_figure(ROOT/'results/figures')
