# visualization.py: Plotting Functions for Kinetic Energy Visualization
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import numpy as np
import pandas as pd

# Function to render synchronized heatmaps using Plotly subplots
def render_heatmaps(reference_data, comparison_data):
    # Create subplots for reference and comparison
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Reference Run Heatmap", "Comparison Run Heatmap"))
    
    colorscale = 'jet'
    # Get active range values for controlling colorscale, if defined
    if 'active_ranges' in st.session_state and len(st.session_state['active_ranges']) > 0:
        ranges = st.session_state['active_ranges']
        cmin = ranges[0]['min']
        cmax = ranges[-1]['max']
        # Handle two ranges scenario by setting values between ranges to the midpoint
        if len(ranges) > 1:
            mid_value = (cmin + cmax) / 2
            reference_data = reference_data.applymap(lambda x: mid_value if ranges[0]['max'] < x < ranges[1]['min'] else x)
            comparison_data = comparison_data.applymap(lambda x: mid_value if ranges[0]['max'] < x < ranges[1]['min'] else x)
    else:
        ranges = []
        cmin = reference_data.min().min()
        cmax = reference_data.max().max()

    # Extract y-axis labels from reference_data index
    y_labels = list(reference_data.index)
    y_values = list(range(len(y_labels)))

    # Create heatmaps for reference and comparison with explicitly set y-axis labels
    trace1 = go.Heatmap(
        z=reference_data.values,  # Use .values to avoid passing index
        y=y_values if st.session_state['reordering_option'] != "Original Order" else None,  # Numeric values corresponding to each row
        colorscale=colorscale,
        showscale=True,
        zmin=cmin,
        zmax=cmax
    )
    trace2 = go.Heatmap(
        z=comparison_data.values,  # Use .values to avoid passing index
        y=y_values if st.session_state['reordering_option'] != "Original Order" else None,  # Numeric values corresponding to each row
        colorscale=colorscale,
        showscale=False,
        zmin=cmin,
        zmax=cmax
    )

    # Add traces to figure
    fig.add_trace(trace1, row=1, col=1)
    fig.add_trace(trace2, row=1, col=2)

    # Use synchronized axes and add layout properties with explicit labels
    fig.update_layout(
        xaxis1=dict(matches='x2'),
        yaxis1=dict(matches='y2', tickvals=y_values, ticktext=y_labels) if st.session_state['reordering_option'] != "Original Order" else dict(matches='y2'),
        xaxis2=dict(matches='x1'),
        yaxis2=dict(matches='y1', tickvals=y_values, ticktext=y_labels) if st.session_state['reordering_option'] != "Original Order" else dict(matches='y1'),
        # yaxis2=dict(matches='y1'),
        title_text="Synchronized Heatmaps for Reference and Comparison Runs",
        # coloraxis_colorbar=dict(
        #     title="Value Range",
        #     tickvals=[r['min'] for r in ranges] + [r['max'] for r in ranges],
        #     ticktext=[f"Range {i + 1} Min" for i in range(len(ranges))] + [f"Range {i + 1} Max" for i in range(len(ranges))]
        # )
    )

    # Display the figure in Streamlit
    st.plotly_chart(fig, use_container_width=True)

# Function to plot histogram using Plotly

def plot_histogram(reference_data, comparison_data, value_type, bin_number, plot_range_min, plot_range_max, key):
    """
    Plots histograms of the provided reference and comparison datasets using Plotly.

    Args:
        reference_data (pd.DataFrame): The reference dataset.
        comparison_data (pd.DataFrame): The comparison dataset.
        value_type (str): Either 'Absolute Values' or 'Per Frame Distribution'.
        bin_number (int): The number of bins for the histogram.
        plot_range_min (float): The minimum value for the plot range.
        plot_range_max (float): The maximum value for the plot range.

    Returns:
        fig (plotly.graph_objects.Figure): The figure object containing the histogram plot.
    """
    if value_type == 'Per Frame Distribution':
        x_label = 'Kinetic Energy Proportion per Frame (%)'
    else:
        x_label = 'Kinetic Energy Values'
    
    # Flatten the data for histogram plotting
    reference_values = reference_data.values.flatten()
    comparison_values = comparison_data.values.flatten()
    
    # Filter values based on plot range
    reference_values = reference_values[(reference_values >= plot_range_min) & (reference_values <= plot_range_max)]
    comparison_values = comparison_values[(comparison_values >= plot_range_min) & (comparison_values <= plot_range_max)]
    
    # Create the histogram plot
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=reference_values, nbinsx=bin_number, name='Reference Run', opacity=0.5))
    fig.add_trace(go.Histogram(x=comparison_values, nbinsx=bin_number, name='Comparison Run', opacity=0.5))
    
    # Update layout
    fig.update_layout(
        title=f'{value_type} Histogram for Reference and Comparison Runs',
        xaxis_title=x_label,
        yaxis_title='Frequency',
        barmode='overlay',
    )
    fig.update_traces(marker_line_width=1, marker_line_color='black')
    # Draw vertical range indicators on the histogram
    if 'active_ranges' in st.session_state:
        for idx, range_data in enumerate(st.session_state['active_ranges']):
            fig.add_vrect(
                x0=range_data['min'], x1=range_data['max'],
                fillcolor='rgba(0, 100, 255, 0.2)' if idx == 0 else 'rgba(0, 255, 100, 0.2)',
                layer='below', line_width=0
            )
            fig.add_annotation(
                x=((range_data['min'] + range_data['max'])/2-plot_range_min)/(plot_range_max - plot_range_min),
                y=1.1,
                text=f"Range {idx + 1}",
                showarrow=False,
                xref="paper",
                yref="paper",
                bgcolor='rgba(0, 100, 255, 0.3)' if idx == 0 else 'rgba(0, 255, 100, 0.3)'
            )

    st.plotly_chart(fig, use_container_width=True, key=key)
    return fig
