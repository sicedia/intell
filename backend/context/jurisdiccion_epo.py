import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.colors as mcolors
from matplotlib.ticker import MaxNLocator, FuncFormatter

def generate_horizontal_bar_chart_top_patent_countries(top_n):
    """
    Generates a horizontal bar chart showing the top n jurisdictions by the number of patent publications.

    This chart is based on data of patent publications by jurisdiction.
    Ecuador is specifically highlighted if present in the data, and an additional bar is added for "Others"
    which represents the sum of publications from jurisdictions not included in the top n and excluding Ecuador.

    The chart uses a color gradient for the jurisdictions in the top n, while Ecuador and "Others" have fixed colors.
    Labels are also displayed on each bar indicating the number of publications and the percentage they represent 
    with respect to the total.

    Parameters:
    ----------
    top_n : int
        Number of jurisdictions to display in the chart.

    Returns:
    --------
    None. The function generates and displays a chart directly.
    """

    # Configuration to preserve text in SVG
    plt.rcParams['svg.fonttype'] = 'none'  # Save text as text
    plt.rcParams['font.sans-serif'] = ['Arial']  

    # File path definition and other key settings
    data_path = r"C:\Users\francisco.alvarez\Downloads\test.xlsx"
    sheet_name = "Countries (family)"
    first_column_name = "Country"
    second_column_name = "Number of Publications"
    gradient_color_min = '#4fc0e5'
    gradient_color_max = '#1e3d8f'
    ecuador_bar_color = '#eebe5a'
    others_bar_color = '#46ad65'
    chart_width = 10
    chart_height = 8
    x_axis_label = 'Número de Patentes Publicadas'
    y_axis_label = 'Jurisdicción'

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

    # Check if Ecuador is present in the data and get its rank and number of publications
    ecuador_rank, ecuador_publications = None, None
    if 'EC' in df['Country'].values:
        ecuador_info = df[df['Country'] == 'EC']
        ecuador_rank = ecuador_info.index[0] + 1  # Rank is 1-indexed
        ecuador_publications = ecuador_info[second_column_name].values[0]

    # Select the top n countries by the number of publications
    top_n_countries = df.nlargest(top_n, second_column_name)

    # Filter countries that are not in the top n and are not Ecuador
    other_countries = df[~df['Country'].isin(top_n_countries['Country']) & (df['Country'] != 'EC')]

    # Sum the number of publications for countries grouped under "Others"
    other_sum = other_countries[second_column_name].sum()

    # Create a DataFrame for the "Others" category
    others_df = pd.DataFrame([{'Country': 'Others', second_column_name: other_sum}])

    # Combine data for the top n countries, Ecuador (if present), and "Others"
    if ecuador_rank is not None:
        top_n_and_ecuador = pd.concat([top_n_countries, ecuador_info, others_df])
    else:
        top_n_and_ecuador = pd.concat([top_n_countries, others_df])

    # Sort combined data by the number of publications in ascending order for visualization
    top_n_and_ecuador.sort_values(second_column_name, ascending=True, inplace=True)

    # Move "Others" to the bottom if it exists
    if 'Others' in top_n_and_ecuador['Country'].values:
        top_n_and_ecuador = top_n_and_ecuador[top_n_and_ecuador['Country'] != 'Others']
        others_row = pd.DataFrame([{'Country': 'Others', second_column_name: other_sum}])
        top_n_and_ecuador = pd.concat([others_row, top_n_and_ecuador], ignore_index=True)

    # Generate a colormap to create a color gradient for the bars
    cmap = mcolors.LinearSegmentedColormap.from_list("mycmap", [gradient_color_min, gradient_color_max])

    # Normalize the values of 'Number of Publications' to the range [0, 1]
    min_val = top_n_and_ecuador[second_column_name].min()
    max_val = top_n_and_ecuador[second_column_name].max()
    normalized_vals = [(x - min_val) / (max_val - min_val) if max_val > min_val else 0.5 
                       for x in top_n_and_ecuador[second_column_name]]

    # Assign colors to the bars: Ecuador and Others have specific colors, others follow the gradient
    bar_colors = []
    for norm_val, country in zip(normalized_vals, top_n_and_ecuador['Country']):
        if country == 'EC':
            bar_colors.append(ecuador_bar_color)
        elif country == 'Others':
            bar_colors.append(others_bar_color)
        else:
            bar_colors.append(cmap(norm_val))

    # Create the horizontal bar chart
    fig, ax = plt.subplots(figsize=[chart_width, chart_height])
    bars = ax.barh(top_n_and_ecuador['Country'], top_n_and_ecuador[second_column_name], color=bar_colors)

    # Force the X-axis to show only integer values
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: '{:,.0f}'.format(x)))

    # Calculate the total number of publications
    total_publications = top_n_and_ecuador['Number of Publications'].sum()

    # Add labels with the number of publications and percentage (with thousand separators)
    label_offset = np.round(0.025 * max_val)
    for i, bar in enumerate(bars):
        num_publications = top_n_and_ecuador["Number of Publications"].iloc[i]
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

    # Annotate Ecuador's rank and number of publications as a note at the bottom of the chart
    if ecuador_rank is not None and ecuador_publications is not None:
        plt.figtext(0, 0, f'* Ecuador # Rango {ecuador_rank} (Número de Patentes Publicadas en Ecuador: {ecuador_publications:,})',
                    ha="left", fontsize=12, color="black", wrap=True)

    # Add additional information if "WO" is present in the data
    if 'WO' in df['Country'].values:
        plt.figtext(0, -0.075, '** "WO" indica que la publicación de la patente es internacional bajo el Tratado de Cooperación en Materia de Patentes (PCT), administrado por la OMPI.',
                    ha="left", fontsize=12, color="black", wrap=True,
                    bbox=dict(facecolor='white', alpha=0.5, edgecolor='none'))

    # Add additional information if "EP" is present in the data
    if 'EP' in df['Country'].values:
        plt.figtext(0, -0.15, '*** "EP" indica que la publicación de la patente corresponde a la Oficina Europea de Patentes (EPO), gestionada por el Convenio sobre la Patente Europea, cubriendo protección en sus estados miembros.',
                    ha="left", fontsize=12, color="black", wrap=True,
                    bbox=dict(facecolor='white', alpha=0.5, edgecolor='none'))

    # Save and display the chart    
    plt.savefig(r"C:\Users\francisco.alvarez\Downloads\editable_jurisdiction_chart.png", format='png', bbox_inches='tight')
    plt.savefig(r"C:\Users\francisco.alvarez\Downloads\editable_jurisdiction_chart.svg", format='svg', bbox_inches='tight')
    plt.show()

# Example usage:
generate_horizontal_bar_chart_top_patent_countries(top_n=15)
