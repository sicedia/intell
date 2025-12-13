import pandas as pd
import matplotlib.pyplot as plt
import datetime
import textwrap

def generate_line_chart_evolution():
    """
    Generates a line chart showing the annual evolution of the number of patent publications, with historical data limited to a defined period.

    The chart represents the number of patent publications per year over a defined time period, allowing visualization of the historical trend.
    The chart includes annotations that explain key concepts related to patents.

    Parameters:
    -----------
    None. All values, such as file path, colors, and visualization settings, are defined within the function.

    Returns:
    --------
    None. The function generates and displays the chart directly on screen, with legends and explanatory annotations.
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
    chart_width = 10
    chart_height = 8
    x_axis_label = 'Año'
    y_axis_label = 'Número de Patentes Publicadas'

    # Load data, with exception handling for common errors
    try:
        df = pd.read_excel(data_path, sheet_name=sheet_name)
    except FileNotFoundError:
        raise Exception(f"The file at path {data_path} was not found. Please verify the path.")
    except Exception as e:
        raise Exception(f"An error occurred while reading the file: {e}")

    # Rename columns if names do not match expected values
    if df.columns[0] != first_column_name or df.columns[1] != second_column_name:
        df.rename(columns={df.columns[0]: first_column_name, df.columns[1]: second_column_name}, inplace=True)

    # Filter the dataframe to exclude the current and previous year
    df = df[(df[first_column_name] <= cutoff_year) & (df[first_column_name] > (cutoff_year - historical_years))]

    # Create a range of years from the minimum to the maximum year in the filtered DataFrame
    complete_years = pd.DataFrame({first_column_name: range(df[first_column_name].min(), df[first_column_name].max() + 1)})

    # Merge with the original DataFrame to ensure all years are present
    df = pd.merge(complete_years, df, on=first_column_name, how='left')

    # Fill missing years with 0 in 'Number of Publications'
    df[second_column_name] = df[second_column_name].fillna(0)

    # Create a figure and axis
    fig, ax = plt.subplots(figsize=(chart_width, chart_height))

    # Plot the evolution of the number of publications as a line
    ax.plot(df[first_column_name], df[second_column_name], color=trend_line_color, marker='o', markersize=4, label=y_axis_label, linewidth=1.5)

    # Labels and format for the Y-axis
    ax.set_xlabel(x_axis_label, fontsize=18)
    ax.set_ylabel(y_axis_label, color="black", fontsize=18)
    ax.tick_params(axis='y', labelcolor="black")
    ax.tick_params(axis='y', color="black")

    # Add a light gray, very thin vertical grid
    ax.grid(True, color='lightgrey', linestyle='-', linewidth=0.35)

    # Function to wrap text labels
    def wrap_labels(labels, text_wrap_width=20):
        return ["\n".join(textwrap.wrap(label, width=text_wrap_width)) for label in labels]

    # Add the legends
    legend = ax.legend(loc='center left', bbox_to_anchor=(1, 0.9), fontsize=12, frameon=False)

    # Apply wrap to legend labels
    wrapped_labels = wrap_labels([text.get_text() for text in legend.get_texts()])

    # Assign wrapped labels to legends
    for text, wrapped_label in zip(legend.get_texts(), wrapped_labels):
        text.set_text(wrapped_label)

    # Remove top and right axis ticks
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    # Force the X-axis to show all years
    ax.set_xticks(df[first_column_name].tolist())
    ax.tick_params(axis='x', rotation=45)

    # Add annotations with explanatory information about patent families
    plt.figtext(0, -0.075,
                '* Se muestran las publicaciones hasta hace 2 años, porque los documentos de patente suelen demorar hasta 18 meses en su publicación.',
                ha="left", fontsize=12, color="black", wrap=True)

    # Save and display the chart    
    plt.savefig(r"C:\Users\francisco.alvarez\Downloads\editable_trend_chart.png", format='png', bbox_inches='tight')
    plt.savefig(r"C:\Users\francisco.alvarez\Downloads\editable_trend_chart.svg", format='svg', bbox_inches='tight')
    plt.show()
    
# Example usage:
generate_line_chart_evolution()

