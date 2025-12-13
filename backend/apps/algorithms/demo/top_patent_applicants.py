"""
Top Patent Applicants algorithm.
Generates horizontal bar chart showing top n patent applicants by publications.
"""
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.colors as mcolors
from matplotlib.ticker import MaxNLocator, FuncFormatter
from pathlib import Path
import json
import io
import textwrap
from typing import Dict, Any
from django.conf import settings

from apps.algorithms.base import BaseAlgorithm, ChartResult
from apps.datasets.models import Dataset


class TopPatentApplicantsAlgorithm(BaseAlgorithm):
    """
    Algorithm for generating horizontal bar chart of top patent applicants.
    Reads data from Dataset.storage_path (JSON format).
    """
    
    def __init__(self):
        """Initialize algorithm."""
        super().__init__(
            algorithm_key="top_patent_applicants",
            algorithm_version="1.0"
        )
        
        self.first_column_name = "Applicants"
        self.second_column_name = "Number of Publications"
        self.gradient_color_min = '#4fc0e5'
        self.gradient_color_max = '#1e3d8f'
        self.chart_width = 10
        self.chart_height = 8
        self.x_axis_label = 'Número de Patentes Publicadas'
        self.y_axis_label = 'Solicitantes'
        self.text_wrap_width = 25
    
    def _load_dataset(self, dataset: Dataset) -> pd.DataFrame:
        """Load data from Dataset."""
        if dataset.storage_path.startswith('/') or ':' in dataset.storage_path:
            file_path = Path(dataset.storage_path)
        else:
            file_path = Path(settings.MEDIA_ROOT) / dataset.storage_path
        
        if not file_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {file_path}")
        
        if dataset.normalized_format == 'json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
        elif dataset.normalized_format == 'parquet':
            df = pd.read_parquet(file_path)
        else:
            raise ValueError(f"Unsupported format: {dataset.normalized_format}")
        
        return df
    
    def run(self, dataset: Dataset, params: Dict[str, Any]) -> ChartResult:
        """Execute algorithm on dataset."""
        import time
        start_time = time.time()
        
        top_n = params.get('top_n', 15)
        if not isinstance(top_n, int) or top_n < 1:
            raise ValueError("top_n must be a positive integer")
        
        # Load data
        df = self._load_dataset(dataset)
        
        # Rename columns if needed
        if len(df.columns) >= 2:
            if df.columns[0] != self.first_column_name or df.columns[1] != self.second_column_name:
                df.rename(columns={df.columns[0]: self.first_column_name, 
                                 df.columns[1]: self.second_column_name}, inplace=True)
        
        # Select top n applicants
        top_n_applicants = df.nlargest(top_n, self.second_column_name)
        top_n_applicants = top_n_applicants.sort_values(by=self.second_column_name, ascending=True)
        
        # Generate colormap
        cmap = mcolors.LinearSegmentedColormap.from_list("mycmap", [self.gradient_color_min, self.gradient_color_max])
        
        # Normalize values
        min_val = top_n_applicants[self.second_column_name].min()
        max_val = top_n_applicants[self.second_column_name].max()
        normalized_vals = [
            (x - min_val) / (max_val - min_val) if max_val > min_val else 0.5
            for x in top_n_applicants[self.second_column_name]
        ]
        
        colors = [cmap(val) for val in normalized_vals]
        
        # Wrap labels
        def wrap_labels(labels, text_wrap_width):
            return ["\n".join(textwrap.wrap(label, width=text_wrap_width)) for label in labels]
        
        top_n_applicants[self.first_column_name] = wrap_labels(top_n_applicants[self.first_column_name], self.text_wrap_width)
        top_n_applicants[self.first_column_name] = top_n_applicants[self.first_column_name].apply(lambda x: x.strip().title())
        
        # Create chart
        plt.rcParams['svg.fonttype'] = 'none'
        plt.rcParams['font.sans-serif'] = ['Arial']
        
        fig, ax = plt.subplots(figsize=[self.chart_width, self.chart_height])
        bars = ax.barh(top_n_applicants[self.first_column_name], top_n_applicants[self.second_column_name], color=colors)
        
        # Format X-axis
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: '{:,.0f}'.format(x)))
        
        # Calculate total
        total_publications = df[self.second_column_name].sum()
        
        # Add labels
        label_offset = 0.025 * max_val
        for i, bar in enumerate(bars):
            num_publications = top_n_applicants[self.second_column_name].iloc[i]
            percentage = (num_publications / total_publications) * 100
            ax.text(
                bar.get_width() + label_offset,
                bar.get_y() + bar.get_height() / 2,
                f'{num_publications:,.0f} ({percentage:.2f}%)',
                ha='left', va='center'
            )
        
        # Remove spines
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.xaxis.set_ticks_position('none')
        ax.yaxis.set_ticks_position('none')
        
        # Labels
        ax.set_xlabel(self.x_axis_label, fontsize=18, labelpad=12, color="black")
        ax.set_ylabel(self.y_axis_label, fontsize=18, labelpad=12, color="black")
        
        # Annotations
        plt.figtext(-0.1, -0.075,
                    '* Los solicitantes de patentes son quienes tienen el derecho legal de presentar y reclamar la protección de una invención, lo que les otorga exclusividad para explotarla comercialmente.',
                    ha="left", fontsize=12, color="black", wrap=True)
        
        plt.figtext(-0.1, -0.15,
                    '** Un solicitante puede ser una persona física o jurídica que busca proteger una invención mediante una patente, asegurando su control y aprovechamiento exclusivo de la innovación.',
                    ha="left", fontsize=12, color="black", wrap=True)
        
        # Save to bytes
        png_buffer = io.BytesIO()
        plt.savefig(png_buffer, format='png', bbox_inches='tight', dpi=100)
        png_bytes = png_buffer.getvalue()
        png_buffer.close()
        
        svg_buffer = io.StringIO()
        plt.savefig(svg_buffer, format='svg', bbox_inches='tight')
        svg_text = svg_buffer.getvalue()
        svg_buffer.close()
        plt.close()
        
        # Prepare chart_data for AI
        chart_data = {
            'type': 'horizontal_bar',
            'x_axis': self.x_axis_label,
            'y_axis': self.y_axis_label,
            'series': [
                {
                    'name': row[self.first_column_name],
                    'value': int(row[self.second_column_name]),
                    'percentage': round((row[self.second_column_name] / total_publications) * 100, 2)
                }
                for _, row in top_n_applicants.iterrows()
            ],
            'total_publications': int(total_publications),
            'top_n': top_n,
            'warnings': []
        }
        
        execution_time = time.time() - start_time
        
        return ChartResult(
            png_bytes=png_bytes,
            svg_text=svg_text,
            chart_data=chart_data,
            meta={
                'algorithm_key': self.algorithm_key,
                'algorithm_version': self.algorithm_version,
                'execution_time_seconds': round(execution_time, 2),
                'top_n': top_n,
                'total_applicants': len(df),
                'displayed_applicants': len(top_n_applicants)
            }
        )

