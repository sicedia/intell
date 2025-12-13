import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.colors as mcolors
from matplotlib.ticker import MaxNLocator, FuncFormatter
import textwrap

def generate_horizontal_bar_chart_top_patent_applicants(top_n):
    """
    Generates a horizontal bar chart showing the top n patent applicants by the number of publications.

    This chart is based on data of patent publications by applicant.
    A color gradient is created to visually represent the range of publications among the highlighted applicants.
    Labels on the bars display both the number of publications and the percentage they represent relative to the total.

    Parameters:
    ----------
    top_n : int
        Number of applicants to display in the chart.

    Returns:
    --------
    None. The function generates and displays a chart directly.
    """

    # Configuration to preserve text in SVG
    plt.rcParams['svg.fonttype'] = 'none'  # Save text as text
    plt.rcParams['font.sans-serif'] = ['Arial']  

    # File path definition and other key settings
    data_path = r"C:\Users\francisco.alvarez\Downloads\test.xlsx"
    sheet_name = "Applicants"
    first_column_name = "Applicants"
    second_column_name = "Number of Publications"
    gradient_color_min = '#4fc0e5'
    gradient_color_max = '#1e3d8f'
    chart_width = 10
    chart_height = 8
    x_axis_label = 'Número de Patentes Publicadas'
    y_axis_label = 'Solicitantes'
    text_wrap_width = 25

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

    # Select the top n applicants by the number of publications
    top_n_applicants = df.nlargest(top_n, second_column_name)
    top_n_applicants = top_n_applicants.sort_values(by=second_column_name, ascending=True)

    # Generate a colormap to create a color gradient for the bars
    cmap = mcolors.LinearSegmentedColormap.from_list("mycmap", [gradient_color_min, gradient_color_max])

    # Normalize the values of 'Number of Publications' to the range [0, 1]
    min_val = top_n_applicants[second_column_name].min()
    max_val = top_n_applicants[second_column_name].max()
    normalized_vals = [(x - min_val) / (max_val - min_val) if max_val > min_val else 0.5 
                        for x in top_n_applicants[second_column_name]]

    # Convert normalized values into colors by applying the colormap
    colors = [cmap(val) for val in normalized_vals]

    # Function to wrap text labels to a maximum of specified characters per line
    def wrap_labels(labels, text_wrap_width):
        return ["\n".join(textwrap.wrap(label, width=text_wrap_width)) for label in labels]

    # Apply wrap_labels to the first column
    top_n_applicants[first_column_name] = wrap_labels(top_n_applicants[first_column_name], text_wrap_width)

    # Create the horizontal bar chart
    fig, ax = plt.subplots(figsize=[chart_width, chart_height])
    # Modify applicant names before using them in the chart
    top_n_applicants[first_column_name] = top_n_applicants[first_column_name].apply(lambda x: x.strip().title())
    bars = ax.barh(top_n_applicants[first_column_name], top_n_applicants[second_column_name], color=colors)

    # Force the X-axis to show only integer values
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: '{:,.0f}'.format(x)))

    # Calculate the total number of publications
    total_publications = df[second_column_name].sum()

    # Add labels with the number of publications and percentage (with thousand separators)
    label_offset = 0.025 * max_val
    for i, bar in enumerate(bars):
        num_publications = top_n_applicants[second_column_name].iloc[i]
        percentage = (num_publications / total_publications) * 100  # Calculate percentage
        ax.text(bar.get_width() + label_offset, 
                bar.get_y() + bar.get_height() / 2,
                f'{num_publications:,.0f} ({percentage:.2f}%)',
                ha='left', va='center')

    # Remove top and right axis ticks
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.xaxis.set_ticks_position('none')
    ax.yaxis.set_ticks_position('none')

    # Add labels to the x and y axes
    ax.set_xlabel(x_axis_label, fontsize=18, labelpad=12, color="black")
    ax.set_ylabel(y_axis_label, fontsize=18, labelpad=12, color="black")

    plt.figtext(-0.1, -0.075, f'* Los solicitantes de patentes son quienes tienen el derecho legal de presentar y reclamar la protección de una invención, lo que les otorga exclusividad para explotarla comercialmente.',
                ha="left", fontsize=12, color="black", wrap=True)

    plt.figtext(-0.1, -0.15, f'** Un solicitante puede ser una persona física o jurídica que busca proteger una invención mediante una patente, asegurando su control y aprovechamiento exclusivo de la innovación.',
                ha="left", fontsize=12, color="black", wrap=True)

    # Save and display the chart    
    plt.savefig(r"C:\Users\francisco.alvarez\Downloads\editable_applicant_chart.png", format='png', bbox_inches='tight')
    plt.savefig(r"C:\Users\francisco.alvarez\Downloads\editable_applicant_chart.svg", format='svg', bbox_inches='tight')
    plt.show()

# Example usage:
generate_horizontal_bar_chart_top_patent_applicants(top_n=15)