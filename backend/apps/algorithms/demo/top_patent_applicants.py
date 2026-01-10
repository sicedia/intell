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
from typing import Dict, Any, Optional
from django.conf import settings

from apps.algorithms.base import BaseAlgorithm, ChartResult
from apps.algorithms.visualization import VisualizationConfig
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
        self.chart_width = 12
        self.chart_height = 10
        self.x_axis_label = 'Número de Patentes Publicadas'
        self.y_axis_label = 'Solicitantes'
        self.text_wrap_width = 30
        self.axis_label_fontsize = 14
        self.tick_fontsize = 9
        self.bar_label_fontsize = 9
        self.annotation_fontsize = 9
        self.max_label_length = 40
    
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
    
    def _detect_name_column(self, df: pd.DataFrame) -> str:
        """Detect which column contains applicant names."""
        name_keywords = ['applicant', 'solicitante', 'name', 'nombre', 'company', 'empresa', 'organization']
        
        for col in df.columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in name_keywords):
                return col
        
        # Fallback to first column if it contains strings
        if len(df.columns) > 0 and df[df.columns[0]].dtype == 'object':
            return df.columns[0]
        
        return df.columns[0] if len(df.columns) > 0 else None
    
    def _detect_count_column(self, df: pd.DataFrame, name_col: str) -> str:
        """Detect which column contains count/number data."""
        count_keywords = ['number', 'count', 'documents', 'cantidad', 'total', 'publications', 'patentes']
        
        for col in df.columns:
            if col == name_col:
                continue
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in count_keywords):
                return col
        
        # Fallback: return first numeric column that is not the name column
        for col in df.columns:
            if col != name_col and df[col].dtype in ['int64', 'float64']:
                return col
        
        # Last fallback
        for col in df.columns:
            if col != name_col:
                return col
        
        return None
    
    def run(
        self, 
        dataset: Dataset, 
        params: Dict[str, Any],
        viz_config: Optional[VisualizationConfig] = None
    ) -> ChartResult:
        """Execute algorithm on dataset."""
        import time
        start_time = time.time()
        
        # Get visualization config
        viz = self._get_viz_config(viz_config)

        top_n = params.get('top_n', 15)
        if not isinstance(top_n, int) or top_n < 1:
            raise ValueError(
                f"El parámetro 'top_n' debe ser un número entero positivo. "
                f"Valor recibido: {top_n}"
            )
        
        # Load data
        df = self._load_dataset(dataset)
        
        # Validate dataset
        if df.empty:
            raise ValueError(
                "El dataset está vacío. No se puede generar el gráfico de solicitantes. "
                "Por favor, verifique que el archivo Excel contenga datos en la hoja de 'Applicants'."
            )
        
        if len(df.columns) < 2:
            available_columns = list(df.columns)
            raise ValueError(
                f"El dataset debe tener al menos 2 columnas. "
                f"Se encontraron {len(df.columns)} columna(s): {available_columns}. "
                f"Se esperaba: una columna con nombres de solicitantes y otra con el número de documentos."
            )
        
        # Detect columns
        name_col = self._detect_name_column(df)
        count_col = self._detect_count_column(df, name_col)
        
        if name_col is None:
            available_columns = list(df.columns)
            raise ValueError(
                f"No se pudo detectar la columna de nombres de solicitantes. "
                f"Columnas disponibles: {available_columns}. "
                f"Asegúrese de que el archivo Excel tenga una columna con nombres (ej: 'Applicants', 'Solicitantes')."
            )
        
        if count_col is None:
            available_columns = list(df.columns)
            raise ValueError(
                f"No se pudo detectar la columna de conteo de documentos. "
                f"Columnas disponibles: {available_columns}. "
                f"Asegúrese de que el archivo Excel tenga una columna con números (ej: 'Number of documents')."
            )
        
        # Rename columns for processing
        df = df.rename(columns={name_col: self.first_column_name, count_col: self.second_column_name})
        
        # Ensure count column is numeric
        df[self.second_column_name] = pd.to_numeric(df[self.second_column_name], errors='coerce')
        
        # Check for valid numeric data
        if df[self.second_column_name].isna().all():
            raise ValueError(
                f"La columna de conteo '{count_col}' no contiene valores numéricos válidos. "
                f"Por favor, verifique que los datos sean números."
            )
        
        df[self.second_column_name] = df[self.second_column_name].fillna(0)
        
        # Check if we have enough data
        if len(df) < top_n:
            raise ValueError(
                f"No hay suficientes solicitantes en el dataset. "
                f"Se solicitaron los top {top_n}, pero solo hay {len(df)} solicitantes disponibles."
            )
        
        # Select top n applicants
        top_n_applicants = df.nlargest(top_n, self.second_column_name)
        top_n_applicants = top_n_applicants.sort_values(by=self.second_column_name, ascending=True)
        
        # Get colors from visualization config
        palette_colors = viz.get_colors()
        primary_color = viz.get_primary_color()
        secondary_color = viz.get_secondary_color()
        text_color = viz.get_text_color()
        grid_color = viz.get_grid_color()
        bg_color = viz.get_background_color()
        axis_fontsize = viz.get_axis_label_fontsize()
        tick_fontsize = viz.get_tick_fontsize()
        bar_label_fontsize = viz.get_annotation_fontsize()
        annotation_fontsize = viz.get_annotation_fontsize()
        
        # Generate colormap using viz config colors
        cmap = mcolors.LinearSegmentedColormap.from_list(
            "mycmap", 
            [palette_colors[0] if len(palette_colors) > 0 else primary_color, 
             palette_colors[-1] if len(palette_colors) > 1 else secondary_color]
        )
        
        # Normalize values
        min_val = top_n_applicants[self.second_column_name].min()
        max_val = top_n_applicants[self.second_column_name].max()
        normalized_vals = [
            (x - min_val) / (max_val - min_val) if max_val > min_val else 0.5
            for x in top_n_applicants[self.second_column_name]
        ]
        
        colors = [cmap(val) for val in normalized_vals]
        
        # Wrap and truncate labels
        def process_labels(labels, text_wrap_width, max_length):
            processed = []
            for label in labels:
                # Truncate if too long
                if len(label) > max_length:
                    label = label[:max_length-3] + "..."
                # Wrap text
                wrapped = "\n".join(textwrap.wrap(label, width=text_wrap_width))
                processed.append(wrapped)
            return processed
        
        top_n_applicants[self.first_column_name] = process_labels(
            top_n_applicants[self.first_column_name].tolist(), 
            self.text_wrap_width, 
            self.max_label_length
        )
        top_n_applicants[self.first_column_name] = top_n_applicants[self.first_column_name].apply(lambda x: x.strip().title())
        
        # Create chart with visualization config
        plt.rcParams['svg.fonttype'] = 'none'
        plt.rcParams['font.sans-serif'] = ['Arial']
        
        fig, ax = plt.subplots(figsize=[self.chart_width, self.chart_height])
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
        
        bars = ax.barh(top_n_applicants[self.first_column_name], top_n_applicants[self.second_column_name], color=colors)
        
        # Format X-axis
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: '{:,.0f}'.format(x)))
        
        # Calculate total
        total_publications = df[self.second_column_name].sum()
        
        # Add labels with viz config
        label_offset = 0.025 * max_val
        for i, bar in enumerate(bars):
            num_publications = top_n_applicants[self.second_column_name].iloc[i]
            percentage = (num_publications / total_publications) * 100
            ax.text(
                bar.get_width() + label_offset,
                bar.get_y() + bar.get_height() / 2,
                f'{num_publications:,.0f} ({percentage:.1f}%)',
                ha='left', va='center',
                fontsize=bar_label_fontsize,
                color=text_color
            )
        
        # Adjust x-axis limit to fit labels
        ax.set_xlim(0, max_val * 1.25)
        ax.tick_params(axis='y', labelsize=tick_fontsize, labelcolor=text_color)
        ax.tick_params(axis='x', labelsize=tick_fontsize, labelcolor=text_color)
        
        # Remove spines and style
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.spines['left'].set_color(grid_color)
        ax.spines['bottom'].set_color(grid_color)
        ax.xaxis.set_ticks_position('none')
        ax.yaxis.set_ticks_position('none')
        
        # Labels with viz config
        ax.set_xlabel(self.x_axis_label, fontsize=axis_fontsize, labelpad=12, color=text_color)
        ax.set_ylabel(self.y_axis_label, fontsize=axis_fontsize, labelpad=12, color=text_color)
        
        # Annotations with viz config
        plt.figtext(0.02, -0.06,
                    '* Los solicitantes tienen el derecho legal de reclamar la protección de una invención.',
                    ha="left", fontsize=annotation_fontsize, color=text_color, wrap=True)
        
        plt.figtext(0.02, -0.10,
                    '** Un solicitante puede ser persona física o jurídica que busca proteger una invención.',
                    ha="left", fontsize=annotation_fontsize, color=text_color, wrap=True)
        
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

