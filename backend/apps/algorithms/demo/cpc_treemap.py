"""
CPC Treemap algorithm.
Generates treemap visualization of top CPC subgroups by patent publications.
"""
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import math
from pathlib import Path
import json
import io
from typing import Dict, Any
from django.conf import settings

from apps.algorithms.base import BaseAlgorithm, ChartResult
from apps.datasets.models import Dataset

# Optional import for treemap
try:
    import squarify
    HAS_SQUARIFY = True
except ImportError:
    HAS_SQUARIFY = False


class CPCTreemapAlgorithm(BaseAlgorithm):
    """
    Algorithm for generating treemap of CPC subgroups.
    Reads data from Dataset.storage_path (JSON format).
    """
    
    def __init__(self):
        """Initialize algorithm."""
        super().__init__(
            algorithm_key="cpc_treemap",
            algorithm_version="1.0"
        )
        
        self.first_column_name = "CPC Subgroups"
        self.second_column_name = "Number of Publications"
        self.chart_width = 12
        self.chart_height = 8
        self.min_font_size = 6
        self.max_font_size = 16
        self.font_scale_factor = 350
        self.simplification_threshold_fontsize = 8
    
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
        warnings = []
        
        num_groups = params.get('num_groups', 15)
        if not isinstance(num_groups, int) or num_groups < 1:
            raise ValueError("num_groups must be a positive integer")
        
        if not HAS_SQUARIFY:
            raise ImportError("squarify package is required for treemap visualization. Install with: pip install squarify")
        
        # Load data
        df = self._load_dataset(dataset)
        
        # Rename columns if needed
        if len(df.columns) >= 2:
            if df.columns[0] != self.first_column_name or df.columns[1] != self.second_column_name:
                df.rename(columns={df.columns[0]: self.first_column_name, 
                                 df.columns[1]: self.second_column_name}, inplace=True)
        
        # Select top n CPCs
        top_n_cpcs = df.nlargest(num_groups, self.second_column_name).copy()
        top_n_cpcs[self.first_column_name] = top_n_cpcs[self.first_column_name].str.title()
        
        # Create figure and axes
        plt.rcParams['svg.fonttype'] = 'none'
        plt.rcParams['font.sans-serif'] = ['Arial']
        
        fig, ax = plt.subplots(figsize=(self.chart_width, self.chart_height))
        
        # Get plotting area dimensions
        x_axis_min, x_axis_max = ax.get_xlim()
        y_axis_min, y_axis_max = ax.get_ylim()
        plot_width = x_axis_max - x_axis_min
        plot_height = y_axis_max - y_axis_min
        
        # Normalize values for squarify
        values = top_n_cpcs[self.second_column_name].tolist()
        values = [max(v, 0) for v in values]
        
        # Calculate layout
        if sum(values) > 0:
            norm_sizes = squarify.normalize_sizes(values, plot_width, plot_height)
            rects_data = squarify.squarify(norm_sizes, x_axis_min, y_axis_min, plot_width, plot_height)
        else:
            rects_data = []
            warnings.append("No positive values to plot")
        
        # Color mapping
        norm_color = plt.Normalize(top_n_cpcs[self.second_column_name].min(), top_n_cpcs[self.second_column_name].max())
        cmap = plt.cm.colors.LinearSegmentedColormap.from_list("custom_blue", ['#44b9be', '#0234a5', '#001f3f'])
        bar_colors = [cmap(norm_color(value)) for value in top_n_cpcs[self.second_column_name]]
        
        # Plot rectangles
        if len(rects_data) == len(top_n_cpcs):
            for i, rect_geom in enumerate(rects_data):
                x, y, dx, dy = rect_geom['x'], rect_geom['y'], rect_geom['dx'], rect_geom['dy']
                area = dx * dy
                
                cpc_label = top_n_cpcs.iloc[i][self.first_column_name]
                num_patents = top_n_cpcs.iloc[i][self.second_column_name]
                color = bar_colors[i]
                
                # Calculate font size
                full_label_text = f"{cpc_label}\n(No. Patentes: {num_patents})"
                simplified_label_text = cpc_label
                
                num_chars_full = len(full_label_text) + 1
                target_size_full = self.min_font_size
                if area > 1e-6 and num_chars_full > 0:
                    target_size_full = math.sqrt(area / num_chars_full) * self.font_scale_factor * ((plot_width * plot_height) / (1.0 * 1.0))
                
                final_font_size_full = max(self.min_font_size, min(self.max_font_size, target_size_full))
                
                # Apply simplification if needed
                display_label_text = full_label_text
                final_font_size = final_font_size_full
                
                if final_font_size_full < self.simplification_threshold_fontsize:
                    display_label_text = simplified_label_text
                    num_chars_simplified = len(display_label_text) + 1
                    target_size_simplified = self.min_font_size
                    if area > 1e-6 and num_chars_simplified > 0:
                        target_size_simplified = math.sqrt(area / num_chars_simplified) * self.font_scale_factor * ((plot_width * plot_height) / (1.0 * 1.0))
                        final_font_size = max(self.min_font_size, min(self.simplification_threshold_fontsize - 0.1, min(self.max_font_size, target_size_simplified)))
                    else:
                        final_font_size = self.min_font_size
                
                # Draw rectangle
                if dx > 1e-6 and dy > 1e-6:
                    rect_patch = plt.Rectangle((x, y), dx, dy,
                                               facecolor=color,
                                               edgecolor='black',
                                               linewidth=1.5,
                                               alpha=0.8)
                    ax.add_patch(rect_patch)
                    
                    # Draw text
                    ax.text(x + dx / 2, y + dy / 2,
                            display_label_text,
                            ha='center', va='center',
                            fontsize=final_font_size,
                            color='white',
                            fontweight='bold',
                            wrap=False)
        
        # Final touches
        ax.axis('off')
        ax.set_xlim(x_axis_min, x_axis_max)
        ax.set_ylim(y_axis_min, y_axis_max)
        
        # Color bar
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm_color)
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, orientation='vertical', shrink=0.8, pad=0.05)
        cbar.set_label('Número de Publicaciones', fontsize=18, color="black")
        
        plt.figtext(0, -0.1,
                    '* Un subgrupo CPC es una clasificación dentro del Sistema de Clasificación Cooperativa de Patentes, utilizado para categorizar invenciones según su tecnología y campo de aplicación.',
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
            'type': 'treemap',
            'series': [
                {
                    'name': row[self.first_column_name],
                    'value': int(row[self.second_column_name]),
                    'percentage': round((row[self.second_column_name] / top_n_cpcs[self.second_column_name].sum()) * 100, 2)
                }
                for _, row in top_n_cpcs.iterrows()
            ],
            'total_publications': int(top_n_cpcs[self.second_column_name].sum()),
            'num_groups': num_groups,
            'warnings': warnings
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
                'num_groups': num_groups,
                'total_cpcs': len(df),
                'displayed_cpcs': len(top_n_cpcs)
            }
        )

