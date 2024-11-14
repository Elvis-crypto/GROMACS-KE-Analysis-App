import base64
from Bio import PDB  # Biopython's PDB module
from io import StringIO
import streamlit as st

def pdb_to_base64(pdb_content):
    """Convert PDB content to base64."""
    return base64.b64encode(pdb_content.encode('utf-8')).decode('utf-8')

def generate_pdb_base64_frame(pdb_file_path):
    """Read a local PDB file, process, and return it as base64-encoded string."""
    # Parse the PDB file
    parser = PDB.PDBParser(QUIET=True)
    structure = parser.get_structure("molecule", pdb_file_path)
    
    # Capture the PDB structure as text
    frame_content = StringIO()
    io = PDB.PDBIO()
    io.set_structure(structure)
    io.save(frame_content)
    
    # Retrieve text and convert to base64
    pdb_content = frame_content.getvalue()
    return pdb_to_base64(pdb_content)

# Specify the local path to the PDB file
local_pdb_file_path = "Calmod_sample.pdb"

# Convert the local file to a base64-encoded string
pdb_base64 = generate_pdb_base64_frame(local_pdb_file_path)

# Create NGL Viewer HTML with the base64 PDB data
html_code = f"""
    <div id="viewport" style="width: 100%; height: 500px;"></div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/ngl/2.0.0-dev.29/ngl.js"></script>
    <script>
        const stage = new NGL.Stage("viewport");
        const pdbData = "data:text/plain;base64,{pdb_base64}";
        stage.loadFile(pdbData, {{ ext: "pdb" }}).then(o => {{
            o.addRepresentation("cartoon", {{ color: "skyblue" }});
            stage.autoView();
        }});
    </script>
"""

# Display the NGL Viewer in Streamlit
st.components.v1.html(html_code, height=500)
