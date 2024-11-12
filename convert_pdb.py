import pandas as pd

# Dictionary to map three-letter residue codes to one-letter codes
RESIDUE_MAP = {
    'ALA': 'A', 'ARG': 'R', 'ASN': 'N', 'ASP': 'D',
    'CYS': 'C', 'GLU': 'E', 'GLN': 'Q', 'GLY': 'G',
    'HIS': 'H', 'ILE': 'I', 'LEU': 'L', 'LYS': 'K',
    'MET': 'M', 'PHE': 'F', 'PRO': 'P', 'SER': 'S',
    'THR': 'T', 'TRP': 'W', 'TYR': 'Y', 'VAL': 'V',
    'SEC': 'U', 'PYL': 'O',  # Uncommon residues
    'ASX': 'B', 'GLX': 'Z', 'XAA': 'X'  # Ambiguous codes
}

def parse_pdb_to_dataframe(pdb_file_path):
    # Initialize empty lists for each column
    atom_numbers = []
    residue_numbers = []
    residue_three_letter = []
    residue_one_letter = []
    atom_names = []

    # Open and read the .pdb file line by line
    with open(pdb_file_path, 'r') as file:
        for line in file:
            if line.startswith("ATOM") or line.startswith("HETATM"):
                # Parse atom number (column 7-11 in .pdb standard)
                atom_number = int(line[6:11].strip())
                atom_numbers.append(atom_number)
                
                # Parse atom name (column 13-16)
                atom_name = line[12:16].strip()
                atom_names.append(atom_name)
                
                # Parse residue three-letter code (column 17-20)
                res_three_letter = line[17:20].strip()
                residue_three_letter.append(res_three_letter)
                
                # Map three-letter code to one-letter code
                res_one_letter = RESIDUE_MAP.get(res_three_letter, 'X')  # Default to 'X' if not found
                residue_one_letter.append(res_one_letter)
                
                # Parse residue number (column 23-26)
                res_number = int(line[22:26].strip())
                residue_numbers.append(res_number)
    
    # Create DataFrame
    df = pd.DataFrame({
        'atom_number': atom_numbers,
        'atom_name': atom_names,
        'residue_number': residue_numbers,
        'residue_three_letter': residue_three_letter,
        'residue_one_letter': residue_one_letter
    })
    
    return df

if __name__ == '__main__':
    pdb_file_path = 'Calmod_sample.pdb'
    csv_file_path = 'aa_map.csv'

    # Parse the PDB file into a DataFrame
    pdb_df = parse_pdb_to_dataframe(pdb_file_path)
    
    # Save the DataFrame to a CSV file
    pdb_df.to_csv(csv_file_path, index=False)

    # Load the CSV file back into a DataFrame
    loaded_df = pd.read_csv(csv_file_path)
    
    # Print the loaded DataFrame
    print(loaded_df.head())