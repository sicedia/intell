import pandas as pd
import matplotlib.pyplot as plt
import datetime
import textwrap

def generate_cumulative_line_chart():
    """
    Generates a line chart showing the cumulative evolution of the number of patent publications over time.

    The chart represents the cumulative number of patent publications over a defined time period.
    This allows visualization of the total growth of patent publications year after year, highlighting the cumulative increase.

    Parameters:
    -----------
    None. All data and settings are defined within the function (file path, colors, analysis years, etc.).

    Returns:
    --------
    None. The function generates and displays the chart directly on the screen, with explanatory annotations about patent families and their protection.
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
    cumulative_line_color = '#001f3f'
    chart_width = 10
    chart_height = 8
    x_axis_label = 'Año'
    y_axis_label = 'Publicaciones de Patentes Acumulativas'

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

    # Add a column for cumulative values
    df[y_axis_label] = df[second_column_name].cumsum()

    # Create a figure and an axis
    fig, ax = plt.subplots(figsize=(chart_width, chart_height))

    # Plot cumulative evolution
    ax.plot(df[first_column_name], df[y_axis_label], color=cumulative_line_color, marker='o', markersize=4, label=y_axis_label, linewidth=1.5)

    # Labels and format for the X and Y axes
    ax.set_xlabel(x_axis_label, fontsize=18)
    ax.set_ylabel(y_axis_label, fontsize=18, color="black")
    ax.tick_params(axis='y', labelcolor="black")

    # Add a light gray, very thin grid
    ax.grid(True, color='lightgrey', linestyle='-', linewidth=0.35)

    # Function to wrap text labels
    def wrap_labels(labels, text_wrap_width=20):
        return ["\n".join(textwrap.wrap(label, width=text_wrap_width)) for label in labels]

    # Add the legend
    legend = ax.legend(loc='center left', bbox_to_anchor=(1, 0.9), fontsize=12, frameon=False)

    # Apply wrap to legend labels
    wrapped_labels1 = wrap_labels([text.get_text() for text in legend.get_texts()])

    # Assign wrapped labels to legends
    for text, wrapped_label in zip(legend.get_texts(), wrapped_labels1):
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
    plt.savefig(r"C:\Users\francisco.alvarez\Downloads\editable_cumulative_chart.png", format='png', bbox_inches='tight')
    plt.savefig(r"C:\Users\francisco.alvarez\Downloads\editable_cumulative_chart.svg", format='svg', bbox_inches='tight')
    plt.show()

# Example usage:
generate_cumulative_line_chart()