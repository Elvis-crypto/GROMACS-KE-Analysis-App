# molvis.py: Molecule visualization module

def generate_ngl_viewer_html(frame_number, molecule_1_url, molecule_2_url, result_df, topo_file_1=None, topo_file_2=None):
    # Filter result_df for the selected frame
    selected_df = result_df[result_df['bin_frame_mid'] == frame_number]

    # Get the unique residues and their categories for each molecule
    molecule_1_residues = selected_df[['residue_number_reference', 'category_ref']].dropna()
    molecule_2_residues = selected_df[['residue_number_comparison', 'category_comp']].dropna()

    # Function to create NGL selection scripts for residues
    def create_selection_script(residues, molecule_name1, molecule_name2):
        selection_script = ""
        color_map = {"common": "green", "neighbour": "orange", "reference only": "blue", "comparison only": "red"}
        
        for _, row in residues.iterrows():
            residue_number = int(row[f'residue_number_{molecule_name1}'])
            category = row[f'category_{molecule_name2}']
            color = color_map.get(category, "gray")
            selection_script += f"""
                o.addRepresentation("stick", {{
                    sele: ":{residue_number}",
                    color: "{color}"
                }});\n
            """
        return selection_script

    # Generate selection scripts for each molecule
    selection_script_1 = create_selection_script(molecule_1_residues, "reference", "ref")
    selection_script_2 = create_selection_script(molecule_2_residues, "comparison", "comp")

    # Conditional loading based on the presence of topology files
    load_molecule_1 = f"""
        Promise.all([
            {'stage1.loadFile("' + topo_file_1 + '"),' if topo_file_1 else ''}
            stage1.loadFile("{molecule_1_url}", {{ ext: "{'trr' if topo_file_1 else 'pdb'}" }})
        ]).then(([structure, traj]) => {{
            structure.addRepresentation("cartoon", {{ color: "skyblue" }});
            {'traj.setFrame(' + str(frame_number) + ');' if topo_file_1 else ''}
            {selection_script_1}
            stage1.autoView();
        }});"""

    load_molecule_2 = f"""
        Promise.all([
            {'stage2.loadFile("' + topo_file_2 + '"),' if topo_file_2 else ''}
            stage2.loadFile("{molecule_2_url}", {{ ext: "{'trr' if topo_file_2 else 'pdb'}" }})
        ]).then(([structure, traj]) => {{
            structure.addRepresentation("cartoon", {{ color: "tomato" }});
            {'traj.setFrame(' + str(frame_number) + ');' if topo_file_2 else ''}
            {selection_script_2}
            stage2.autoView();
        }});"""

    # HTML code for NGL Viewer with synchronized views
    html_code = f"""
    <div style="display: flex;">
        <div id="viewport1" style="width: 50%; height: 500px;"></div>
        <div id="viewport2" style="width: 50%; height: 500px;"></div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/ngl/2.0.0-dev.29/ngl.js"></script>
    <script>
        const stage1 = new NGL.Stage("viewport1");
        const stage2 = new NGL.Stage("viewport2");

        // Load molecules into stage1 and stage2
        {load_molecule_1}
        {load_molecule_2}

        // Sync camera orientations between stages
        let mouseMovingStage1 = false;
        let mouseMovingStage2 = false;

        document.getElementById("viewport1").addEventListener("mousedown", () => mouseMovingStage1 = true);
        document.getElementById("viewport1").addEventListener("mouseup", () => mouseMovingStage1 = false);
        document.getElementById("viewport2").addEventListener("mousedown", () => mouseMovingStage2 = true);
        document.getElementById("viewport2").addEventListener("mouseup", () => mouseMovingStage2 = false);

        function syncStages() {{
            if (!mouseMovingStage1) {{
                stage1.viewerControls.orient(stage2.viewerControls.getOrientation());
                stage1.viewer.requestRender();
            }}
            if (!mouseMovingStage2) {{
                stage2.viewerControls.orient(stage1.viewerControls.getOrientation());
                stage2.viewer.requestRender();
            }}
            requestAnimationFrame(syncStages);
        }}
        syncStages();
    </script>
    """
    
    return html_code