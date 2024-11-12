# app.py: Main Application for Kinetic Energy Visualization
import streamlit as st
import streamlit.components.v1 as components
import numpy as np
from PIL import Image

# Placeholder imports (functions to be implemented in other modules later)
from data_handler import register_available_datasets, load_dataset, normalize_per_frame
from visualization import plot_histogram, render_heatmaps, plot_aa_distribution_by_frame_mid, plot_residue_category_distribution, show_frame_details
from reorder_handler import reorder_data, construct_KE_pairs, add_residue_category
from molvis import generate_ngl_viewer_html

# Setting up Streamlit page config
st.set_page_config(page_title="Kinetic Energy Visualization App", layout="wide", page_icon="favicon.ico")
logo = Image.open("icons/no_bg.png")
# Sidebar setup for dataset selection and login

def is_logged_in():
    return st.session_state.get('logged_in', False)

@st.cache_data
def cached_register_available_datasets():
    return register_available_datasets()

def setup_sidebar():
    def toggle_info_button(info_name):
        if info_name not in st.session_state:
            st.session_state[info_name] = False
        st.session_state[info_name] = not st.session_state[info_name]

    def toggle_info_button(info_name):
        if info_name not in st.session_state:
            st.session_state[info_name] = False
        st.session_state[info_name] = not st.session_state[info_name]
    def dropdown_w_info(selectbox_text, sbx_options_list, info_message, sbx_type, ib_counter=None, index=0):
        def create_info_button():
            if info_name not in st.session_state:
                st.session_state[info_name] = False
            st.button("ℹ️", key=f"info_button_{info_counter}", on_click=toggle_info_button, kwargs={'info_name':info_name})
            # st.write(f'info_counter: {info_counter}')

        col_res_1, col_res_2 = st.sidebar.columns([4, 1],vertical_alignment='bottom')
        with col_res_1:
            if sbx_type == 'selectbox':
                attribute = st.selectbox(selectbox_text, sbx_options_list, index=index, help=info_message)
            elif sbx_type == 'radio':
                attribute = st.radio(selectbox_text, sbx_options_list, index=index, help=info_message)
            else:
                raise ValueError(f'Unknown selectbox type option given to dropdown_w_info: {sbx_type}')
        with col_res_2:
            st.session_state['infobox_counter'] = info_counter = st.session_state.get('infobox_counter', 0) + 1 if ib_counter is None else ib_counter
            info_name = f'info_visible_{info_counter}'
            create_info_button()
        if st.session_state[info_name]:
            st.sidebar.write(info_message)
        return attribute
    
    col1, col2 = st.sidebar.columns(2, gap='medium', vertical_alignment='bottom')
    with col1:
        st.image(logo, width=140)
    # Title
    with col2:
        st.title("GROMACS Pulsed MD Kinetic Energy Analysis")
    
    # User Authentication (Placeholder UI)
    if not is_logged_in():
        col1, col2 = st.sidebar.columns(2)
        with col1:
            login = st.button("Log In")
        with col2:
            register = st.button("Register")
        if login:
            st.session_state['logged_in'] = True
            st.sidebar.write("Login functionality to be implemented...")
        if register:
            st.sidebar.write("Register functionality to be implemented...")
    else:
        logout = st.sidebar.button("Log Out")
        if logout:
            st.session_state['logged_in'] = False
            st.sidebar.write("Logout functionality to be implemented...")

    # Dataset Selection
    st.sidebar.subheader("Select Datasets")

    available_datasets = cached_register_available_datasets()
    
    resolution = dropdown_w_info(selectbox_text="Select Resolution", sbx_options_list=["residue", "atom"], info_message="Select the level of detail for the analysis: residue or atom.", sbx_type='selectbox', ib_counter=1)

    reference_category = dropdown_w_info(selectbox_text="Select Reference Run Category", sbx_options_list=["effective", "ineffective", "neutral"], info_message="Select the category of the reference run: effective, ineffective, or neutral.", sbx_type='selectbox')

    comparison_category = dropdown_w_info(selectbox_text="Select Comparison Run Category", sbx_options_list=["effective", "ineffective", "neutral"], info_message="Select the category of the comparison run: effective, ineffective, or neutral.", sbx_type='selectbox', index=2)
    
    reference_run = None
    comparison_run = None
    reference_data = None
    comparison_data = None

    if (resolution, reference_category) in available_datasets:
        reference_run = st.sidebar.selectbox("Select Reference Run", available_datasets[(resolution, reference_category)], key="reference_run")
        if reference_run:
            try:
                reference_data = load_dataset(reference_run, resolution, reference_category)
            except Exception as e:
                st.sidebar.write(f"Error loading reference dataset: {e}")
    else:
        st.sidebar.write("No datasets found for the selected resolution and reference category.")

    if (resolution, comparison_category) in available_datasets:
        comparison_run = st.sidebar.selectbox("Select Comparison Run", available_datasets[(resolution, comparison_category)], key="comparison_run")
        if comparison_run:
            try:
                comparison_data = load_dataset(comparison_run, resolution, comparison_category)
            except Exception as e:
                st.sidebar.write(f"Error loading comparison dataset: {e}")
    else:
        st.sidebar.write("No datasets found for the selected resolution and comparison category.")

    calculation_form = dropdown_w_info(selectbox_text="Select Calculation Form", sbx_options_list=["Linear KE", "Logarithmic KE"], info_message="Select whether to display kinetic energy values linearly or logarithmically.", sbx_type='radio')
     
    st.session_state['reordering_option'] = reordering_option = dropdown_w_info(selectbox_text="Select Reordering Option", sbx_options_list=["Original Order", "Reordered by Persistence", "Reordered by Streak Length", "Reordered by Absolute Persistence"], info_message="Choose how to reorder residues: keep the original order, reorder by persistence score, or by the longest streak above a percentile threshold. The persistence score represents how consistently a residue remains above a given per-frame percentile across all frames, while streak length measures the longest continuous period a residue exceeds that percentile. Note the appearing sliders below if you choose a reordering option.", sbx_type='radio')
    
    st.session_state['value_type'] = value_type = dropdown_w_info(selectbox_text="Select Value Type", sbx_options_list=["Absolute Values", "Per Frame Distribution"], info_message="Choose whether to use absolute kinetic energy values or normalize them per frame for comparison.", sbx_type='radio')
    
    # Add sliders for adjusting reordering thresholds
    if reordering_option != "Original Order":
        st.sidebar.subheader("Reordering Parameters")
        frame_min = st.sidebar.slider("Select Minimum Frame", min_value=0, max_value=200, value=42, step=1, help='The minimum frame, above which, the persistance or streak length will be evaluated.')
        frame_max = st.sidebar.slider("Select Maximum Frame", min_value=0, max_value=200, value=200, step=1, help='The maximum frame, below which, the persistance or streak length will be evaluated.')
        if reordering_option != "Reordered by Absolute Persistence":
            threshold = st.sidebar.slider("Select Threshold Percentile", min_value=0, max_value=100, value=70, step=1, help='The minimum per frame percentile threshold for a frame to be included in the persistence score or streak length calculation for a residue.' )
    
    norm_reference_data = normalize_per_frame(reference_data)
    norm_comparison_data = normalize_per_frame(comparison_data)
    if value_type == 'Per Frame Distribution':
        reference_data = norm_reference_data
        comparison_data = norm_comparison_data

    if reordering_option != "Original Order":
        if reordering_option != "Reordered by Absolute Persistence":
            reference_data, comparison_data = reorder_data(reference_data, comparison_data, reordering_option, frame_min=frame_min, frame_max=frame_max, threshold=threshold)
        else:
            reference_data, comparison_data = reorder_data(reference_data, comparison_data, reordering_option, frame_min=frame_min, frame_max=frame_max, threshold=70)
        
    if calculation_form == 'Logarithmic KE':
        reference_data = reference_data.applymap(lambda x: np.log10(x) if x > 0 else 0)
        comparison_data = comparison_data.applymap(lambda x: np.log10(x) if x > 0 else 0)
    
    return reference_data, comparison_data, resolution, reference_category, comparison_category, calculation_form, reordering_option, value_type, norm_reference_data, norm_comparison_data, reference_run, comparison_run


# Function to render interactive range panels for histogram and heatmap syncing
def render_range_panels(col4):
    def ranges_updated():
        st.session_state['ranges_updated'] = True
    if 'active_ranges' not in st.session_state:
        st.session_state['active_ranges'] = []
    # Histogram settings for bins and range
    with col4:
        st.write("#### Adjust Histogram Settings")
        bin_number_col, range_min_col, range_max_col = st.columns([1, 1, 1])
        with bin_number_col:
            st.session_state['bin_number'] = st.number_input("#Bins", min_value=1, value=st.session_state.get('bin_number', 50), step=1, on_change=ranges_updated)
        with range_min_col:
            active_range_min = (st.session_state['active_ranges'][0]['min'] if st.session_state['active_ranges'] else 4.7)
            plot_act_min = st.session_state.get('plot_range_min', 0.0)
            st.session_state['plot_range_min'] = st.number_input("Plot Range Min", value=(plot_act_min if plot_act_min <= active_range_min else active_range_min), max_value=active_range_min, min_value=0.0, step=0.1, on_change=ranges_updated)
        with range_max_col:
            active_range_max = (max([r['max'] for r in st.session_state['active_ranges']]) if st.session_state['active_ranges'] else 0.3)
            plot_act_max = st.session_state.get('plot_range_max', 4.0)
            st.session_state['plot_range_max'] = st.number_input("Plot Range Max", value=(plot_act_max if plot_act_max >= active_range_max else active_range_max), min_value=active_range_max, max_value=5.0, step=0.1, on_change=ranges_updated)
    if 'active_ranges' not in st.session_state:
        st.session_state['active_ranges'] = []

    # Button to add a new range (up to 2 allowed)
    if len(st.session_state['active_ranges']) < 2:
        with col4:
            if st.button("Add Range", key="add_range_button", on_click=ranges_updated):
                last_max = st.session_state['active_ranges'][-1]['max'] if st.session_state['active_ranges'] else 0.0
                st.session_state['active_ranges'].append({'min': last_max + 0.1, 'max': last_max + 1.0})
                st.session_state['ranges_updated'] = True

    # Render the panels for active ranges
    to_remove = []
    for idx, range_data in enumerate(st.session_state['active_ranges']):
        with col4:
            st.write(f"### Range {idx + 1}")
        with col4:
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                range_data['min'] = st.number_input(f"Min (Range {idx + 1})", value=range_data['min'], key=f"range_min_{idx}", min_value=0.0 if idx == 0 else st.session_state['active_ranges'][idx - 1]['max'], max_value=range_data['max']-0.1, format="%0.01f", step=0.1, on_change=ranges_updated)
            with col2:
                range_data['max'] = st.number_input(f"Max (Range {idx + 1})", value=range_data['max'], key=f"range_max_{idx}", min_value=range_data['min'] + 0.1, max_value=st.session_state['active_ranges'][idx + 1]['min'] if idx == 0 and len(st.session_state['active_ranges']) == 2 else 5.0, format="%0.01f", step=0.1, on_change=ranges_updated)
            with col3:
                if st.button(f"Remove Range {idx + 1}", key=f"remove_range_button_{idx}", on_click=ranges_updated):
                    to_remove.append(idx)

    # Remove ranges if requested
    for idx in reversed(to_remove):
        del st.session_state['active_ranges'][idx]

    # Button to update the plots
    with col4:
        st.button("Update Plots and Ranges", key="update_plots_button", on_click=ranges_updated)

# Main visualization area
def render_visualization(reference_data, comparison_data, resolution, reference_category, comparison_category, calculation_form, reordering_option, value_type, norm_reference_data, norm_comparison_data, KE_prc_threshold, reference_run, comparison_run):
    if reference_data is None or comparison_data is None:
        st.write("Error: Please select valid datasets for both the reference and comparison runs to visualize the results.")
        return
    
    # Placeholder for visualization (to be implemented in visualization.py later)
    st.write(f"### Visualization for Reference Run: {reference_category} vs Comparison Run: {comparison_category}")
    st.write(f"Resolution: {resolution}")
    st.write(f"Calculation Form: {calculation_form}, Reordering Option: {reordering_option}, Value Type: {value_type}")
    
    # Render synchronized heatmaps
    col1 = st.columns(1)[0]
    # heatmap_placeholder = col1.empty()

    # Render histogram with interactive vertical range indicators
    st.write("### Histogram of Values")
    col3, col4 = st.columns(2)
    histogram_placeholder = col3.empty()
    st.write("## Select one of the bars in charts below to see detailed info on the range.") 
    st.write("### Selection in the left graph takes precedence over right if both contain selections.")
    col6, col7 = st.columns(2)
    table1 = st.columns(1)[0]
    col8, col9, col10 = st.columns([2,3,1])
    # Render Pymol visualizations
    col5 = st.columns(1)[0]

    topology = None
    molecule_1_url = f'./trajectories/pdb/{reference_category}/traj_{reference_run}.pdb'
    molecule_2_url = f'./trajectories/pdb/{comparison_category}/traj_{comparison_run}.pdb'
    # molecule_2_url = molecule_1_url = "https://github.com/Elvis-crypto/GROMACS-KE-Analysis-App/blob/main/Calmod_sample.pdb"
    molecule_2_url = molecule_1_url = "https://github.com/Elvis-crypto/GROMACS-KE-Analysis-App/tree/main/1CRN.pdb"
    # topology = 'topologies/no_water.top'
    # molecule_1_url = f'trajectories/trr/{reference_category}/traj_{reference_run}.trr'
    # molecule_2_url = f'trajectories/trr/{comparison_category}/traj_{comparison_run}.trr'
    
    # We will estabilish the html code for the Pymol window here. Maybe move to a function later
    # URLs or file paths for the molecules in .pdb format
    # molecule_1_url = "https://files.rcsb.org/download/1CRN.pdb"  # Replace with your molecule URL or path
    # molecule_2_url = "https://files.rcsb.org/download/2B5C.pdb"  # Replace with your molecule URL or path

    # HTML code for NGL Viewer with grid view, DSS, and alignment setup
    html_code = f"""
        <div style="display: flex;">
            <div id="viewport1" style="width: 50%; height: 500px;"></div>
            <div id="viewport2" style="width: 50%; height: 500px;"></div>
        </div>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/ngl/2.0.0-dev.29/ngl.js"></script>
        <script>
            // Initialize two separate NGL Stages
            const stage1 = new NGL.Stage("viewport1");
            const stage2 = new NGL.Stage("viewport2");

            // Load first molecule into stage1
            stage1.loadFile("{molecule_1_url}").then(o => {{
                o.addRepresentation("cartoon", {{ color: "skyblue" }});
                stage1.autoView();
            }});

            // Load second molecule into stage2
            stage2.loadFile("{molecule_2_url}").then(o => {{
                o.addRepresentation("cartoon", {{ color: "tomato" }});
                stage2.autoView();
            }});

            // Flags for tracking mouse movements in each stage
            let mouseMovingStage1 = false;
            let mouseMovingStage2 = false;

            // Event listeners for mouse events for stage1
            document.getElementById("viewport1").addEventListener("mousedown", () => mouseMovingStage1 = true);
            document.getElementById("viewport1").addEventListener("mouseup", () => mouseMovingStage1 = false);

            // Event listeners for mouse events for stage2
            document.getElementById("viewport2").addEventListener("mousedown", () => mouseMovingStage2 = true);
            document.getElementById("viewport2").addEventListener("mouseup", () => mouseMovingStage2 = false);

            // Continuous synchronization loop to ensure alignment between stages
            function syncStages() {{
                // Sync the stages based on mouse movement
                if (!mouseMovingStage1) {{
                    // Get the camera parameters from stage2 and apply to stage1
                    stage1.viewerControls.orient(stage2.viewerControls.getOrientation());
                    stage1.viewer.requestRender();
                }}

                if (!mouseMovingStage2) {{
                    // Get the camera parameters from stage1 and apply to stage2
                    stage2.viewerControls.orient(stage1.viewerControls.getOrientation());
                    stage2.viewer.requestRender();
                }}

                // Request the next frame for sync
                requestAnimationFrame(syncStages);
            }}

            // Start the synchronization loop
            syncStages();
        </script>
    """

    KE_pairs = construct_KE_pairs(norm_reference_data, norm_comparison_data, step_res=5, KE_prc_threshold=KE_prc_threshold, resolution=resolution)
    KE_pairs = add_residue_category(KE_pairs)
    
    # Render range panels for histogram and heatmap syncing in col4
    render_range_panels(col4)
    if st.session_state.get('ranges_updated', False):
        st.session_state['ranges_updated'] = False
        st.rerun()
    with col3:
        fig = plot_histogram(reference_data, comparison_data, value_type, st.session_state.get('bin_number', 50), st.session_state.get('plot_range_min', 0.0), st.session_state.get('plot_range_max', 1.0), key="histogram")
    
    with col1:
        render_heatmaps(reference_data, comparison_data)

    with col6:
        clicked_bin_frame_mid1 = plot_aa_distribution_by_frame_mid(KE_pairs, KE_prc_threshold)
    with col7:
        clicked_bin_frame_mid2 = plot_residue_category_distribution(KE_pairs)
    
    with table1:
        st.write(KE_pairs)

    if clicked_bin_frame_mid1:
        clicked_bin_frame_mid = clicked_bin_frame_mid1
    elif clicked_bin_frame_mid2:
        clicked_bin_frame_mid = clicked_bin_frame_mid2
    else:
        clicked_bin_frame_mid = None
    if clicked_bin_frame_mid:
        show_frame_details(KE_pairs, clicked_bin_frame_mid, col8, col9, col10)
        
        # html_code = generate_ngl_viewer_html(clicked_bin_frame_mid, molecule_1_url, molecule_2_url, KE_pairs, topo_file_1=topology, topo_file_2=topology)
        with col5:
            st.write(molecule_1_url)
            components.html(html_code, height=600)
        



# Main function to run the Streamlit app
def main():
    if 'active_ranges' not in st.session_state:
        st.session_state['active_ranges'] = []
    reference_data, comparison_data, resolution, reference_category, comparison_category, calculation_form, reordering_option, value_type, norm_reference_data, norm_comparison_data, reference_run, comparison_run = setup_sidebar()
    
    # Render visualizations
    render_visualization(reference_data, comparison_data, resolution, reference_category, comparison_category, calculation_form, reordering_option, value_type, norm_reference_data, norm_comparison_data, KE_prc_threshold=0.1,  reference_run=reference_run, comparison_run=comparison_run)
        

if __name__ == "__main__":
    main()
