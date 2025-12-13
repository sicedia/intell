import pandas as pd
import matplotlib.pyplot as plt
import datetime
import textwrap
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from pmdarima import auto_arima

def generate_evolution_and_forecast_chart():
    """
    Generates a line chart showing the evolution of the number of patent publications over recent years and forecasts future publications using ETS and ARIMA models.

    The chart includes the historical publication line, the projection based on the Compound Annual Growth Rate (CAGR), and forecasts calculated using Exponential Smoothing (ETS) and ARIMA models.
    The forecast period is also shaded.

    Parameters:
    -----------
    None. All configurations (data path, colors, analysis years, etc.) are defined within the function.

    Returns:
    --------
    None. The function generates and displays the chart directly on the screen, along with explanatory annotations.
    """
    
    # Configuration to preserve text in SVG
    plt.rcParams['svg.fonttype'] = 'none'  # Save text as text
    plt.rcParams['font.sans-serif'] = ['Arial']  
    
    # File path definition and other key settings
    data_path = r"C:\Users\francisco.alvarez\Downloads\test.xlsx"
    sheet_name = "Earliest publication date (fam"
    first_column_name = "Year"
    second_column_name = "Number of Publications"
    historical_years = 20
    cutoff_year = datetime.datetime.now().year - 2
    trend_line_color = '#44b9be'
    cagr_line_color = '#46ad65'
    forecast_ets_color = '#eebe5a'
    forecast_arima_color = '#ef823a'
    chart_width = 15
    chart_height = 8
    x_axis_label = 'Año'
    y_axis_label = 'Número de Familias de Patentes Publicadas'

    # Load data
    df = pd.read_excel(data_path, sheet_name=sheet_name)

    # Rename columns if names do not match expected values
    if df.columns[0] != first_column_name or df.columns[1] != second_column_name:
        df.rename(columns={df.columns[0]: first_column_name, df.columns[1]: second_column_name}, inplace=True)

    # Filter the dataframe to exclude years after the cutoff year
    df = df[(df[first_column_name] <= cutoff_year) & (df[first_column_name] > (cutoff_year - historical_years))]

    # Create a range of years from the minimum to the maximum year in the filtered DataFrame
    complete_years = pd.DataFrame({first_column_name: range(df[first_column_name].min(), df[first_column_name].max() + 1)})

    # Merge with the original DataFrame to ensure all years are present
    df = pd.merge(complete_years, df, on=first_column_name, how='left')

    # Fill missing years with 0 in 'Number of Publications'
    df[second_column_name] = df[second_column_name].fillna(0)

    # Fit the ETS model with additive and multiplicative trends, choosing the model with the lowest BIC
    best_bic = np.inf
    best_model_ets = None
    best_model_fit_ets = None

    for trend in ['add', 'mul']:
        try:
            model_ets = ExponentialSmoothing(df[second_column_name], trend=trend, seasonal=None)
            model_fit_ets = model_ets.fit()
            if model_fit_ets.bic < best_bic:
                best_bic = model_fit_ets.bic
                best_model_ets = model_ets
                best_model_fit_ets = model_fit_ets
        except Exception as e:
            model_fit_ets = None

    # Fit an Auto ARIMA model
    try:
        model_arima = auto_arima(df[second_column_name], seasonal=False)
        model_fit_arima = model_arima.fit(df[second_column_name])
    except Exception as e:
        model_fit_arima = None

    # Generate forecasts for the current year and the next 5 years
    forecast_years = list(range(cutoff_year + 2, cutoff_year + 8))
    forecast_ets = best_model_fit_ets.predict(start=len(df), end=len(df) + 5) if best_model_fit_ets else None
    forecast_arima = model_fit_arima.predict(n_periods=6) if model_fit_arima else None

    # Create a DataFrame with historical data
    df_historic = df[[first_column_name, second_column_name]].copy()

    # Create DataFrames for ETS and ARIMA forecasts
    df_forecast_ets = pd.DataFrame({first_column_name: forecast_years, "Forecast_ETS": forecast_ets})
    df_forecast_arima = pd.DataFrame({first_column_name: forecast_years, "Forecast_ARIMA": forecast_arima})

    # Extend the CAGR line both forward and backward in time
    extended_start_year = cutoff_year - historical_years + 1
    extended_end_year = cutoff_year + 5
    start_year = cutoff_year - 10
    end_year = cutoff_year
    extended_years = np.arange(extended_start_year, extended_end_year + 1)

    # Calculate the projected CAGR line for the extended range
    start_value_cagr = df.loc[df[first_column_name] == start_year, second_column_name].iloc[0]
    end_value_cagr = df.loc[df[first_column_name] == end_year, second_column_name].iloc[0]
    cagr_rate = ((end_value_cagr / start_value_cagr) ** (1 / (end_year - start_year))) - 1
    projected_cagr_line = start_value_cagr * ((1 + cagr_rate) ** (extended_years - start_year))

    # Create a new extended DataFrame for CAGR values
    df_extended_cagr = pd.DataFrame({
        first_column_name: extended_years,
        "CAGR_Projected_Line": projected_cagr_line
    })

    # Combine the projected line with historical data and forecasts
    df = pd.merge(df_historic, df_extended_cagr, on=first_column_name, how='left')
    df = pd.concat([df, df_forecast_ets.set_index(first_column_name), df_forecast_arima.set_index(first_column_name)], axis=1).reset_index(drop=True)

    # Set the correct years in the final df
    year_list = range(int(df[first_column_name].min()), max(forecast_years))
    df[first_column_name] = year_list

    # Create the figure and axes
    fig, ax = plt.subplots(figsize=(chart_width, chart_height))

    # Plot the historical publications line
    ax.plot(df[first_column_name], df[second_column_name], color=trend_line_color, marker='o', markersize=4, label="Número de Familias de Patentes Publicadas", linewidth=1.5)

    # Plot the extended CAGR projected line
    ax.plot(df_extended_cagr[first_column_name], df_extended_cagr["CAGR_Projected_Line"], color=cagr_line_color, linestyle='dotted', label="Línea Proyectada CAGR", linewidth=2.5)

    # Plot the ETS forecast
    ax.plot(df[first_column_name], df["Forecast_ETS"], color=forecast_ets_color, linestyle='dotted', label="Forecast ETS", linewidth=2.5)

    # Plot the ARIMA forecast
    ax.plot(df[first_column_name], df["Forecast_ARIMA"], color=forecast_arima_color, linestyle='dotted', label="Forecast ARIMA", linewidth=2.5)

    # Shade the background for the forecast years
    start_forecast_year = cutoff_year
    end_forecast_year = max(forecast_years)
    ax.axvspan(start_forecast_year, end_forecast_year, color='gray', alpha=0.1)  # Light gray background with transparency

    # Axis labels
    ax.set_xlabel(x_axis_label, fontsize=18)
    ax.set_ylabel(y_axis_label, fontsize=18)

    # Add a light gray, very thin grid
    ax.grid(True, color='lightgrey', linestyle='-', linewidth=0.35)

    # Function to wrap text labels
    def wrap_labels(labels, text_wrap_width=30):
        return ["\n".join(textwrap.wrap(label, width=text_wrap_width)) for label in labels]

    # Add the legend
    legend = ax.legend(loc='center left', bbox_to_anchor=(1, 0.9), fontsize=12, frameon=False)

    # Apply wrap to legend labels
    wrapped_labels1 = wrap_labels([text.get_text() for text in legend.get_texts()])

    # Assign wrapped labels to legends
    for text, wrapped_label in zip(legend.get_texts(), wrapped_labels1):
        text.set_text(wrapped_label)

    # Rotate the X-axis labels to avoid overlap
    ax.tick_params(axis='x', rotation=45)

    # Remove top and right spines
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    # Force the X-axis to show all years
    ax.set_xticks(df[first_column_name].tolist())
    ax.tick_params(axis='x', rotation=45)

    # Add annotations
    plt.figtext(-0.1, -0.1, '*El crecimiento anual compuesto (CAGR) indica la tasa de crecimiento promedio de un valor entre dos puntos en el tiempo, asumiendo un crecimiento acumulado.',
                ha="left", fontsize=12, color="black", wrap=True)

    plt.figtext(-0.1, -0.14, '** El modelo ARIMA proyecta series temporales considerando patrones históricos de autocorrelación, tendencias y estacionalidades para prever valores futuros.',
                ha="left", fontsize=12, color="black", wrap=True)
    
    plt.figtext(-0.1, -0.18, '*** El modelo ETS utiliza descomposición exponencial para prever tendencias, estacionalidad y nivel de una serie temporal, adaptándose dinámicamente a cambios en los datos.',
                ha="left", fontsize=12, color="black", wrap=True)

    plt.figtext(-0.1, -0.22, f'**** El número de publicaciones de familias de patentes ha variado con una Tasa de Crecimiento Anual Compuesta (CAGR) de {round(cagr_rate * 100, 2)}% para el periodo {start_year}-{end_year}, sin incluir {cutoff_year + 1} ni {cutoff_year + 2}.',
                ha="left", fontsize=12, color="black", wrap=True)
    
    # Save and display the chart    
    plt.tight_layout()
    plt.savefig(r"C:\Users\francisco.alvarez\Downloads\editable_forecast_chart.png", format='png', bbox_inches='tight')
    plt.savefig(r"C:\Users\francisco.alvarez\Downloads\editable_forecast_chart.svg", format='svg', bbox_inches='tight')
    plt.show()

# Example usage:
generate_evolution_and_forecast_chart()