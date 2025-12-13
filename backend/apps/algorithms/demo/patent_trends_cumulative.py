"""
Patent Trends Cumulative algorithm.
Generates dual-axis line chart showing annual and cumulative evolution.
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


class PatentTrendsCumulativeAlgorithm(BaseAlgorithm):
    """
    Algorithm for generating dual-axis line chart of annual and cumulative patent evolution.
    Reads data from Dataset.storage_path (JSON format).
    """
    
    def __init__(self):
        """Initialize algorithm."""
        super().__init__(
            algorithm_key="patent_trends_cumulative",
            algorithm_version="1.0"
        )
        
        self.first_column_name = "Year"
        self.second_column_name = "Number of Publications"
        self.historical_years = 20
        self.cutoff_year = datetime.datetime.now().year - 2
        self.trend_line_color = '#44b9be'
        self.cumulative_line_color = '#001f3f'
        self.chart_width = 10
        self.chart_height = 8
        self.x_axis_label = 'Año'
        self.y_axis_label = 'Número de Patentes Publicadas'
        self.y_axis_label_2 = 'Publicaciones de Patentes Acumulativas'
    
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
        
        # Calculate cumulative
        df[self.y_axis_label_2] = df[self.second_column_name].cumsum()
        
        # Create chart with dual axes
        plt.rcParams['svg.fonttype'] = 'none'
        plt.rcParams['font.sans-serif'] = ['Arial']
        
        fig, ax1 = plt.subplots(figsize=(self.chart_width, self.chart_height))
        
        # Plot annual evolution
        ax1.plot(df[self.first_column_name], df[self.second_column_name], 
                color=self.trend_line_color, marker='o', markersize=4, 
                label=self.y_axis_label, linewidth=1.5)
        
        # First Y-axis labels
        ax1.set_xlabel(self.x_axis_label, fontsize=18)
        ax1.set_ylabel(self.y_axis_label, color=self.trend_line_color, fontsize=18)
        ax1.tick_params(axis='y', labelcolor=self.trend_line_color)
        ax1.tick_params(axis='y', color=self.trend_line_color)
        
        # Second Y-axis for cumulative
        ax2 = ax1.twinx()
        ax2.plot(df[self.first_column_name], df[self.y_axis_label_2], 
                color=self.cumulative_line_color, marker='o', markersize=4, 
                label=self.y_axis_label_2, linewidth=1.5)
        
        # Second Y-axis labels
        ax2.set_ylabel(self.y_axis_label_2, color=self.cumulative_line_color, fontsize=18)
        ax2.tick_params(axis='y', labelcolor=self.cumulative_line_color)
        ax2.tick_params(axis='y', color=self.cumulative_line_color)
        
        # Grid
        ax1.grid(True, axis='x', color='lightgrey', linestyle='-', linewidth=0.35)
        
        # Legends
        def wrap_labels(labels, text_wrap_width=20):
            return ["\n".join(textwrap.wrap(label, width=text_wrap_width)) for label in labels]
        
        legend1 = ax1.legend(loc='center left', bbox_to_anchor=(1.1, 0.9), fontsize=12, frameon=False)
        legend2 = ax2.legend(loc='center left', bbox_to_anchor=(1.1, 0.8), fontsize=12, frameon=False)
        
        wrapped_labels1 = wrap_labels([text.get_text() for text in legend1.get_texts()])
        wrapped_labels2 = wrap_labels([text.get_text() for text in legend2.get_texts()])
        
        for text, wrapped_label in zip(legend1.get_texts(), wrapped_labels1):
            text.set_text(wrapped_label)
        for text, wrapped_label in zip(legend2.get_texts(), wrapped_labels2):
            text.set_text(wrapped_label)
        
        # Remove spines
        for ax in [ax1, ax2]:
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_visible(False)
            ax.spines['top'].set_visible(False)
        
        # X-axis ticks
        ax1.set_xticks(df[self.first_column_name].tolist())
        ax1.tick_params(axis='x', rotation=45)
        
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
            'type': 'dual_axis_line',
            'x_axis': self.x_axis_label,
            'y_axis_1': self.y_axis_label,
            'y_axis_2': self.y_axis_label_2,
            'series': [
                {
                    'year': int(row[self.first_column_name]),
                    'annual_publications': int(row[self.second_column_name]),
                    'cumulative_publications': int(row[self.y_axis_label_2])
                }
                for _, row in df.iterrows()
            ],
            'total_cumulative': int(df[self.y_axis_label_2].max()),
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

