"""
Top Patent Countries algorithm.
Generates horizontal bar chart showing top n jurisdictions by patent publications.
Adapted to consume datasets.Dataset instead of file paths.
"""
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.colors as mcolors
from matplotlib.ticker import MaxNLocator, FuncFormatter
from pathlib import Path
import json
import io
from typing import Dict, Any
from django.conf import settings

from apps.algorithms.base import BaseAlgorithm, ChartResult
from apps.datasets.models import Dataset


class TopPatentCountriesAlgorithm(BaseAlgorithm):
    """
    Algorithm for generating horizontal bar chart of top patent countries.
    Reads data from Dataset.storage_path (JSON format).
    """
    
    def __init__(self):
        """Initialize algorithm."""
        super().__init__(
            algorithm_key="top_patent_countries",
            algorithm_version="1.0"
        )
        
        # Configuration
        self.first_column_name = "Country"
        self.second_column_name = "Number of Publications"
        self.gradient_color_min = '#4fc0e5'
        self.gradient_color_max = '#1e3d8f'
        self.ecuador_bar_color = '#eebe5a'
        self.others_bar_color = '#46ad65'
        self.chart_width = 10
        self.chart_height = 8
        self.x_axis_label = 'Number of Patents Published'
        self.y_axis_label = 'Jurisdiction'
    
    def _load_dataset(self, dataset: Dataset) -> pd.DataFrame:
        """
        Load data from Dataset.
        
        Args:
            dataset: Dataset instance
            
        Returns:
            DataFrame with data
        """
        # Get file path
        if dataset.storage_path.startswith('/') or ':' in dataset.storage_path:
            # Absolute path
            file_path = Path(dataset.storage_path)
        else:
            # Relative to MEDIA_ROOT
            file_path = Path(settings.MEDIA_ROOT) / dataset.storage_path
        
        if not file_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {file_path}")
        
        # Load based on format
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
        """
        Execute algorithm on dataset.
        
        Args:
            dataset: Dataset instance
            params: Must contain 'top_n' (int)
            
        Returns:
            ChartResult with PNG bytes, SVG text, and chart_data
        """
        import time
        start_time = time.time()
        
        # Validate params
        top_n = params.get('top_n', 15)
        if not isinstance(top_n, int) or top_n < 1:
            raise ValueError("top_n must be a positive integer")
        
        # Load data from Dataset
        df = self._load_dataset(dataset)
        
        # Rename columns if needed
        if len(df.columns) >= 2:
            if df.columns[0] != self.first_column_name or df.columns[1] != self.second_column_name:
                df.rename(columns={df.columns[0]: self.first_column_name, 
                                 df.columns[1]: self.second_column_name}, inplace=True)
        
        # Check if Ecuador is present
        ecuador_rank, ecuador_publications = None, None
        if 'EC' in df[self.first_column_name].values:
            ecuador_info = df[df[self.first_column_name] == 'EC']
            ecuador_rank = ecuador_info.index[0] + 1
            ecuador_publications = ecuador_info[self.second_column_name].values[0]
        
        # Select top n countries
        top_n_countries = df.nlargest(top_n, self.second_column_name)
        
        # Filter others (not in top n and not Ecuador)
        other_countries = df[
            ~df[self.first_column_name].isin(top_n_countries[self.first_column_name]) & 
            (df[self.first_column_name] != 'EC')
        ]
        other_sum = other_countries[self.second_column_name].sum()
        
        # Create Others DataFrame
        others_df = pd.DataFrame([{
            self.first_column_name: 'Others', 
            self.second_column_name: other_sum
        }])
        
        # Combine data
        if ecuador_rank is not None:
            top_n_and_ecuador = pd.concat([top_n_countries, ecuador_info, others_df])
        else:
            top_n_and_ecuador = pd.concat([top_n_countries, others_df])
        
        # Sort by publications (ascending for horizontal bar)
        top_n_and_ecuador.sort_values(self.second_column_name, ascending=True, inplace=True)
        
        # Move Others to bottom
        if 'Others' in top_n_and_ecuador[self.first_column_name].values:
            top_n_and_ecuador = top_n_and_ecuador[top_n_and_ecuador[self.first_column_name] != 'Others']
            others_row = pd.DataFrame([{
                self.first_column_name: 'Others', 
                self.second_column_name: other_sum
            }])
            top_n_and_ecuador = pd.concat([others_row, top_n_and_ecuador], ignore_index=True)
        
        # Generate colormap
        cmap = mcolors.LinearSegmentedColormap.from_list(
            "mycmap", 
            [self.gradient_color_min, self.gradient_color_max]
        )
        
        # Normalize values for gradient
        min_val = top_n_and_ecuador[self.second_column_name].min()
        max_val = top_n_and_ecuador[self.second_column_name].max()
        normalized_vals = [
            (x - min_val) / (max_val - min_val) if max_val > min_val else 0.5
            for x in top_n_and_ecuador[self.second_column_name]
        ]
        
        # Assign colors
        bar_colors = []
        for norm_val, country in zip(normalized_vals, top_n_and_ecuador[self.first_column_name]):
            if country == 'EC':
                bar_colors.append(self.ecuador_bar_color)
            elif country == 'Others':
                bar_colors.append(self.others_bar_color)
            else:
                bar_colors.append(cmap(norm_val))
        
        # Create chart
        plt.rcParams['svg.fonttype'] = 'none'
        plt.rcParams['font.sans-serif'] = ['Arial']
        
        fig, ax = plt.subplots(figsize=[self.chart_width, self.chart_height])
        bars = ax.barh(
            top_n_and_ecuador[self.first_column_name], 
            top_n_and_ecuador[self.second_column_name], 
            color=bar_colors
        )
        
        # Format X-axis
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: '{:,.0f}'.format(x)))
        
        # Calculate total
        total_publications = top_n_and_ecuador[self.second_column_name].sum()
        
        # Add labels
        label_offset = np.round(0.025 * max_val)
        for i, bar in enumerate(bars):
            num_publications = top_n_and_ecuador[self.second_column_name].iloc[i]
            percentage = (num_publications / total_publications) * 100
            ax.text(
                bar.get_width() + label_offset,
                bar.get_y() + bar.get_height() / 2,
                f'{num_publications:,.0f} ({percentage:.2f}%)',
                ha='left', va='center'
            )
        
        # Remove top and right spines
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.xaxis.set_ticks_position('none')
        ax.yaxis.set_ticks_position('none')
        
        # Add axis labels
        ax.set_xlabel(self.x_axis_label, fontsize=18, labelpad=12, color="black")
        ax.set_ylabel(self.y_axis_label, fontsize=18, labelpad=12, color="black")
        
        # Generate PNG bytes
        png_buffer = io.BytesIO()
        plt.savefig(png_buffer, format='png', bbox_inches='tight', dpi=100)
        png_bytes = png_buffer.getvalue()
        png_buffer.close()
        
        # Generate SVG text
        svg_buffer = io.StringIO()
        plt.savefig(svg_buffer, format='svg', bbox_inches='tight')
        svg_text = svg_buffer.getvalue()
        svg_buffer.close()
        
        plt.close(fig)
        
        # Build chart_data for AI
        chart_data = {
            "type": "horizontal_bar",
            "title": f"Top {top_n} Patent Countries",
            "x_axis": {
                "label": self.x_axis_label,
                "values": top_n_and_ecuador[self.second_column_name].tolist()
            },
            "y_axis": {
                "label": self.y_axis_label,
                "categories": top_n_and_ecuador[self.first_column_name].tolist()
            },
            "series": [
                {
                    "name": self.second_column_name,
                    "data": top_n_and_ecuador[self.second_column_name].tolist(),
                    "labels": top_n_and_ecuador[self.first_column_name].tolist()
                }
            ],
            "totals": {
                "total_publications": int(total_publications),
                "top_n": top_n,
                "ecuador_rank": ecuador_rank,
                "ecuador_publications": int(ecuador_publications) if ecuador_publications else None
            },
            "warnings": []
        }
        
        # Add warnings
        if 'WO' in df[self.first_column_name].values:
            chart_data["warnings"].append(
                "WO indicates international patent publication under PCT, administered by WIPO"
            )
        if 'EP' in df[self.first_column_name].values:
            chart_data["warnings"].append(
                "EP indicates European Patent Office publication, covering protection in member states"
            )
        
        # Build metadata
        execution_time = time.time() - start_time
        meta = {
            "algorithm_key": self.algorithm_key,
            "algorithm_version": self.algorithm_version,
            "execution_time_seconds": round(execution_time, 3),
            "dataset_id": dataset.id,
            "top_n_applied": top_n,
            "total_countries": len(top_n_and_ecuador)
        }
        
        return ChartResult(
            png_bytes=png_bytes,
            svg_text=svg_text,
            chart_data=chart_data,
            meta=meta
        )

