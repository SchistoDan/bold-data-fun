# Stacked Bar Chart Generator

A Python script that creates professional horizontal stacked bar charts showing pass/fail percentages for various criteria.

## Features

- **Horizontal Stacked Layout**: Clear visualization of pass/fail distributions
- **Automatic Sorting**: Criteria sorted by pass rate (descending)
- **Smart Label Placement**: Pass percentage labels on green bars
- **Selective Labeling**: Skips labels for Type Specimen and values < 5%
- **Publication Quality**: High-resolution PNG output (300 DPI)
- **Clean Design**: Professional color scheme (green for pass, red for fail)

## Requirements

```bash
pip install pandas matplotlib pathlib
```

## Usage

### Basic Usage

```bash
python create_stacked_bar_chart.py input.csv output.png
```

### Command Line Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `input_file` | String | Yes | Path to input CSV file |
| `output_file` | String | Yes | Path to output PNG file |

## Input CSV Format

The input CSV must contain three columns:

| Column | Type | Description |
|--------|------|-------------|
| `Criterion` | String | Name of the criterion being evaluated |
| `Pass` | Float | Percentage that passed (0-100) |
| `Fail` | Float | Percentage that failed (0-100) |

### Example Input CSV

```csv
Criterion,Pass,Fail
Species ID,96.2,3.8
Genus,95.8,4.2
Family,98.1,1.9
Country,99.5,0.5
Coordinates,45.2,54.8
Type Specimen,0.2,99.8
Voucher Photo,78.9,21.1
```

## Output

The script generates:
- **PNG file**: High-resolution chart (300 DPI) at specified output path
- **Automatic sorting**: Bars sorted by pass rate (highest to lowest)
- **Smart labels**: Pass percentages displayed on green bars (except for special cases)

## Examples

### Basic Example

```bash
# Create chart from criteria data
python create_stacked_bar_chart.py quality_metrics.csv quality_chart.png
```

### With Custom Data

```bash
# Biodiversity data quality metrics
python create_stacked_bar_chart.py bold_quality.csv bold_quality_chart.png
```

## Chart Appearance

### Visual Features

- **Green bars (Pass)**: #4ade80 - Light, vibrant green
- **Red bars (Fail)**: #f87171 - Soft red
- **Labels**: White text on green bars, bold font
- **Grid**: Light horizontal gridlines for easier reading
- **Y-axis**: Criterion names, clearly labeled
- **X-axis**: Percentage scale (0-100%)
- **Legend**: Upper right corner showing Pass/Fail

### Smart Labeling Rules

The script applies intelligent labeling to avoid clutter:

1. **Skip Type Specimen**: This criterion typically has very low pass rates
2. **Skip Small Values**: Pass percentages < 5% don't show labels (too small)
3. **All Others**: Show pass percentage centered on green bar

## Use Cases

### Quality Assessment

```csv
Criterion,Pass,Fail
Taxonomy Complete,94.5,5.5
Geographic Data,88.2,11.8
Sequence Quality,96.8,3.2
Photo Available,72.4,27.6
```

### Completeness Metrics

```csv
Criterion,Pass,Fail
Required Fields,99.1,0.9
Recommended Fields,76.3,23.7
Optional Fields,45.8,54.2
```

### Validation Results

```csv
Criterion,Pass,Fail
Format Validation,98.7,1.3
Data Consistency,94.2,5.8
Reference Check,89.5,10.5
Cross-validation,91.8,8.2
```

## Customization

### Modifying Colors

To change the color scheme, edit these lines in the script:

```python
pass_color = '#4ade80'  # Green - change hex code here
fail_color = '#f87171'  # Red - change hex code here
```

### Adjusting Figure Size

Modify the `figsize` parameter:

```python
fig, ax = plt.subplots(figsize=(10, 8))  # Width, Height in inches
```

### Changing Label Threshold

Modify the minimum pass percentage for labels:

```python
if criterion != 'Type Specimen' and pass_val >= 5:  # Change 5 to desired minimum
```

## Output Validation

The script will:
1. Verify input file exists
2. Check for required columns (Criterion, Pass, Fail)
3. Create chart with proper sorting
4. Save to specified output path
5. Print confirmation message

## Error Handling

Common errors and solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| `FileNotFoundError` | Input CSV not found | Check file path |
| `ValueError: CSV must contain columns` | Missing required columns | Ensure CSV has Criterion, Pass, Fail |
| `Permission denied` | Cannot write output | Check output directory permissions |

## Tips

1. **Data Preparation**: Ensure Pass + Fail = 100% for each criterion
2. **File Paths**: Use absolute paths or ensure working directory is correct
3. **Column Names**: Must exactly match: "Criterion", "Pass", "Fail" (case-sensitive)
4. **Output Format**: Currently supports PNG only (300 DPI for publication quality)
5. **Chart Width**: Default 10 inches works well for 5-15 criteria

## Example Workflow

```bash
# 1. Prepare your data
cat > data.csv << EOF
Criterion,Pass,Fail
Species ID,96.2,3.8
Genus,95.8,4.2
Family,98.1,1.9
Type Specimen,0.2,99.8
EOF

# 2. Generate chart
python create_stacked_bar_chart.py data.csv output_chart.png

# 3. View result
# Chart saved to: /path/to/output_chart.png
```

## Advanced Usage

### Integration with Data Pipeline

```python
import pandas as pd

# Calculate pass/fail percentages from raw data
df = pd.read_csv('raw_data.csv')
criteria = {}

for criterion in ['Species ID', 'Genus', 'Family']:
    total = len(df)
    passed = df[df[criterion].notna()].shape[0]
    criteria[criterion] = {
        'Pass': (passed / total) * 100,
        'Fail': ((total - passed) / total) * 100
    }

# Create input CSV for chart script
output_df = pd.DataFrame.from_dict(criteria, orient='index')
output_df.reset_index(inplace=True)
output_df.columns = ['Criterion', 'Pass', 'Fail']
output_df.to_csv('chart_input.csv', index=False)
```

## License

This script is provided as-is for data visualization purposes.
