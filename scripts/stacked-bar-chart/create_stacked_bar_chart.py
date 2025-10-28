#!/usr/bin/env python3
"""
Create a horizontal stacked bar chart showing pass/fail percentages for various criteria.

Usage:
    python create_stacked_bar_chart.py input.csv output.png

Input CSV format:
    Criterion,Pass,Fail
    Species ID,96.2,3.8
    Type Specimen,0.2,99.8
    ...

The script will:
- Read the data from the CSV file
- Sort criteria by pass rate (descending)
- Create a horizontal stacked bar chart
- Add pass percentage labels on green bars (except Type Specimen and values < 5%)
- Save as PNG
"""

import argparse
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path


def create_stacked_bar_chart(input_file, output_file):
    """
    Create a horizontal stacked bar chart from CSV data.
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output PNG file
    """
    # Read the data
    df = pd.read_csv(input_file)
    
    # Ensure required columns exist
    required_cols = ['Criterion', 'Pass', 'Fail']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"CSV must contain columns: {required_cols}")
    
    # Sort by pass rate (descending)
    df_sorted = df.sort_values('Pass', ascending=True)  # ascending=True for matplotlib's horizontal bars
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Define colors
    pass_color = '#4ade80'  # Green
    fail_color = '#f87171'  # Red
    
    # Create horizontal stacked bars
    criteria = df_sorted['Criterion'].values
    pass_values = df_sorted['Pass'].values
    fail_values = df_sorted['Fail'].values
    
    y_pos = range(len(criteria))
    
    # Plot bars
    bars_pass = ax.barh(y_pos, pass_values, color=pass_color, label='Pass')
    bars_fail = ax.barh(y_pos, fail_values, left=pass_values, color=fail_color, label='Fail')
    
    # Add pass percentage labels on green bars
    for i, (criterion, pass_val) in enumerate(zip(criteria, pass_values)):
        # Skip Type Specimen and values < 5%
        if criterion != 'Type Specimen' and pass_val >= 5:
            ax.text(pass_val / 2, i, f'{pass_val:.1f}%', 
                   ha='center', va='center', 
                   color='white', fontweight='bold', fontsize=11)
    
    # Customize the plot
    ax.set_yticks(y_pos)
    ax.set_yticklabels(criteria, fontsize=10)
    ax.set_xlabel('Percentage (%)', fontsize=12)
    ax.set_xlim(0, 100)
    ax.set_title('Criteria Distribution (Pass/Fail)', fontsize=14, pad=20)
    
    # Add grid
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # Add legend
    ax.legend(loc='upper right', framealpha=0.9)
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    # Save the figure
    output_path = Path(output_file)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Chart saved to: {output_path.absolute()}")
    
    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description='Create a stacked bar chart from pass/fail criteria data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
    python create_stacked_bar_chart.py data.csv output.png

Input CSV format:
    Criterion,Pass,Fail
    Species ID,96.2,3.8
    Type Specimen,0.2,99.8
        """
    )
    
    parser.add_argument('input_file', type=str,
                       help='Path to input CSV file')
    parser.add_argument('output_file', type=str,
                       help='Path to output PNG file')
    
    args = parser.parse_args()
    
    # Validate input file exists
    input_path = Path(args.input_file)
    if not input_path.exists():
        parser.error(f"Input file not found: {input_path}")
    
    # Create the chart
    create_stacked_bar_chart(args.input_file, args.output_file)


if __name__ == '__main__':
    main()
