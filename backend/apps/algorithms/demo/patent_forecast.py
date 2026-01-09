"""
Patent Forecast algorithm.
Generates line chart with historical data, CAGR projection, and ETS/ARIMA forecasts.
"""
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import datetime
import textwrap
import numpy as np
from pathlib import Path
import json
import io
from typing import Dict, Any, Optional
from django.conf import settings

from apps.algorithms.base import BaseAlgorithm, ChartResult
from apps.datasets.models import Dataset

# Optional imports for forecasting
try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

try:
    from pmdarima import auto_arima
    HAS_PMDARIMA = True
except ImportError:
    HAS_PMDARIMA = False


class PatentForecastAlgorithm(BaseAlgorithm):
    """
    Algorithm for generating forecast chart with ETS and ARIMA models.
    Reads data from Dataset.storage_path (JSON format).
    """
    
    def __init__(self):
        """Initialize algorithm."""
        super().__init__(
            algorithm_key="patent_forecast",
            algorithm_version="1.0"
        )
        
        self.first_column_name = "Year"
        self.second_column_name = "Number of Publications"
        self.historical_years = 20
        self.cutoff_year = datetime.datetime.now().year - 2
        self.trend_line_color = '#44b9be'
        self.cagr_line_color = '#46ad65'
        self.forecast_ets_color = '#eebe5a'
        self.forecast_arima_color = '#ef823a'
        self.chart_width = 15
        self.chart_height = 8
        self.x_axis_label = 'Año'
        self.y_axis_label = 'Número de Familias de Patentes Publicadas'
        self.axis_label_fontsize = 14
        self.tick_fontsize = 10
        self.legend_fontsize = 10
        self.annotation_fontsize = 9
    
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
    
    def run(self, dataset: Dataset, params: Dict[str, Any]) -> ChartResult:
        """Execute algorithm on dataset."""
        import time
        start_time = time.time()
        warnings = []
        
        # Load data
        df = self._load_dataset(dataset)
        
        # Validate dataset has columns
        if df.empty:
            available_columns = list(df.columns) if hasattr(df, 'columns') else []
            raise ValueError(
                f"El dataset está vacío. No se puede generar el gráfico de pronóstico. "
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
        
        # Fit ETS model
        best_model_fit_ets = None
        if HAS_STATSMODELS:
            try:
                best_bic = np.inf
                for trend in ['add', 'mul']:
                    try:
                        model_ets = ExponentialSmoothing(df[self.second_column_name], trend=trend, seasonal=None)
                        model_fit_ets = model_ets.fit()
                        if model_fit_ets.bic < best_bic:
                            best_bic = model_fit_ets.bic
                            best_model_fit_ets = model_fit_ets
                    except Exception:
                        pass
            except Exception as e:
                warnings.append(f"ETS model fitting failed: {str(e)}")
        else:
            warnings.append("statsmodels not available, ETS forecast skipped")
        
        # Fit ARIMA model
        model_fit_arima = None
        if HAS_PMDARIMA:
            try:
                model_arima = auto_arima(df[self.second_column_name], seasonal=False)
                model_fit_arima = model_arima.fit(df[self.second_column_name])
            except Exception as e:
                warnings.append(f"ARIMA model fitting failed: {str(e)}")
        else:
            warnings.append("pmdarima not available, ARIMA forecast skipped")
        
        # Generate forecasts
        forecast_years = list(range(self.cutoff_year + 2, self.cutoff_year + 8))
        forecast_ets = None
        forecast_arima = None
        
        if best_model_fit_ets:
            try:
                forecast_ets = best_model_fit_ets.predict(start=len(df), end=len(df) + 5)
            except Exception:
                pass
        
        if model_fit_arima:
            try:
                forecast_arima = model_fit_arima.predict(n_periods=6)
            except Exception:
                pass
        
        # Create historical DataFrame
        df_historic = df[[self.first_column_name, self.second_column_name]].copy()
        
        # Create forecast DataFrames
        df_forecast_ets = pd.DataFrame({self.first_column_name: forecast_years, "Forecast_ETS": forecast_ets}) if forecast_ets is not None else None
        df_forecast_arima = pd.DataFrame({self.first_column_name: forecast_years, "Forecast_ARIMA": forecast_arima}) if forecast_arima is not None else None
        
        # Calculate CAGR
        start_year = self.cutoff_year - 10
        end_year = self.cutoff_year
        extended_start_year = self.cutoff_year - self.historical_years + 1
        extended_end_year = self.cutoff_year + 5
        extended_years = np.arange(extended_start_year, extended_end_year + 1)
        
        cagr_rate = None
        projected_cagr_line = None
        if start_year in df[self.first_column_name].values and end_year in df[self.first_column_name].values:
            try:
                start_value_cagr = df.loc[df[self.first_column_name] == start_year, self.second_column_name].iloc[0]
                end_value_cagr = df.loc[df[self.first_column_name] == end_year, self.second_column_name].iloc[0]
                if start_value_cagr > 0:
                    cagr_rate = ((end_value_cagr / start_value_cagr) ** (1 / (end_year - start_year))) - 1
                    projected_cagr_line = start_value_cagr * ((1 + cagr_rate) ** (extended_years - start_year))
            except Exception as e:
                warnings.append(f"CAGR calculation failed: {str(e)}")
        
        # Create extended CAGR DataFrame
        df_extended_cagr = None
        if projected_cagr_line is not None:
            df_extended_cagr = pd.DataFrame({
                self.first_column_name: extended_years,
                "CAGR_Projected_Line": projected_cagr_line
            })
        
        # Create chart
        plt.rcParams['svg.fonttype'] = 'none'
        plt.rcParams['font.sans-serif'] = ['Arial']
        
        fig, ax = plt.subplots(figsize=(self.chart_width, self.chart_height))
        
        # Plot historical data
        ax.plot(df[self.first_column_name], df[self.second_column_name], 
                color=self.trend_line_color, marker='o', markersize=4, 
                label="Número de Familias de Patentes Publicadas", linewidth=1.5)
        
        # Plot CAGR line
        if df_extended_cagr is not None:
            ax.plot(df_extended_cagr[self.first_column_name], df_extended_cagr["CAGR_Projected_Line"], 
                    color=self.cagr_line_color, linestyle='dotted', 
                    label="Línea Proyectada CAGR", linewidth=2.5)
        
        # Plot ETS forecast
        if df_forecast_ets is not None and not df_forecast_ets["Forecast_ETS"].isna().all():
            ax.plot(df_forecast_ets[self.first_column_name], df_forecast_ets["Forecast_ETS"], 
                    color=self.forecast_ets_color, linestyle='dotted', 
                    label="Forecast ETS", linewidth=2.5)
        
        # Plot ARIMA forecast
        if df_forecast_arima is not None and not df_forecast_arima["Forecast_ARIMA"].isna().all():
            ax.plot(df_forecast_arima[self.first_column_name], df_forecast_arima["Forecast_ARIMA"], 
                    color=self.forecast_arima_color, linestyle='dotted', 
                    label="Forecast ARIMA", linewidth=2.5)
        
        # Shade forecast area
        start_forecast_year = self.cutoff_year
        end_forecast_year = max(forecast_years) if forecast_years else self.cutoff_year + 5
        ax.axvspan(start_forecast_year, end_forecast_year, color='gray', alpha=0.1)
        
        # Labels
        ax.set_xlabel(self.x_axis_label, fontsize=self.axis_label_fontsize)
        ax.set_ylabel(self.y_axis_label, fontsize=self.axis_label_fontsize)
        ax.tick_params(axis='both', labelsize=self.tick_fontsize)
        
        # Grid
        ax.grid(True, color='lightgrey', linestyle='-', linewidth=0.35)
        
        # Legend
        def wrap_labels(labels, text_wrap_width=30):
            return ["\n".join(textwrap.wrap(label, width=text_wrap_width)) for label in labels]
        
        legend = ax.legend(loc='center left', bbox_to_anchor=(1, 0.9), fontsize=self.legend_fontsize, frameon=False)
        wrapped_labels1 = wrap_labels([text.get_text() for text in legend.get_texts()])
        for text, wrapped_label in zip(legend.get_texts(), wrapped_labels1):
            text.set_text(wrapped_label)
        
        # X-axis - include both historical and forecast years
        all_years = sorted(set(df[self.first_column_name].tolist() + forecast_years))
        ax.set_xticks(all_years)
        ax.tick_params(axis='x', rotation=45)
        
        # Remove spines
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        
        # Annotations - positioned to avoid overflow
        plt.figtext(0.02, -0.08,
                    '*El crecimiento anual compuesto (CAGR) indica la tasa de crecimiento promedio de un valor entre dos puntos en el tiempo.',
                    ha="left", fontsize=self.annotation_fontsize, color="black", wrap=True)
        
        plt.figtext(0.02, -0.12,
                    '** El modelo ARIMA proyecta series temporales considerando patrones históricos de autocorrelación y tendencias.',
                    ha="left", fontsize=self.annotation_fontsize, color="black", wrap=True)
        
        plt.figtext(0.02, -0.16,
                    '*** El modelo ETS utiliza descomposición exponencial para prever tendencias y nivel de una serie temporal.',
                    ha="left", fontsize=self.annotation_fontsize, color="black", wrap=True)
        
        if cagr_rate is not None:
            plt.figtext(0.02, -0.20,
                        f'**** CAGR de {round(cagr_rate * 100, 2)}% para el periodo {start_year}-{end_year}.',
                        ha="left", fontsize=self.annotation_fontsize, color="black", wrap=True)
        
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
            'type': 'forecast_line',
            'x_axis': self.x_axis_label,
            'y_axis': self.y_axis_label,
            'historical_series': [
                {
                    'year': int(row[self.first_column_name]),
                    'publications': int(row[self.second_column_name])
                }
                for _, row in df_historic.iterrows()
            ],
            'forecast_ets': [
                {
                    'year': int(row[self.first_column_name]),
                    'forecast': float(row["Forecast_ETS"])
                }
                for _, row in df_forecast_ets.iterrows()
            ] if df_forecast_ets is not None and not df_forecast_ets["Forecast_ETS"].isna().all() else [],
            'forecast_arima': [
                {
                    'year': int(row[self.first_column_name]),
                    'forecast': float(row["Forecast_ARIMA"])
                }
                for _, row in df_forecast_arima.iterrows()
            ] if df_forecast_arima is not None and not df_forecast_arima["Forecast_ARIMA"].isna().all() else [],
            'cagr_rate': round(cagr_rate * 100, 2) if cagr_rate is not None else None,
            'cagr_period': {'start': start_year, 'end': end_year} if cagr_rate is not None else None,
            'years_range': {
                'start': int(df[self.first_column_name].min()),
                'end': int(df[self.first_column_name].max())
            },
            'forecast_years': forecast_years,
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
                'years_analyzed': len(df),
                'cutoff_year': self.cutoff_year,
                'has_ets_forecast': best_model_fit_ets is not None,
                'has_arima_forecast': model_fit_arima is not None,
                'has_cagr': cagr_rate is not None
            }
        )

