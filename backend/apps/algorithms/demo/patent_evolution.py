"""
Patent Evolution algorithm.
Generates line chart showing annual evolution of patent publications.
"""
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import datetime
import textwrap
from pathlib import Path
import json
import io
from typing import Dict, Any
from django.conf import settings

from apps.algorithms.base import BaseAlgorithm, ChartResult
from apps.datasets.models import Dataset


class PatentEvolutionAlgorithm(BaseAlgorithm):
    """
    Algorithm for generating line chart of annual patent evolution.
    Reads data from Dataset.storage_path (JSON format).
    """
    
    def __init__(self):
        """Initialize algorithm."""
        super().__init__(
            algorithm_key="patent_evolution",
            algorithm_version="1.0"
        )
        
        self.first_column_name = "Year"
        self.second_column_name = "Number of Publications"
        self.historical_years = 20
        self.cutoff_year = datetime.datetime.now().year - 2
        self.trend_line_color = '#44b9be'
        self.chart_width = 10
        self.chart_height = 8
        self.x_axis_label = 'Año'
        self.y_axis_label = 'Número de Patentes Publicadas'
    
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
        
        # Load data
        df = self._load_dataset(dataset)
        
        # Rename columns if needed
        if len(df.columns) >= 2:
            if df.columns[0] != self.first_column_name or df.columns[1] != self.second_column_name:
                df.rename(columns={df.columns[0]: self.first_column_name, 
                                 df.columns[1]: self.second_column_name}, inplace=True)
        
        # Filter data
        df = df[(df[self.first_column_name] <= self.cutoff_year) & 
                (df[self.first_column_name] > (self.cutoff_year - self.historical_years))]
        
        # Complete years range
        complete_years = pd.DataFrame({
            self.first_column_name: range(df[self.first_column_name].min(), df[self.first_column_name].max() + 1)
        })
        
        # Merge to ensure all years present
        df = pd.merge(complete_years, df, on=self.first_column_name, how='left')
        df[self.second_column_name] = df[self.second_column_name].fillna(0)
        
        # Create chart
        plt.rcParams['svg.fonttype'] = 'none'
        plt.rcParams['font.sans-serif'] = ['Arial']
        
        fig, ax = plt.subplots(figsize=(self.chart_width, self.chart_height))
        ax.plot(df[self.first_column_name], df[self.second_column_name], 
                color=self.trend_line_color, marker='o', markersize=4, 
                label=self.y_axis_label, linewidth=1.5)
        
        # Labels
        ax.set_xlabel(self.x_axis_label, fontsize=18)
        ax.set_ylabel(self.y_axis_label, color="black", fontsize=18)
        ax.tick_params(axis='y', labelcolor="black")
        ax.tick_params(axis='y', color="black")
        
        # Grid
        ax.grid(True, color='lightgrey', linestyle='-', linewidth=0.35)
        
        # Legend
        def wrap_labels(labels, text_wrap_width=20):
            return ["\n".join(textwrap.wrap(label, width=text_wrap_width)) for label in labels]
        
        legend = ax.legend(loc='center left', bbox_to_anchor=(1, 0.9), fontsize=12, frameon=False)
        wrapped_labels = wrap_labels([text.get_text() for text in legend.get_texts()])
        for text, wrapped_label in zip(legend.get_texts(), wrapped_labels):
            text.set_text(wrapped_label)
        
        # Remove spines
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        
        # X-axis ticks
        ax.set_xticks(df[self.first_column_name].tolist())
        ax.tick_params(axis='x', rotation=45)
        
        # Annotations
        plt.figtext(0, -0.075,
                    '* Se muestran las publicaciones hasta hace 2 años, porque los documentos de patente suelen demorar hasta 18 meses en su publicación.',
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
            'type': 'line',
            'x_axis': self.x_axis_label,
            'y_axis': self.y_axis_label,
            'series': [
                {
                    'year': int(row[self.first_column_name]),
                    'publications': int(row[self.second_column_name])
                }
                for _, row in df.iterrows()
            ],
            'total_publications': int(df[self.second_column_name].sum()),
            'years_range': {
                'start': int(df[self.first_column_name].min()),
                'end': int(df[self.first_column_name].max())
            },
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
                'years_analyzed': len(df),
                'cutoff_year': self.cutoff_year
            }
        )

