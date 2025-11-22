#!/usr/bin/env python3
"""
UKBOL Project Search Tool

This script identifies BOLD records from specified BOLD projects that meet specific filtering criteria
related to species gaps, BAGS grades, and UK representation in BINs.

Usage:
    python project_search.py --species <species.csv> --bags <bags.tsv> --bold <bold.tsv> --projects <projects.txt>

Example:
    python project_search.py \\
        --species "C:\\_claude_files\\projects\\ukbol_bioscan\\test_species.csv" \\
        --bags "C:\\_claude_files\\projects\\ukbol_bioscan\\test_bags.tsv" \\
        --bold "C:\\_claude_files\\projects\\ukbol_bioscan\\test_bold.tsv" \\
        --projects "C:\\_claude_files\\projects\\ukbol_bioscan\\test_projects.txt"

Filtering Criteria:
    - gaps: Records in BINs with no species from the input species list
    - BAGS_E: Records with species having BAGS grade E (multiple names in a BIN)
    - BAGS_D: Records with species having BAGS grade D (less than 3 specimens in a BIN)
    - UK_rep: UK records that are the only UK representatives in their BIN

Output Files:
    - project_search_output.tsv: Detailed results with flag columns
    - project_search_summary.tsv: Family-level summary counts
    - project_search_log.txt: Processing log

Requirements:
    - Python 3.6+
    - pandas
    - argparse (standard library)

Authors: Ben Price and Claude Sonnet 4.5
Date: 2025
"""

import argparse
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import sys


def setup_logging(output_dir):
    """
    Configure logging to both file and console.
    
    Args:
        output_dir (Path): Directory for log file output
        
    Returns:
        logging.Logger: Configured logger instance
    """
    log_file = output_dir / "project_search_log.txt"
    
    # Create logger
    logger = logging.getLogger('project_search')
    logger.setLevel(logging.INFO)
    
    # File handler
    fh = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    fh.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger


def load_species_list(species_file, logger):
    """
    Load species list with synonyms from CSV file.
    
    Args:
        species_file (str): Path to species CSV file
        logger (logging.Logger): Logger instance
        
    Returns:
        dict: Dictionary mapping normalized species names to their canonical form
              e.g., {'agyneta gulosa': 'Agyneta gulosa', 'micaria alpinus': 'Micaria alpina'}
    """
    logger.info(f"Loading species list from: {species_file}")
    
    species_dict = {}
    
    with open(species_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
                
            # Split on semicolon to get primary name and synonyms
            names = [name.strip() for name in line.split(';') if name.strip()]
            
            if not names:
                continue
            
            # First name is the canonical/valid name
            canonical_name = names[0]
            
            # Add all names (including canonical) to dictionary, normalized to lowercase
            for name in names:
                normalized = name.lower()
                species_dict[normalized] = canonical_name
    
    logger.info(f"Loaded {len(species_dict)} species names (including synonyms)")
    logger.info(f"Unique valid species: {len(set(species_dict.values()))}")
    
    return species_dict


def load_bags_data(bags_file, logger):
    """
    Load BAGS grade data.
    
    Args:
        bags_file (str): Path to BAGS TSV file
        logger (logging.Logger): Logger instance
        
    Returns:
        dict: Dictionary mapping taxonid to BAGS grade
    """
    logger.info(f"Loading BAGS data from: {bags_file}")
    
    bags_df = pd.read_csv(bags_file, sep='\t', dtype={'taxonid': str})
    
    # Create dictionary for fast lookup
    bags_dict = dict(zip(bags_df['taxonid'], bags_df['BAGS']))
    
    logger.info(f"Loaded BAGS data for {len(bags_dict)} taxa")
    
    # Count by grade
    grade_counts = bags_df['BAGS'].value_counts().to_dict()
    for grade, count in sorted(grade_counts.items()):
        logger.info(f"  BAGS grade {grade}: {count} taxa")
    
    return bags_dict


def load_projects(projects_file, logger):
    """
    Load list of BOLD project codes.
    
    Args:
        projects_file (str): Path to projects text file
        logger (logging.Logger): Logger instance
        
    Returns:
        set: Set of project codes
    """
    logger.info(f"Loading project list from: {projects_file}")
    
    projects = set()
    
    with open(projects_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                projects.add(line)
    
    logger.info(f"Loaded {len(projects)} projects: {', '.join(sorted(projects))}")
    
    return projects


def matches_project(processid, projects):
    """
    Check if a processid matches any of the specified project codes.
    Project code must be followed immediately by a digit.
    
    Args:
        processid: Process ID to check
        projects (set): Set of project codes
        
    Returns:
        bool: True if processid matches a project code
    """
    if pd.isna(processid):
        return False
    processid_str = str(processid)
    for proj in projects:
        if processid_str.startswith(proj):
            # Check that the character after the project code is a digit
            if len(processid_str) > len(proj) and processid_str[len(proj)].isdigit():
                return True
    return False


def load_bold_data(bold_file, projects, logger):
    """
    Load BOLD data (unfiltered).
    
    Args:
        bold_file (str): Path to BOLD TSV file
        projects (set): Set of project codes (for logging only)
        logger (logging.Logger): Logger instance
        
    Returns:
        pd.DataFrame: Full BOLD data
    """
    logger.info(f"Loading BOLD data from: {bold_file}")
    
    # Try different encodings for BOLD data files which may have mixed encoding
    encodings_to_try = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
    
    bold_df = None
    for encoding in encodings_to_try:
        try:
            logger.info(f"Trying encoding: {encoding}")
            bold_df = pd.read_csv(bold_file, sep='\t', low_memory=False, encoding=encoding, encoding_errors='replace')
            logger.info(f"Successfully loaded with encoding: {encoding}")
            break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            logger.warning(f"Failed with encoding {encoding}: {str(e)}")
            continue
    
    if bold_df is None:
        raise ValueError("Could not load BOLD data with any supported encoding")
    
    initial_count = len(bold_df)
    logger.info(f"Loaded {initial_count:,} total BOLD records")
    
    return bold_df


def normalize_species_name(name):
    """
    Normalize species/subspecies name for comparison.
    
    Args:
        name: Species or subspecies name (can be None, string, or numeric)
        
    Returns:
        str: Normalized lowercase name, or empty string if None/invalid
    """
    if pd.isna(name) or name == 'None':
        return ''
    return str(name).strip().lower()


def get_species_name_from_record(row, species_dict):
    """
    Extract the appropriate species name from a BOLD record.
    Checks subspecies first (if 3 words), then species (if 2 words).
    
    Args:
        row: DataFrame row from BOLD data
        species_dict (dict): Dictionary of valid species names
        
    Returns:
        str: Canonical species name if found in species_dict, else empty string
    """
    # Check subspecies first (3-word name)
    subspecies = normalize_species_name(row.get('subspecies', ''))
    if subspecies and len(subspecies.split()) == 3:
        if subspecies in species_dict:
            return species_dict[subspecies]
    
    # Check species (2-word name)
    species = normalize_species_name(row.get('species', ''))
    if species and len(species.split()) == 2:
        if species in species_dict:
            return species_dict[species]
    
    return ''


def identify_gaps(bold_df, species_dict, logger):
    """
    Identify records in BINs that contain no species from the species list.
    
    Args:
        bold_df (pd.DataFrame): BOLD data
        species_dict (dict): Dictionary of valid species names
        logger (logging.Logger): Logger instance
        
    Returns:
        set: Set of processid values that are gaps
    """
    logger.info("Identifying BIN gaps...")
    
    # For each BIN, check if it contains ANY species from our list
    bin_has_known_species = defaultdict(bool)
    
    for idx, row in bold_df.iterrows():
        bin_uri = row.get('bin_uri', '')
        if pd.isna(bin_uri) or not bin_uri:
            continue
        
        # Check if this record's species is in our list
        matched_species = get_species_name_from_record(row, species_dict)
        if matched_species:
            bin_has_known_species[bin_uri] = True
    
    # Now identify all records in BINs that have NO known species
    gaps = set()
    
    for idx, row in bold_df.iterrows():
        bin_uri = row.get('bin_uri', '')
        if pd.isna(bin_uri) or not bin_uri:
            continue
        
        # If BIN has no known species, this record is a gap
        if not bin_has_known_species[bin_uri]:
            gaps.add(row['processid'])
    
    logger.info(f"Found {len(gaps)} gap records in {len([b for b, v in bin_has_known_species.items() if not v])} BINs")
    
    return gaps


def identify_bags_records(bold_df, bags_dict, species_dict, grade, logger):
    """
    Identify records with a specific BAGS grade.
    
    Args:
        bold_df (pd.DataFrame): BOLD data
        bags_dict (dict): Dictionary mapping taxonid to BAGS grade
        species_dict (dict): Dictionary of valid species names
        grade (str): BAGS grade to filter for ('D' or 'E')
        logger (logging.Logger): Logger instance
        
    Returns:
        set: Set of processid values with the specified BAGS grade
    """
    logger.info(f"Identifying BAGS grade {grade} records...")
    
    bags_records = set()
    
    for idx, row in bold_df.iterrows():
        taxonid = str(row.get('taxonid', ''))
        
        # Check if this taxon has the specified BAGS grade
        if taxonid in bags_dict and bags_dict[taxonid] == grade:
            bags_records.add(row['processid'])
    
    logger.info(f"Found {len(bags_records)} records with BAGS grade {grade}")
    
    return bags_records


def identify_uk_representatives(bold_df_full, projects, logger):
    """
    Identify UK records from target projects that are the only UK records in their BIN.
    Checks across the full BOLD dataset to see if other UK records exist outside the projects.
    
    Args:
        bold_df_full (pd.DataFrame): Full BOLD data (unfiltered)
        projects (set): Set of project codes
        logger (logging.Logger): Logger instance
        
    Returns:
        set: Set of processid values that are sole UK representatives
    """
    logger.info("Identifying UK-only representatives in BINs...")
    
    # Identify which processids are in our target projects
    project_processids = set()
    for idx, row in bold_df_full.iterrows():
        if matches_project(row['processid'], projects):
            project_processids.add(row['processid'])
    
    # Group by BIN and separate UK records: in projects vs outside projects
    bin_uk_records = defaultdict(lambda: {'in_projects': [], 'outside_projects': []})
    
    for idx, row in bold_df_full.iterrows():
        bin_uri = row.get('bin_uri', '')
        if pd.isna(bin_uri) or not bin_uri:
            continue
        
        country_iso = row.get('country_iso', '')
        processid = row['processid']
        
        # Only interested in UK records
        if country_iso == 'GB':
            if processid in project_processids:
                bin_uk_records[bin_uri]['in_projects'].append(processid)
            else:
                bin_uk_records[bin_uri]['outside_projects'].append(processid)
    
    # Flag UK records from projects that are the ONLY UK records in their BIN
    uk_reps = set()
    
    for bin_uri, records in bin_uk_records.items():
        # UK records exist in our projects AND no UK records exist outside our projects
        if records['in_projects'] and not records['outside_projects']:
            uk_reps.update(records['in_projects'])
    
    logger.info(f"Found {len(uk_reps)} UK representative records")
    
    return uk_reps


def create_output_dataframe(bold_df, gaps, bags_e, bags_d, uk_reps, logger):
    """
    Create output dataframe with flag columns for each criterion.
    
    Args:
        bold_df (pd.DataFrame): Original BOLD data
        gaps (set): Set of gap processids
        bags_e (set): Set of BAGS E processids
        bags_d (set): Set of BAGS D processids
        uk_reps (set): Set of UK representative processids
        logger (logging.Logger): Logger instance
        
    Returns:
        pd.DataFrame: DataFrame with original columns plus flag columns
    """
    logger.info("Creating output dataframe...")
    
    # Use ALL records from bold_df (which is already filtered to target projects)
    output_df = bold_df.copy()
    
    # Add flag columns (will be False for records not in the sets)
    output_df['gaps'] = output_df['processid'].isin(gaps)
    output_df['BAGS_E'] = output_df['processid'].isin(bags_e)
    output_df['BAGS_D'] = output_df['processid'].isin(bags_d)
    output_df['UK_rep'] = output_df['processid'].isin(uk_reps)
    
    # Count flagged records
    flagged_count = (output_df[['gaps', 'BAGS_E', 'BAGS_D', 'UK_rep']].any(axis=1)).sum()
    
    logger.info(f"Output contains {len(output_df)} total records from target projects")
    logger.info(f"  Records meeting at least one criterion: {flagged_count}")
    logger.info(f"  gaps: {output_df['gaps'].sum()}")
    logger.info(f"  BAGS_E: {output_df['BAGS_E'].sum()}")
    logger.info(f"  BAGS_D: {output_df['BAGS_D'].sum()}")
    logger.info(f"  UK_rep: {output_df['UK_rep'].sum()}")
    
    # Count records matching multiple criteria
    multi_criteria = (output_df[['gaps', 'BAGS_E', 'BAGS_D', 'UK_rep']].sum(axis=1) > 1).sum()
    logger.info(f"  Records matching multiple criteria: {multi_criteria}")
    
    return output_df


def create_summary_dataframe(output_df, logger):
    """
    Create family-level summary with counts per criterion.
    
    Args:
        output_df (pd.DataFrame): Output dataframe with flags
        logger (logging.Logger): Logger instance
        
    Returns:
        pd.DataFrame: Summary dataframe with taxonomic hierarchy and counts
    """
    logger.info("Creating family-level summary...")
    
    # Group by taxonomic hierarchy
    taxonomy_cols = ['phylum', 'class', 'order', 'family']
    flag_cols = ['gaps', 'BAGS_E', 'BAGS_D', 'UK_rep']
    
    # Sum flags by family
    summary = output_df.groupby(taxonomy_cols)[flag_cols].sum().reset_index()
    
    # Rename columns to match specification
    summary.columns = ['Phylum', 'Class', 'Order', 'Family', 'gaps', 'BAGS_E', 'BAGS_D', 'UK_rep']
    
    # Sort by taxonomic hierarchy
    summary = summary.sort_values(['Phylum', 'Class', 'Order', 'Family']).reset_index(drop=True)
    
    logger.info(f"Summary contains {len(summary)} families")
    
    return summary


def main():
    """
    Main execution function.
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='UKBOL BioScan Project Search Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python project_search.py --species species.csv --bags bags.tsv --bold bold.tsv --projects projects.txt
        """
    )
    
    parser.add_argument('--species', required=True, help='CSV file with species list and synonyms')
    parser.add_argument('--bags', required=True, help='TSV file with BAGS assessment data')
    parser.add_argument('--bold', required=True, help='TSV file with BOLD database records')
    parser.add_argument('--projects', required=True, help='Text file with project codes')
    
    args = parser.parse_args()
    
    # Determine output directory (same as script location)
    script_dir = Path(__file__).parent
    
    # Setup logging
    logger = setup_logging(script_dir)
    
    logger.info("=" * 80)
    logger.info("UKBOL BioScan Project Search Tool")
    logger.info("=" * 80)
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")
    
    try:
        # Load input files
        logger.info("Loading input files...")
        species_dict = load_species_list(args.species, logger)
        bags_dict = load_bags_data(args.bags, logger)
        projects = load_projects(args.projects, logger)
        bold_df_full = load_bold_data(args.bold, projects, logger)
        logger.info("")
        
        # Run filtering criteria
        logger.info("Applying filtering criteria...")
        
        # UK representatives needs full dataset to check for other UK records
        uk_reps = identify_uk_representatives(bold_df_full, projects, logger)
        
        # Filter to project records for other criteria
        logger.info("Filtering to target projects...")
        bold_df = bold_df_full[bold_df_full['processid'].apply(lambda pid: matches_project(pid, projects))].copy()
        filtered_count = len(bold_df)
        total_count = len(bold_df_full)
        logger.info(f"Filtered to {filtered_count:,} records from specified projects")
        logger.info(f"Removed {total_count - filtered_count:,} records from other projects")
        logger.info("")
        
        gaps = identify_gaps(bold_df, species_dict, logger)
        bags_e = identify_bags_records(bold_df, bags_dict, species_dict, 'E', logger)
        bags_d = identify_bags_records(bold_df, bags_dict, species_dict, 'D', logger)
        logger.info("")
        
        # Create outputs
        logger.info("Generating outputs...")
        output_df = create_output_dataframe(bold_df, gaps, bags_e, bags_d, uk_reps, logger)
        summary_df = create_summary_dataframe(output_df, logger)
        logger.info("")
        
        # Write output files
        logger.info("Writing output files...")
        
        output_file = script_dir / "project_search_output.tsv"
        output_df.to_csv(output_file, sep='\t', index=False)
        logger.info(f"Wrote detailed output: {output_file}")
        
        summary_file = script_dir / "project_search_summary.tsv"
        summary_df.to_csv(summary_file, sep='\t', index=False)
        logger.info(f"Wrote summary output: {summary_file}")
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("Processing completed successfully!")
        logger.info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Error during processing: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
