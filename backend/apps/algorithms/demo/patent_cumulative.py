"""
Patent Cumulative algorithm.
Generates line chart showing cumulative evolution of patent publications.
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
from typing import Dict, Any, Optional
from django.conf import settings

from apps.algorithms.base import BaseAlgorithm, ChartResult
from apps.algorithms.visualization import VisualizationConfig
from apps.datasets.models import Dataset


class PatentCumulativeAlgorithm(BaseAlgorithm):
    """
    Algorithm for generating line chart of cumulative patent publications.
    Reads data from Dataset.storage_path (JSON format).
    """
    
    def __init__(self):
        """Initialize algorithm."""
        super().__init__(
            algorithm_key="patent_cumulative",
            algorithm_version="1.0"
        )
        
        self.first_column_name = "Year"
        self.second_column_name = "Number of Publications"
        self.historical_years = 20
        self.cutoff_year = datetime.datetime.now().year - 2
        self.cumulative_line_color = '#001f3f'
        self.chart_width = 12
        self.chart_height = 8
        self.x_axis_label = 'Año'
        self.y_axis_label = 'Publicaciones de Patentes Acumulativas'
        self.axis_label_fontsize = 14
        self.tick_fontsize = 10
        self.legend_fontsize = 10
        self.annotation_fontsize = 10
    
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
    
    def _detect_year_column(self, df: pd.DataFrame) -> str:
        """Detect which column contains year data."""
        # Try to find a column that looks like years
        year_keywords = ['year', 'año', 'date', 'fecha', 'publication', 'publicación', 'earliest', 'priority']
        
        for col in df.columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in year_keywords):
                # Try to convert to numeric to verify it's years
                test_series = pd.to_numeric(df[col], errors='coerce')
                if not test_series.isna().all():
                    # Check if values are in reasonable year range (1900-2100)
                    valid_years = test_series.dropna()
                    if len(valid_years) > 0:
                        min_val = valid_years.min()
                        max_val = valid_years.max()
                        if 1900 <= min_val <= 2100 and 1900 <= max_val <= 2100:
                            return col
        
        # Fallback: check all columns for year-like values
        for col in df.columns:
            test_series = pd.to_numeric(df[col], errors='coerce')
            if not test_series.isna().all():
                valid_years = test_series.dropna()
                if len(valid_years) > 0:
                    min_val = valid_years.min()
                    max_val = valid_years.max()
                    if 1900 <= min_val <= 2100 and 1900 <= max_val <= 2100:
                        return col
        
        # Fallback to first column
        return df.columns[0] if len(df.columns) > 0 else None
    
    def _detect_count_column(self, df: pd.DataFrame, year_col: str) -> str:
        """Detect which column contains count/number data."""
        count_keywords = ['number', 'count', 'documents', 'cantidad', 'total', 'publications']
        
        for col in df.columns:
            if col == year_col:
                continue
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in count_keywords):
                return col
        
        # Fallback: return first column that is not the year column
        for col in df.columns:
            if col != year_col:
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

        # Load data
        df = self._load_dataset(dataset)
        
        # Validate dataset has columns
        if df.empty:
            available_columns = list(df.columns) if hasattr(df, 'columns') else []
            raise ValueError(
                f"El dataset está vacío. No se puede generar el gráfico acumulativo. "
                f"Columnas disponibles: {available_columns}. "
                f"Verifique que el archivo Excel contenga datos en la hoja 'Earliest publication date'."
            )
        
        if len(df.columns) < 2:
            available_columns = list(df.columns)
            raise ValueError(
                f"El dataset debe tener al menos 2 columnas. "
                f"Se encontraron {len(df.columns)} columna(s): {available_columns}. "
                f"Se esperaba: una columna con años y otra con el número de publicaciones."
            )
        
        # Detect year column
        year_col = self._detect_year_column(df)
        if year_col is None:
            available_columns = list(df.columns)
            raise ValueError(
                f"No se pudo detectar la columna de años en el dataset. "
                f"Columnas disponibles: {available_columns}. "
                f"Asegúrese de que el archivo Excel tenga una columna con años (ej: 'Year', 'Año', 'Earliest publication date')."
            )
        
        # Detect count column
        count_col = self._detect_count_column(df, year_col)
        if count_col is None:
            available_columns = list(df.columns)
            raise ValueError(
                f"No se pudo detectar la columna de conteo de documentos. "
                f"Columnas disponibles: {available_columns}. "
                f"Asegúrese de que el archivo Excel tenga una columna con números (ej: 'Number of documents')."
            )
        
        # Rename columns for processing
        df = df.rename(columns={year_col: self.first_column_name, count_col: self.second_column_name})
        
        # Convert first column to numeric (handles string years)
        df[self.first_column_name] = pd.to_numeric(df[self.first_column_name], errors='coerce')
        
        # Drop rows where conversion failed (NaN values)
        original_count = len(df)
        df = df.dropna(subset=[self.first_column_name])
        dropped_count = original_count - len(df)
        
        # Check if we have valid data after conversion
        if df.empty:
            raise ValueError(
                f"No se encontraron datos de años válidos después de la conversión. "
                f"La columna original '{year_col}' no pudo ser convertida a años numéricos. "
                f"Asegúrese de que la columna de años contenga valores numéricos (ej: 2020, 2021, 2022)."
            )
        
        if dropped_count > 0:
            # Log warning but continue
            pass
        
        # Convert to int for year operations
        df[self.first_column_name] = df[self.first_column_name].astype(int)
        
        # Get year range before filtering for better error messages
        min_year_before_filter = int(df[self.first_column_name].min())
        max_year_before_filter = int(df[self.first_column_name].max())
        
        # Filter data
        df = df[(df[self.first_column_name] <= self.cutoff_year) & 
                (df[self.first_column_name] > (self.cutoff_year - self.historical_years))]
        
        # Check if we have data after filtering
        if df.empty:
            raise ValueError(
                f"No se encontraron datos en el rango de años especificado ({self.cutoff_year - self.historical_years} a {self.cutoff_year}). "
                f"Su dataset contiene años desde {min_year_before_filter} hasta {max_year_before_filter}. "
                f"Este algoritmo analiza los últimos {self.historical_years} años hasta {self.cutoff_year} (excluyendo años recientes incompletos). "
                f"Por favor, use un dataset con datos en el rango {self.cutoff_year - self.historical_years} a {self.cutoff_year}."
            )
        
        # Complete years range (ensure min and max are integers and not NaN)
        min_val = df[self.first_column_name].min()
        max_val = df[self.first_column_name].max()
        
        if pd.isna(min_val) or pd.isna(max_val):
            raise ValueError(
                f"Valores de año inválidos después del filtrado: mínimo={min_val}, máximo={max_val}. "
                f"Verifique que los datos del archivo Excel sean correctos."
            )
        
        min_year = int(min_val)
        max_year = int(max_val)
        complete_years = pd.DataFrame({
            self.first_column_name: range(min_year, max_year + 1)
        })
        
        # Merge to ensure all years present
        df = pd.merge(complete_years, df, on=self.first_column_name, how='left')
        
        # Convert count column to numeric (in case JSON has strings)
        df[self.second_column_name] = pd.to_numeric(df[self.second_column_name], errors='coerce')
        df[self.second_column_name] = df[self.second_column_name].fillna(0)
        
        # Sort by year to ensure proper line plotting
        df = df.sort_values(by=self.first_column_name).reset_index(drop=True)
        
        # Calculate cumulative
        df[self.y_axis_label] = df[self.second_column_name].cumsum()
        
        # Get colors and font sizes from visualization config
        primary_color = viz.get_primary_color()
        text_color = viz.get_text_color()
        grid_color = viz.get_grid_color()
        bg_color = viz.get_background_color()
        axis_fontsize = viz.get_axis_label_fontsize()
        tick_fontsize = viz.get_tick_fontsize()
        legend_fontsize = viz.get_legend_fontsize()
        annotation_fontsize = viz.get_annotation_fontsize()
        
        # Create chart with visualization config
        plt.rcParams['svg.fonttype'] = 'none'
        plt.rcParams['font.sans-serif'] = ['Arial']
        
        fig, ax = plt.subplots(figsize=(self.chart_width, self.chart_height))
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
        
        ax.plot(df[self.first_column_name], df[self.y_axis_label], 
                color=primary_color, marker='o', markersize=4, 
                label=self.y_axis_label, linewidth=1.5)
        
        # Labels with viz config
        ax.set_xlabel(self.x_axis_label, fontsize=axis_fontsize, color=text_color)
        ax.set_ylabel(self.y_axis_label, fontsize=axis_fontsize, color=text_color)
        ax.tick_params(axis='y', labelcolor=text_color, labelsize=tick_fontsize)
        ax.tick_params(axis='x', labelcolor=text_color, labelsize=tick_fontsize)
        
        # Grid with viz config
        ax.grid(True, color=grid_color, linestyle='-', linewidth=0.35)
        
        # Legend
        def wrap_labels(labels, text_wrap_width=20):
            return ["\n".join(textwrap.wrap(label, width=text_wrap_width)) for label in labels]
        
        legend = ax.legend(loc='center left', bbox_to_anchor=(1, 0.9), fontsize=legend_fontsize, frameon=False)
        wrapped_labels = wrap_labels([text.get_text() for text in legend.get_texts()])
        for text, wrapped_label in zip(legend.get_texts(), wrapped_labels):
            text.set_text(wrapped_label)
            text.set_color(text_color)
        
        # Remove spines and style
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.spines['left'].set_color(grid_color)
        ax.spines['bottom'].set_color(grid_color)
        
        # X-axis ticks
        ax.set_xticks(df[self.first_column_name].tolist())
        ax.tick_params(axis='x', rotation=45)
        
        # Annotations with viz config
        plt.figtext(0, -0.075,
                    '* Se muestran las publicaciones hasta hace 2 años, porque los documentos de patente suelen demorar hasta 18 meses en su publicación.',
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
            'type': 'line',
            'x_axis': self.x_axis_label,
            'y_axis': self.y_axis_label,
            'series': [
                {
                    'year': int(row[self.first_column_name]),
                    'annual_publications': int(row[self.second_column_name]),
                    'cumulative_publications': int(row[self.y_axis_label])
                }
                for _, row in df.iterrows()
            ],
            'total_cumulative': int(df[self.y_axis_label].max()),
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

