# reorder_handler.py: Reordering Functions for Kinetic Energy Data
import pandas as pd
import numpy as np
import itertools

# Function to calculate reordering statistics based on primary and secondary frame ranges
def calculate_reordering(reference_pivot, primary_range, secondary_range):
    """
    Calculates the primary and secondary statistics for reordering residues.

    Args:
        reference_pivot (pd.DataFrame): The pivot table for the reference run.
        primary_range (dict): The frame range for primary statistic calculation.
        secondary_range (dict): The frame range for secondary statistic calculation.
        use_median (bool): Whether to use median (default) or mean for the statistics.

    Returns:
        pd.Index: The reordered indices of the residues.
    """
    # Extract frames for primary and secondary ranges
    primary_frames = reference_pivot.loc[:, primary_range['min']:primary_range['max']]
    secondary_frames = reference_pivot.loc[:, secondary_range['min']:secondary_range['max']]

    # Calculate the primary and secondary statistics (using median)
    primary_stat = primary_frames.median(axis=1)
    secondary_stat = secondary_frames.median(axis=1)

    # Create a DataFrame for sorting with the same index as reference_pivot
    sorting_df = pd.DataFrame({
        'primary_stat': primary_stat,
        'secondary_stat': secondary_stat
    }, index=reference_pivot.index)

    # Sort the residues based on primary_stat descending, then secondary_stat descending
    sorted_df = sorting_df.sort_values(by=['primary_stat', 'secondary_stat'], ascending=[False, False])
    return sorted_df.index

# Function to calculate persistence scores and streak lengths for reordering

def calculate_persistence_score(df, frame_min, frame_max, threshold):
    """
    Calculate the persistence score for each residue, based on the proportion of frames where KE is above a threshold.
    
    :param df: The pivot table of KE values (residues x frames).
    :param frame_min: The minimum frame to consider for persistence detection.
    :param threshold: The threshold (percentile) above which we consider values for persistence detection.
    :return: A Series with the persistence score for each residue.

    Args:
        reference_pivot (pd.DataFrame): The pivot table for the reference run.
        frame_min (int): The minimum frame to consider.
        threshold (float): The threshold value to calculate persistence.

    Returns:
        pd.Series: Persistence scores for each residue.
    """
    # Focus on the region of interest (frames >= frame_min)
    df_region = df.loc[:, (df.columns >= frame_min) & (df.columns <= frame_max)]
    
    # Calculate the threshold value based on the provided percentile
    threshold_value = np.percentile(df_region.values, threshold)
    
    # Create a mask where values above the threshold are True
    above_threshold = df_region >= threshold_value
    
    # Calculate the persistence score (proportion of frames above the threshold for each residue)
    persistence_scores = above_threshold.mean(axis=1)
    return persistence_scores

def calculate_absolute_persistence_score(df, frame_min, frame_max):
    """
    Calculate the persistence score for each residue, based on the proportion of frames where KE is above a threshold.
    
    :param df: The pivot table of KE values (residues x frames).
    :param frame_min: The minimum frame to consider for persistence detection.
    :param threshold: The threshold (percentile) above which we consider values for persistence detection.
    :return: A Series with the persistence score for each residue.

    Args:
        reference_pivot (pd.DataFrame): The pivot table for the reference run.
        frame_min (int): The minimum frame to consider.
        threshold (float): The threshold value to calculate persistence.

    Returns:
        pd.Series: Persistence scores for each residue.
    """
    # Focus on the region of interest (frames >= frame_min)
    df_region = df.loc[:, (df.columns >= frame_min) & (df.columns <= frame_max)]
    
    persistence_scores = df_region.mean(axis=1)
    return persistence_scores

def detect_longest_streak(df, frame_min, frame_max, threshold):
    """
    Detect the longest streak (consecutive frames) of kinetic energy above a given threshold for each residue.
    
    :param df: The pivot table of KE values (residues x frames).
    :param frame_min: The minimum frame to consider for streak detection.
    :param threshold: The threshold above which we consider values for streak detection.
    :return: A Series with the longest streak length for each residue.
    """
    # Focus on the region of interest (frames >= frame_min)
    df_region = df.loc[:, (df.columns >= frame_min) & (df.columns <= frame_max)]
    
    # Calculate the threshold value based on the provided percentile
    threshold_value = np.percentile(df_region.values, threshold)
    
    # Create a mask where values above the threshold are True
    above_threshold = df_region >= threshold_value
    
    # Calculate streak lengths (consecutive True values in each row)
    streak_lengths = above_threshold.apply(lambda row: max((sum(1 for _ in group) for key, group in itertools.groupby(row) if key)), axis=1)
    
    return streak_lengths

def get_KE_ordered_index(pivot, frame_min, frame_max):
    index_order = calculate_absolute_persistence_score(pivot, frame_min, frame_max).rank(method='dense', ascending=False).sort_values().index
    return index_order

def construct_KE_pairs(reference_pivot, comparison_pivot, step_res, KE_prc_threshold, resolution):
    threshold_num = int(np.floor(len(reference_pivot) * KE_prc_threshold))
    result = pd.DataFrame(columns=[
        'bin_frame_start', 'bin_frame_stop', 'bin_frame_mid', 
        'reference_top_index', 'comparison_top_index'
    ])
    col_len = len(reference_pivot.columns)
    start_frame = 0
    stop_frame = step_res
    
    while stop_frame <= col_len:
        mid_frame = start_frame + int(np.ceil(step_res / 2))
        
        ref_indices = get_KE_ordered_index(reference_pivot, start_frame, stop_frame)[-threshold_num:]
        comp_indices = get_KE_ordered_index(comparison_pivot, start_frame, stop_frame)[-threshold_num:]
        
        # Create a new DataFrame row
        new_df = pd.DataFrame(columns=[
        'bin_frame_start', 'bin_frame_stop', 'bin_frame_mid', 
        'reference_top_index', 'comparison_top_index'
        ])
        new_df['reference_top_index'] = ref_indices
        new_df['comparison_top_index'] = comp_indices
        new_df['bin_frame_start'] = start_frame
        new_df['bin_frame_stop'] = stop_frame
        new_df['bin_frame_mid'] = mid_frame
                
        result = pd.concat([result, new_df], ignore_index=True)
        
        start_frame += step_res
        stop_frame += step_res

    # Load the CSV file back into a DataFrame for mapping
    aa_map = pd.read_csv('aa_map.csv')
    
    if resolution == 'atom':
        result = result.merge(aa_map, how='left', left_on='reference_top_index', right_on='atom_number',suffixes=(None, "_reference")).drop(columns=['reference_top_index'])
        result.rename(columns={'atom_name':'atom_name_reference', 'atom_number':'atom_number_reference', 'residue_number':'residue_number_reference', 'residue_three_letter':'residue_three_letter_reference'}, inplace=True)
        result = result.merge(aa_map, how='left', left_on='comparison_top_index', right_on='atom_number',suffixes=(None, "_comparison")).drop(columns=['comparison_top_index'])
        result.rename(columns={'atom_name':'atom_name_comparison', 'atom_number':'atom_number_comparison', 'residue_number':'residue_number_comparison', 'residue_three_letter':'residue_three_letter_comparison'}, inplace=True)
    elif resolution == 'residue':
        result = result.merge(aa_map[['residue_number', 'residue_three_letter']].drop_duplicates(), how='left', left_on='reference_top_index', right_on='residue_number',suffixes=(None, "_reference")).drop(columns=['reference_top_index'])
        result.rename(columns={'residue_number':'residue_number_reference', 'residue_three_letter':'residue_three_letter_reference'}, inplace=True)
        result = result.merge(aa_map[['residue_number', 'residue_three_letter']].drop_duplicates(), how='left', left_on='comparison_top_index', right_on='residue_number',suffixes=(None, "_comparison")).drop(columns=['comparison_top_index'])
        result.rename(columns={'residue_number':'residue_number_comparison', 'residue_three_letter':'residue_three_letter_comparison'}, inplace=True)
    else:
        raise ValueError("Invalid resolution. Choose 'atom' or 'residue'.")

    return result

def add_residue_category(result_df):
    # Create a set of residue numbers for reference and comparison by frame
    frame_residue_groups = (
        result_df.groupby(['bin_frame_mid', 'residue_number_reference', 'residue_number_comparison'])
        .apply(lambda x: set(x['residue_number_reference']).union(set(x['residue_number_comparison'])))
        .reset_index()
    )

    # Initialize the category column
    result_df['category_ref'] = 'Unclassified'
    result_df['category_comp'] = 'Unclassified'

    # Iterate over frames and assign categories
    for frame, frame_data in result_df.groupby('bin_frame_mid'):
        ref_residues = set(frame_data['residue_number_reference'].dropna())
        comp_residues = set(frame_data['residue_number_comparison'].dropna())

        # Assign categories based on conditions
        for index, row in frame_data.iterrows():
            residue_num_ref = row['residue_number_reference']
            residue_num_comp = row['residue_number_comparison']

            if pd.notna(residue_num_ref):
                if residue_num_ref in comp_residues:
                    result_df.at[index, 'category_ref'] = 'common'
                elif residue_num_ref - 1 in comp_residues or residue_num_ref + 1 in comp_residues:
                    result_df.at[index, 'category_ref'] = 'neighbour'
                else:
                    result_df.at[index, 'category_ref'] = 'reference only'
            if pd.notna(residue_num_comp):
                if residue_num_comp in ref_residues:
                    result_df.at[index, 'category_comp'] = 'common'
                elif residue_num_comp - 1 in ref_residues or residue_num_comp + 1 in ref_residues:
                    result_df.at[index, 'category_comp'] = 'neighbour'
                else:
                    result_df.at[index, 'category_comp'] = 'comparison only'

    return result_df

# Function to apply reordered indices to reference and comparison datasets
def reorder_data(reference_pivot, comparison_pivot, reordering_option, frame_min, frame_max, threshold):
    """
    Reorders the reference and comparison pivot tables based on the given indices.

    Args:
        reference_pivot (pd.DataFrame): The pivot table for the reference run.
        comparison_pivot (pd.DataFrame): The pivot table for the comparison run.
        reordered_indices (pd.Index): The reordered indices of the residues.

    Returns:
        tuple: Reordered reference and comparison pivot tables.
    """
    if reordering_option == "Reordered by Persistence":
        persistence_scores = calculate_persistence_score(reference_pivot, frame_min=frame_min, frame_max=frame_max, threshold=threshold)
        final_rank = persistence_scores.rank(method='dense', ascending=False)
    elif reordering_option == "Reordered by Streak Length":
        streak_lengths = detect_longest_streak(reference_pivot, frame_min, frame_max, threshold)
        final_rank = streak_lengths.rank(method='dense', ascending=False)
    elif reordering_option == "Reordered by Absolute Persistence":
        absolute_persistence_score = calculate_absolute_persistence_score(reference_pivot, frame_min, frame_max)
        final_rank = absolute_persistence_score.rank(method='dense', ascending=False)
    else:
        raise ValueError("Unhandled reordering option was passed")
    
    reordered_indices = final_rank.sort_values().index
    reordered_reference_pivot = reference_pivot.loc[reordered_indices, :]
    reordered_comparison_pivot = comparison_pivot.loc[reordered_indices, :]
    return reordered_reference_pivot, reordered_comparison_pivot
