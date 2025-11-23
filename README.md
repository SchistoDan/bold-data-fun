## BOLD DATA FUN

A place to organise and share scripts used to manipulate BOLD data into other formats for downstream processing.

### Scripts

#### [CSV Mapper](scripts/csv-mapper)
Advanced choropleth map generator that creates professional geographic visualizations from CSV data. Features smart label placement, multiple color schemes, custom boundaries, and publication-quality output in PNG/SVG formats.

#### [Extract Taxonomy](scripts/extract-taxonomy)
Extracts taxonomy information from BOLD project TSV files based on plate IDs. Automatically handles multiple BOLD data formats and provides robust error handling. Helpful when partners don't use Plate_Well as their sample ID.

#### [Merge TSV](scripts/merge-tsv)
Two-stage TSV merging tools for BOLD data exports. First script merges multiple TSV files from individual datasets, second script combines multiple merged datasets into a unified file. Handles UUID field mapping and complex BOLD data structures.

#### [Stacked Bar Chart](scripts/stacked-bar-chart)
Creates horizontal stacked bar charts showing pass/fail percentages for various criteria. Automatically sorts by pass rate, includes smart label placement (hiding labels for small values and specific criteria), and generates publication-quality PNG output with customizable colors.

#### [Sunburst Plot](scripts/sunburst-plot)
Creates hierarchical sunburst charts from CSV data with support for 3-5 levels of hierarchy. Features intelligent color inheritance, smart labeling, slice aggregation for small categories, and multiple output formats (PNG, SVG, PDF).

#### [Project Search](scripts/project-search)
Identifies BOLD records from specified projects that meet filtering criteria related to species gaps, BAGS grades, and UK representation in BINs. Processes species lists with synonyms and generates detailed results with family-level summaries.
