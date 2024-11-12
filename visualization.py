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

def plot_aa_distribution_by_frame_mid(result_df, n_percent):
    # Prepare the title
    title = f"Distribution of Residue Types Among the Top {n_percent*100}% Most Excited Residues"
    
    # Group by bin_frame_mid and residue_three_letter for both reference and comparison
    reference_grouped = (
        result_df.groupby(['bin_frame_mid', 'residue_three_letter_reference'])
        .size()
        .groupby(level=0, group_keys=False)
        .apply(lambda x: 100 * x / float(x.sum()))  # Normalize to 100%
        .reset_index(drop=False, name='percent')  # <--- Explicitly setting drop=False to keep bin_frame_mid
    )
    reference_grouped['group'] = 'Reference'
    reference_grouped.rename(columns={'residue_three_letter_reference': 'residue_three_letter'}, inplace=True)
    
    comparison_grouped = (
        result_df.groupby(['bin_frame_mid', 'residue_three_letter_comparison'])
        .size()
        .groupby(level=0, group_keys=False)
        .apply(lambda x: 100 * x / float(x.sum()))
        .reset_index(drop=False, name='percent')  # <--- Explicitly setting drop=False here as well
    )
    comparison_grouped['group'] = 'Comparison'
    comparison_grouped.rename(columns={'residue_three_letter_comparison': 'residue_three_letter'}, inplace=True)
    
    # Concatenate reference and comparison into a single DataFrame
    combined_df = pd.concat([reference_grouped, comparison_grouped], ignore_index=True)
    
    # Create the bar chart
    fig = px.bar(
        combined_df, 
        x="bin_frame_mid", 
        y="percent", 
        color="residue_three_letter",
        facet_col="group", 
        barmode="relative",
        title=title,
        labels={"bin_frame_mid": "Bin Frame Mid", "percent": "Percentage (%)"},
        hover_data={"percent": ":.2f"}
    )

    event_data = st.plotly_chart(fig, use_container_width=True, on_select='rerun')
    st.write(event_data)
    
    # Return the bin_frame_mid of the clicked bar if any bar was clicked
    if len(event_data['selection']['points']) > 0:
        clicked_bin_frame_mid = event_data['selection']['points'][0]['x']
        return clicked_bin_frame_mid
    else:
        return None
    
def plot_residue_category_distribution(result_df):
    # Count categories for reference and comparison by frame
    ref_counts = (
        result_df.groupby(['bin_frame_mid', 'category_ref'])
        .size()
        .reset_index(name='count')
        .assign(group='Reference')
    )
    
    comp_counts = (
        result_df.groupby(['bin_frame_mid', 'category_comp'])
        .size()
        .reset_index(name='count')
        .assign(group='Comparison')
    )

    # Rename the columns to align the category column between reference and comparison
    ref_counts.rename(columns={'category_ref': 'category'}, inplace=True)
    comp_counts.rename(columns={'category_comp': 'category'}, inplace=True)

    # Concatenate reference and comparison counts into a single DataFrame
    combined_counts = pd.concat([ref_counts, comp_counts], ignore_index=True)

    # Create the paired stacked bar chart
    fig = px.bar(
        combined_counts, 
        x="bin_frame_mid", 
        y="count", 
        color="category",
        facet_col="group", 
        barmode="relative",  # Stacks bars in a normalized, relative format within each frame
        title="Distribution of Residue Categories by Frame",
        labels={"bin_frame_mid": "Bin Frame Mid", "count": "Residue Count"},
        hover_data={"count": ":.0f"}
    )

    # Plot the chart in Streamlit and add click event functionality
    event_data = st.plotly_chart(fig, use_container_width=True, on_select='rerun')
    st.write(event_data)
    
    # Return the clicked frame if any bar was clicked
    if len(event_data['selection']['points']) > 0:
        clicked_bin_frame_mid = event_data['selection']['points'][0]['x']
        return clicked_bin_frame_mid
    else:
        return None
    
def show_frame_details(result_df, selected_frame, col1, col2, col3):
    # Filter and prepare the DataFrame for the selected frame
    selected_df = result_df[result_df['bin_frame_mid'] == selected_frame]
    frame_start = selected_df['bin_frame_start'].iloc[0]
    frame_stop = selected_df['bin_frame_stop'].iloc[0]
    
    # Display a slimmed-down version of the DataFrame in col1
    selected_df['AA_Ref'] = selected_df['residue_three_letter_reference'] + " " + selected_df['residue_number_reference'].astype(str)
    selected_df['AA_Comp'] = selected_df['residue_three_letter_comparison'] + " " + selected_df['residue_number_comparison'].astype(str)
    slim_df = selected_df[['AA_Ref', 'AA_Comp', 'category_ref', 'category_comp']]
    slim_df.columns = ['AA_Ref', 'AA_Comp', 'Cat_Ref', 'Cat_Comp']  # Rename for display
    col1.write(f"Data for Bin Frame {frame_start} - {frame_stop}")
    col1.dataframe(slim_df, use_container_width=True)

    # Prepare data for amino acid composition pie charts without residue numbers
    aa_ref_counts = selected_df['residue_three_letter_reference'].value_counts().reset_index()
    aa_ref_counts.columns = ['Amino Acid', 'Count']
    aa_comp_counts = selected_df['residue_three_letter_comparison'].value_counts().reset_index()
    aa_comp_counts.columns = ['Amino Acid', 'Count']

    # Create pie charts for amino acid composition in reference and comparison
    fig_aa = make_subplots(rows=1, cols=2, specs=[[{'type':'pie'}, {'type':'pie'}]],
                           subplot_titles=(f"Reference Amino Acid Composition<br>Frame {frame_start} - {frame_stop}", 
                                           f"Comparison Amino Acid Composition<br>Frame {frame_start} - {frame_stop}"))
    
    fig_aa.add_trace(
        go.Pie(labels=aa_ref_counts['Amino Acid'], values=aa_ref_counts['Count']),
        row=1, col=1
    )
    
    fig_aa.add_trace(
        go.Pie(labels=aa_comp_counts['Amino Acid'], values=aa_comp_counts['Count']),
        row=1, col=2
    )

    col2.plotly_chart(fig_aa, use_container_width=True)

    # Prepare data for the category composition bar chart with 'group' as x-axis
    ref_counts = selected_df['category_ref'].value_counts().reset_index()
    ref_counts.columns = ['Category', 'Count']
    ref_counts['group'] = 'Reference'
    
    comp_counts = selected_df['category_comp'].value_counts().reset_index()
    comp_counts.columns = ['Category', 'Count']
    comp_counts['group'] = 'Comparison'
    
    combined_counts = pd.concat([ref_counts, comp_counts], ignore_index=True)

    # Create the paired stacked bar chart for category composition in reference and comparison
    fig_cat = px.bar(
        combined_counts, 
        x="group", 
        y="Count", 
        color="Category",
        category_orders={"Category": ["common", "neighbour", "reference only", "comparison only"]},
        barmode="relative",  # Stacks bars in a normalized, relative format within each frame
        title=f"Residue Category Composition<br>Frame {frame_start} - {frame_stop}",
        labels={"group": "Group", "Count": "Residue Count"},
        hover_data={"Count": ":.0f"}
    )
    fig_cat.update_layout(showlegend=False)  # Hide legend to save space

    col3.plotly_chart(fig_cat, use_container_width=True)