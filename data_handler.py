import os
import glob
import pandas as pd
from pathlib import Path

# Function to register available datasets from the pivots directory
def register_available_datasets():
    """
    Scans the 'pivots' directory and registers available datasets based on resolution and category.
    Returns a dictionary with keys as tuples (resolution, category) and values as lists of run numbers.
    """
    base_path = Path("pivots")
    available_datasets = {}

    # Iterate over the resolution types (residue or atom)
    for resolution in ["residue", "atom"]:
        resolution_path = base_path / resolution
        if resolution_path.exists():
            # Iterate over the run categories (effective, ineffective, neutral)
            for category in ["effective", "ineffective", "neutral"]:
                category_path = resolution_path / category
                if category_path.exists():
                    # Get the list of dataset files in the category path
                    dataset_files = glob.glob(f"{category_path}/data_pivot_*.pckl")
                    available_datasets[(resolution, category)] = [
                        Path(f).stem.split("_")[-1] for f in dataset_files
                    ]
    return available_datasets

# Function to load a dataset based on resolution, category, and run number
def load_dataset(run_num, resolution, category):
    """
    Loads the dataset for a given run number, resolution, and category.
    :param run_num: The run number to load (e.g., '0500').
    :param resolution: The resolution type ('residue' or 'atom').
    :param category: The run category ('effective', 'ineffective', 'neutral').
    :return: A pandas DataFrame of the dataset if found, otherwise None.
    """
    file_path = Path(f"pivots/{resolution}/{category}/data_pivot_{run_num}.pckl")
    
    if file_path.exists():
        try:
            dataset = pd.read_pickle(file_path)
            return dataset
        except Exception as e:
            print(f"Error loading dataset {run_num}: {e}")
            return None
    else:
        print(f"Dataset file not found: {file_path}")
        return None
    
# Normalize by frame to get relative distribution
def normalize_per_frame(data):
    data = data.div(data.sum(axis=1), axis=0)
    data *= 100
    return data