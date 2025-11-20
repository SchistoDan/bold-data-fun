#!/usr/bin/env python3
"""
Create Species Sunburst - Wrapper for Custom Sunburst Charts

A specialized wrapper around sunburst_script.py that creates sunburst charts
with custom center labels and specific hierarchy configurations.

This script demonstrates how to:
- Load and process taxonomy data (Phylum > Order > Family)
- Create custom center labels (e.g., "Species" instead of default)
- Generate sunburst charts with specific styling
- Export in multiple formats (PNG, SVG, PDF)

Usage:
    1. Edit the csv_file path and level_cols to match your data
    2. Run: python create_species_sunburst.py

Customization:
    - Modify csv_file: Path to your CSV data file
    - Modify level_cols: Hierarchy columns ['Level1', 'Level2', 'Level3', None, None]
    - Modify line 208: Center label text (default: 'Species')
    - Modify output_file: Output filename (line 37)
    - Modify title: Chart title (line 38)

Output:
    - animal_species_sunburst.png: High-resolution PNG
    - animal_species_sunburst.svg: Editable vector format
    - animal_species_sunburst.pdf: Publication-ready PDF

Note: This is a template script. For general usage, use sunburst_script.py
      with command-line arguments instead.
"""

import sys
from sunburst_script import load_and_process_data, create_sunburst_chart

# Load data
csv_file = r'C:\GitHub\bold-data-fun\scripts\sunburst-plot\geneflow_unique_animals.csv'
level_cols = ['Phylum', 'Order', 'Family', None, None]

# Load and process
hierarchy, total_samples, active_levels = load_and_process_data(
    csv_file, 
    'Species',  # Sample ID column
    level_cols, 
    count_unique=False  # Count all records (each record is a unique species)
)

# Create chart with custom modifications
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from collections import defaultdict

# We'll use the core logic but need to modify the center label
# Let me import the necessary functions
from sunburst_script import (
    aggregate_small_slices, 
    calculate_total_recursive,
    generate_distinct_colors,
    generate_color_variations
)

# Chart parameters
output_file = 'animal_species_sunburst.png'
title = 'Animal Species from eDNA Dataset'
figsize = (18, 18)
line_width = 0.3
threshold_percent = 0.5
other_label = "Other"
label_threshold = 5.0
color_inherit_level = 1
color_mode = 'variations'

fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(aspect="equal"))

n_levels = len(active_levels)

# Define ring radii
center_radius = 0.15
ring_width = (0.85 - center_radius) / n_levels
radii = [center_radius + i * ring_width for i in range(n_levels + 1)]

print(f"Creating {n_levels} level sunburst with radii: {radii}")
print(f"Line width: {line_width}")
print(f"Small slice threshold: {threshold_percent}%")
print(f"Label threshold: {label_threshold} degrees")

# Apply small slice aggregation to level 1
processed_hierarchy = dict(hierarchy)
aggregation_info = {}

if threshold_percent > 0:
    print(f"Applying {threshold_percent}% threshold for small slice aggregation:")
    level1_totals = {k: calculate_total_recursive(v) for k, v in hierarchy.items()}
    total_for_level1 = sum(level1_totals.values())
    
    processed_hierarchy, aggregated_items = aggregate_small_slices(
        hierarchy, threshold_percent, total_for_level1, other_label
    )
    
    if aggregated_items:
        aggregation_info['level_1'] = aggregated_items

# Calculate totals and sort
level1_totals = {k: calculate_total_recursive(v) for k, v in processed_hierarchy.items()}
level1_sorted = sorted(level1_totals.items(), key=lambda x: x[1], reverse=True)

# Generate colors
level1_colors = generate_distinct_colors(len(level1_sorted))
base_color_map = {key: level1_colors[i] for i, (key, _) in enumerate(level1_sorted)}

segments = []

def process_level(data_dict, level, parent_angle_start, parent_angle_size, parent_color, path=[]):
    """Recursively process each level of the hierarchy"""
    if level >= n_levels:
        return
    
    # Apply small slice aggregation
    processed_data = data_dict
    if threshold_percent > 0 and level > 0 and other_label not in str(path):
        if isinstance(list(data_dict.values())[0], int):
            total_for_level = sum(data_dict.values())
        else:
            total_for_level = sum(calculate_total_recursive(v) for v in data_dict.values())
        
        processed_data, aggregated_items = aggregate_small_slices(
            data_dict, threshold_percent, total_for_level, other_label
        )
        
        if aggregated_items:
            level_key = f"level_{level + 1}"
            if level_key not in aggregation_info:
                aggregation_info[level_key] = []
            aggregation_info[level_key].extend([f"{'/'.join(path)}/{item}" for item in aggregated_items])
    
    # Sort items
    if isinstance(list(processed_data.values())[0], int):
        items_sorted = sorted(processed_data.items(), key=lambda x: x[1], reverse=True)
        total_for_level = sum(processed_data.values())
    else:
        items_sorted = sorted(processed_data.items(), key=lambda x: calculate_total_recursive(x[1]), reverse=True)
        total_for_level = sum(calculate_total_recursive(v) for v in processed_data.values())
    
    current_angle = parent_angle_start
    
    # Color scheme
    level_colors = []
    if level + 1 <= color_inherit_level:
        if level == 0:
            level_colors = [base_color_map.get(key, '#CCCCCC') for key, _ in items_sorted]
        else:
            level_colors = generate_distinct_colors(len(items_sorted))
    else:
        if color_mode == 'same':
            level_colors = [parent_color] * len(items_sorted)
        else:
            level_colors = generate_color_variations(parent_color, len(items_sorted))
    
    for i, (key, value) in enumerate(items_sorted):
        if isinstance(value, int):
            item_total = value
        else:
            item_total = calculate_total_recursive(value)
        
        angle_size = (item_total / total_for_level) * parent_angle_size
        segment_color = level_colors[i]
        
        segments.append({
            'level': level + 1,
            'start_angle': current_angle,
            'end_angle': current_angle + angle_size,
            'inner_radius': radii[level],
            'outer_radius': radii[level + 1],
            'color': segment_color,
            'label': f"{key}\n{item_total:,}",
            'key': key,
            'value': item_total,
            'path': path + [key]
        })
        
        if not isinstance(value, int) and level + 1 < n_levels:
            process_level(value, level + 1, current_angle, angle_size, segment_color, path + [key])
        
        current_angle += angle_size

# Process hierarchy
process_level(processed_hierarchy, 0, 0, 360, None, [])

# Draw segments
for segment in segments:
    wedge = mpatches.Wedge(
        (0, 0), segment['outer_radius'],
        segment['start_angle'], segment['end_angle'],
        width=segment['outer_radius'] - segment['inner_radius'],
        facecolor=segment['color'],
        edgecolor='white',
        linewidth=line_width
    )
    ax.add_patch(wedge)
    
    angle_size = segment['end_angle'] - segment['start_angle']
    show_label = angle_size > label_threshold
        
    if show_label:
        mid_angle = (segment['start_angle'] + segment['end_angle']) / 2
        mid_radius = (segment['inner_radius'] + segment['outer_radius']) / 2
        
        angle_rad = np.radians(mid_angle)
        x = mid_radius * np.cos(angle_rad)
        y = mid_radius * np.sin(angle_rad)
        
        rotation = mid_angle
        if mid_angle > 90 and mid_angle <= 270:
            rotation = mid_angle + 180
        
        base_fontsize = max(6, min(12, 14 - segment['level']))
        if angle_size < 10:
            fontsize = max(6, base_fontsize - 2)
        else:
            fontsize = base_fontsize
            
        fontweight = 'bold' if segment['level'] <= 2 else 'normal'
        
        ax.text(x, y, segment['label'], 
                horizontalalignment='center', verticalalignment='center',
                fontsize=fontsize, weight=fontweight, rotation=rotation,
                color='black')

# Add center circle with "Species" label
center_circle = plt.Circle((0, 0), center_radius, fc='white', ec='black', linewidth=3)
ax.add_patch(center_circle)

# CUSTOM CENTER LABEL - "Species" instead of default
ax.text(0, 0, f'Species\n{total_samples:,}', 
        horizontalalignment='center', verticalalignment='center',
        fontsize=14, weight='bold', color='black')

# Set plot properties
max_radius = radii[-1]
ax.set_xlim(-max_radius * 1.1, max_radius * 1.1)
ax.set_ylim(-max_radius * 1.1, max_radius * 1.1)
ax.set_aspect('equal')
ax.axis('off')

plt.title(title, fontsize=18, weight='bold', pad=20, color='black')

# Save files
plt.tight_layout()

save_params = {
    'bbox_inches': 'tight',
    'facecolor': 'white',
    'dpi': 300
}

plt.savefig(output_file, **save_params)
print(f"Sunburst chart saved as {output_file}")

# Save SVG
svg_file = output_file.replace('.png', '.svg')
plt.savefig(svg_file, format='svg', bbox_inches='tight', facecolor='white')
print(f"Also saved editable SVG version: {svg_file}")

# Save PDF
pdf_file = output_file.replace('.png', '.pdf')
plt.savefig(pdf_file, format='pdf', bbox_inches='tight', facecolor='white')
print(f"Also saved PDF version: {pdf_file}")

# Print summary
print(f"\nSummary Statistics:")
print(f"Total species: {total_samples:,}")
print(f"Number of levels: {n_levels}")
print(f"Line width: {line_width}")
print(f"Label threshold: {label_threshold} degrees")

if aggregation_info:
    print(f"\nSmall slice aggregation (threshold: {threshold_percent}%):")
    for level_key, items in aggregation_info.items():
        level_num = level_key.split('_')[1]
        print(f"  Level {level_num}: {len(items)} items aggregated into '{other_label}'")
        for item in items[:5]:
            print(f"    - {item}")
        if len(items) > 5:
            print(f"    ... and {len(items) - 5} more")

for i, level_name in enumerate(active_levels):
    level_segments = [s for s in segments if s['level'] == i + 1]
    print(f"Level {i+1} ({level_name}): {len(level_segments)} categories")

for key, total in level1_sorted:
    percentage = (total / total_samples) * 100
    print(f"  {key}: {total:,} species ({percentage:.1f}%)")

print("\n✓ Complete! Files saved in current directory.")
