import matplotlib.pyplot as plt
import squarify
import pandas as pd
import math

def generate_treemap_publications(num_groups):
    """
    Generates a treemap by first calculating layout geometry with squarify,
    then manually plotting rectangles and text with adjusted font sizes.
    """
    # Configuration
    plt.rcParams['svg.fonttype'] = 'none'
    plt.rcParams['font.sans-serif'] = ['Arial']

    # --- Parameters ---
    # (¡¡¡AJUSTA ESTAS RUTAS!!!)
    data_path = r"C:\Users\francisco.alvarez\Downloads\test.xlsx"
    sheet_name = "CPC subgroups"
    output_png_path = r"C:\Users\francisco.alvarez\Downloads\treemap_manual_layout.png"
    output_svg_path = r"C:\Users\francisco.alvarez\Downloads\treemap_manual_layout.svg"

    first_column_name = "CPC Subgroups"
    second_column_name = "Number of Publications"
    chart_width = 12
    chart_height = 8

    # --- Text display parameters (REQUIEREN AJUSTE) ---
    min_font_size = 6
    max_font_size = 16
    # AJUSTA ESTE FACTOR - Empieza bajo (e.g., 20-30) y sube si es necesario
    font_scale_factor = 350
    simplification_threshold_fontsize = 8

    # Load data
    try:
        df = pd.read_excel(data_path, sheet_name=sheet_name)
    except FileNotFoundError:
        raise Exception(f"File not found: {data_path}. Please verify.")
    except Exception as e:
        raise Exception(f"Error reading file: {e}")

    # Prepare data
    if df.columns[0] != first_column_name or df.columns[1] != second_column_name:
        df.rename(columns={df.columns[0]: first_column_name, df.columns[1]: second_column_name}, inplace=True)
    top_n_cpcs = df.nlargest(num_groups, second_column_name).copy()
    top_n_cpcs[first_column_name] = top_n_cpcs[first_column_name].str.title()

    # --- Calculate Layout Geometry using Squarify ---
    # Create Figure and Axes first to define the plotting area
    fig, ax = plt.subplots(figsize=(chart_width, chart_height))

    # Get the actual plotting area dimensions from the axes (usually 0 to 1)
    x_axis_min, x_axis_max = ax.get_xlim()
    y_axis_min, y_axis_max = ax.get_ylim()
    plot_width = x_axis_max - x_axis_min
    plot_height = y_axis_max - y_axis_min

    # Normalize the publication values for the layout algorithm
    # squarify expects a list of positive values
    values = top_n_cpcs[second_column_name].tolist()
    # Handle potential non-positive values if any (shouldn't happen with nlargest)
    values = [max(v, 0) for v in values]

    # Ensure values sum > 0 if there are any values
    if sum(values) > 0 :
         norm_sizes = squarify.normalize_sizes(values, plot_width, plot_height)
         # Calculate the rectangle geometries (list of dicts)
         # Each dict: {'x', 'y', 'dx', 'dy', 'value'} coords are within plot_width/height
         rects_data = squarify.squarify(norm_sizes, x_axis_min, y_axis_min, plot_width, plot_height)
    else:
         rects_data = [] # No data to plot

    # --- Manually Plot Rectangles and Text ---
    # Colors mapped to the original data order
    norm_color = plt.Normalize(top_n_cpcs[second_column_name].min(), top_n_cpcs[second_column_name].max())
    cmap = plt.cm.colors.LinearSegmentedColormap.from_list("custom_blue", ['#44b9be', '#0234a5', '#001f3f'])
    bar_colors = [cmap(norm_color(value)) for value in top_n_cpcs[second_column_name]]

    if len(rects_data) == len(top_n_cpcs):
        print("--- Starting Manual Plotting ---")
        for i, rect_geom in enumerate(rects_data):
            # Get geometry (note: dx, dy are width, height)
            x, y, dx, dy = rect_geom['x'], rect_geom['y'], rect_geom['dx'], rect_geom['dy']
            area = dx * dy

            # Get corresponding data entry
            cpc_label = top_n_cpcs.iloc[i][first_column_name]
            num_patents = top_n_cpcs.iloc[i][second_column_name]
            color = bar_colors[i] # Get color based on original data order

            print(f"\n--- Processing: {cpc_label} ---")
            print(f"Rect: x={x:.2f}, y={y:.2f}, dx={dx:.2f}, dy={dy:.2f}, Area: {area:.4f}")

            # Calculate font size based on geometry (dx, dy)
            full_label_text = f"{cpc_label}\n(No. Patentes: {num_patents})"
            simplified_label_text = cpc_label

            num_chars_full = len(full_label_text) + 1
            target_size_full = min_font_size
            if area > 1e-6 and num_chars_full > 0: # Avoid division by zero for tiny/zero areas
                # Scale factor adjusted for overall figure size (relative to default 12x8)
                # Use dx*dy (area in axes coords) directly. Maybe scale by plot_width*plot_height?
                # Heuristic: size proportional to sqrt(area / num_chars)
                target_size_full = math.sqrt(area / num_chars_full) * font_scale_factor * ((plot_width*plot_height)/(1.0*1.0)) # Assuming plot area is ~1x1

            final_font_size_full = max(min_font_size, min(max_font_size, target_size_full))
            print(f"Full Label Chars: {num_chars_full}, Target Size (Full): {target_size_full:.2f}, Final Size (Full): {final_font_size_full:.2f}")

            # Apply Simplification Logic
            display_label_text = full_label_text
            final_font_size = final_font_size_full

            if final_font_size_full < simplification_threshold_fontsize:
                display_label_text = simplified_label_text
                print(f"Simplification Triggered (Threshold={simplification_threshold_fontsize})")

                num_chars_simplified = len(display_label_text) + 1
                target_size_simplified = min_font_size
                if area > 1e-6 and num_chars_simplified > 0:
                     target_size_simplified = math.sqrt(area / num_chars_simplified) * font_scale_factor * ((plot_width*plot_height)/(1.0*1.0))
                     # Cap the recalculated size strictly
                     final_font_size = max(min_font_size, min(simplification_threshold_fontsize - 0.1, min(max_font_size, target_size_simplified)))
                else:
                     final_font_size = min_font_size
                print(f"Simplified Label Chars: {num_chars_simplified}, Target Size (Simpl.): {target_size_simplified:.2f}, Final Size (Simpl.): {final_font_size:.2f}")
            else:
                 print("Simplification Not Triggered.")

            # --- Draw the rectangle (Patch) ---
            if dx > 1e-6 and dy > 1e-6 : # Only draw if dimensions are positive
                rect_patch = plt.Rectangle((x, y), dx, dy,
                                           facecolor=color,
                                           edgecolor='black',
                                           linewidth=1.5,
                                           alpha=0.8)
                ax.add_patch(rect_patch)

                # --- Draw the text ---
                print(f"Using Label: '{display_label_text[:30].replace(chr(10),' ')}...', Font Size: {final_font_size:.2f}")
                ax.text(x + dx / 2, y + dy / 2, # Center text
                        display_label_text,
                        ha='center', va='center',
                        fontsize=final_font_size,
                        color='white',
                        fontweight='bold',
                        wrap=False # wrap=False likely better now
                       )

        print("\n--- Finished Manual Plotting ---")

    else:
         if len(rects_data) == 0 and sum(values) == 0:
              print("No data with positive values to plot.")
         else:
              print("Warning: Layout data size mismatch. Skipping plotting.")


    # Final Touches
    ax.axis('off')
    # Reset limits just in case squarify changed them, though it shouldn't
    ax.set_xlim(x_axis_min, x_axis_max)
    ax.set_ylim(y_axis_min, y_axis_max)

    # Color bar (needs the norm_color used for manual coloring)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm_color)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, orientation='vertical', shrink=0.8, pad=0.05)
    cbar.set_label('Número de Publicaciones', fontsize=18, color="black")
    plt.figtext(0,-0.1, f'* Un subgrupo CPC es una clasificación dentro del Sistema de Clasificación Cooperativa de Patentes, utilizado para categorizar invenciones según su tecnología y campo de aplicación.',
                ha="left", fontsize=12, color="black", wrap=True)

    # Save and Show
    plt.tight_layout()
    plt.savefig(output_png_path, format='png', bbox_inches='tight')
    plt.savefig(output_svg_path, format='svg', bbox_inches='tight')
    plt.show()

# --- Example Usage ---
generate_treemap_publications(num_groups=15)