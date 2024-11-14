# molvis.py: Molecule visualization module
import base64
from Bio import PDB  # Biopython's PDB module
from io import StringIO
import streamlit as st
import numpy as np

def pdb_to_base64(pdb_content):
    """Convert PDB content to base64."""
    return base64.b64encode(pdb_content.encode('utf-8')).decode('utf-8')

def generate_pdb_base64_frame(pdb_file_path, frame_number=0):
    """
    Read a local PDB file, extract a specific frame (MODEL), 
    and return it as a base64-encoded string along with the geometric center.
    """
    if st.session_state.get(pdb_file_path, None):
        model = st.session_state[pdb_file_path]
    else:
        parser = PDB.PDBParser(QUIET=True)
        structure = parser.get_structure("molecule", pdb_file_path)

        try:
            model = structure[frame_number]
        except KeyError:
            model = structure[0]
        st.session_state[pdb_file_path] = model

    # Calculate geometric center
    atom_coords = [atom.coord for atom in model.get_atoms()]
    center_of_mass = np.mean(atom_coords, axis=0)  # Compute geometric center
    
    # Convert the frame to base64
    frame_content = StringIO()
    io = PDB.PDBIO()
    io.set_structure(model)
    io.save(frame_content)
    pdb_content = frame_content.getvalue()
    
    return pdb_to_base64(pdb_content), center_of_mass.tolist()

def generate_ngl_viewer_html(frame_number, molecule_1_path, molecule_2_path, result_df):
    # Filter result_df for the selected frame
    selected_df = result_df[result_df['bin_frame_mid'] == frame_number]

    # Get the unique residues and their categories for each molecule
    molecule_1_residues = selected_df[['residue_number_reference', 'category_ref']].dropna()
    molecule_2_residues = selected_df[['residue_number_comparison', 'category_comp']].dropna()

    # Get base64 PDB content and centers
    pdb_base64_1, molecule_1_center = generate_pdb_base64_frame(molecule_1_path, frame_number)
    pdb_base64_2, molecule_2_center = generate_pdb_base64_frame(molecule_2_path, frame_number)


    # Function to create NGL selection scripts for residues
    def create_selection_script(residues, molecule_name1, molecule_name2):
        selection_script = ""
        color_map = {"common": "skyblue", "neighbour": "blue", "reference only": "pink", "comparison only": "red"}
        
        for _, row in residues.iterrows():
            residue_number = int(row[f'residue_number_{molecule_name1}'])
            category = row[f'category_{molecule_name2}']
            color = color_map.get(category, "gray")
            selection_script += f"""
                o.addRepresentation("ball+stick", {{
                    sele: ":A and {residue_number}",
                    color: "{color}"
                }});\n
            """
        return selection_script

    # Generate selection scripts for each molecule
    selection_script_1 = create_selection_script(molecule_1_residues, "reference", "ref")
    selection_script_2 = create_selection_script(molecule_2_residues, "comparison", "comp")

    # Load molecules into NGL as Blobs from base64
    load_molecule_1 = f"""
        const pdbBlob1 = new Blob([atob("{pdb_base64_1}")], {{ type: "text/plain" }});
        stage1.loadFile(pdbBlob1, {{ ext: "pdb" }}).then(o => {{
            o.addRepresentation("cartoon", {{ color: "#6A5ACD" }});
            stage1.autoView();
            {selection_script_1}
        }});
    """
    load_molecule_2 = f"""
        const pdbBlob2 = new Blob([atob("{pdb_base64_2}")], {{ type: "text/plain" }});
        stage2.loadFile(pdbBlob2, {{ ext: "pdb" }}).then(o => {{
            o.addRepresentation("cartoon", {{ color: "#F08080" }});
            stage2.autoView();
            {selection_script_2}
        }});
    """

    # HTML code for NGL Viewer with synchronized views
    html_code = f"""
    <div style="display: flex;">
        <div id="viewport1" style="width: 50%; height: 500px;"></div>
        <div id="viewport2" style="width: 50%; height: 500px;"></div>
    </div>
    <div style="margin-top: 10px;">
        <button id="snapshotButton">Save Snapshot</button>
        <button id="resetViewButton">Reset View</button>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/ngl/2.0.0-dev.29/ngl.js"></script>
    <script>
        const stage1 = new NGL.Stage("viewport1");
        const stage2 = new NGL.Stage("viewport2");

        // Load molecules into stage1 and stage2 as Blobs
        {load_molecule_1}
        {load_molecule_2}
        const standardOrientation = stage1.viewerControls.getOrientation()

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
        document.getElementById("snapshotButton").addEventListener("click", async () => {{
            // Capture snapshots from both stages
            const blob1 = await stage1.makeImage({{
                factor: 2,  // Image quality multiplier, 2x for better quality
                antialias: true,
                transparent: true
            }});
            const blob2 = await stage2.makeImage({{
                factor: 2,
                antialias: true,
                transparent: true
            }});

            // Load both images into canvases for side-by-side combination
            const canvas = document.createElement("canvas");
            const img1 = new Image();
            const img2 = new Image();

            // When both images are loaded, draw them on a combined canvas
            img1.onload = () => {{
                img2.onload = () => {{
                    const width = img1.width + img2.width;
                    const height = Math.max(img1.height, img2.height);
                    canvas.width = width;
                    canvas.height = height;
                    const ctx = canvas.getContext("2d");

                    // Draw the images on the combined canvas
                    ctx.drawImage(img1, 0, 0);
                    ctx.drawImage(img2, img1.width, 0);

                    // Download the combined snapshot
                    canvas.toBlob((combinedBlob) => {{
                        const a = document.createElement("a");
                        a.href = URL.createObjectURL(combinedBlob);
                        a.download = "ngl_combined_snapshot.png";
                        a.click();
                    }});
                }};
                img2.src = URL.createObjectURL(blob2);
            }};
            img1.src = URL.createObjectURL(blob1);
        }});

        // Reset View functionality
        document.getElementById("resetViewButton").addEventListener("click", () => {{
            stage1.viewerControls.orient(standardOrientation)
            stage2.viewerControls.orient(standardOrientation)
            stage1.autoView();  // Reset view for stage1
            stage2.autoView();  // Reset view for stage2
        }});
    </script>
    """
    
    return html_code
