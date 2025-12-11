# GBIF Name Processor

A Python script for processing GBIF species match outputs against a configurable rules matrix to determine whether to use original or GBIF-accepted names for taxonomic workflows.

## Overview

When reconciling specimen names against GBIF's taxonomic backbone, you often need to decide whether to keep the original name (e.g., for type specimens) or adopt GBIF's accepted name. This script automates that decision based on a rules matrix that considers:

- **Status**: ACCEPTED, SYNONYM, DOUBTFUL
- **Match type**: EXACT, FUZZY, HIGHERRANK
- **Species epithet**: same or different between input and GBIF
- **Genus**: same or different between input and GBIF
- **Type specimen status**: whether "type" appears in the occurrenceId

## Installation

No external dependencies required — uses Python standard library only.

```bash
# Clone or download the script
git clone <repository-url>
cd gbif-processor
```

Requires Python 3.6+

## Usage

```bash
python gbif_name_processor.py -i INPUT_FILE -r RULES_FILE [-o OUTPUT_DIR]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `-i`, `--input` | Yes | Input CSV file (GBIF species match output) |
| `-r`, `--rules` | Yes | Rules CSV file defining the decision matrix |
| `-o`, `--output-dir` | No | Output directory (default: same as input file) |

### Example

```bash
python gbif_name_processor.py -i XE-4013_output.csv -r gbif_rules.csv
```

## Input Files

### GBIF Match Output (input file)

A CSV file containing GBIF species match results. Expected columns:

| Column | Description |
|--------|-------------|
| `occurrenceId` | Specimen identifier (checked for "type" substring) |
| `verbatimScientificName` | Original input name |
| `status` | GBIF taxonomic status (ACCEPTED, SYNONYM, DOUBTFUL) |
| `matchType` | Match quality (EXACT, FUZZY, HIGHERRANK) |
| `species` | GBIF species binomial |
| `genus` | GBIF genus |
| `key` | GBIF taxon key |

### Rules File

A CSV file defining the decision matrix. See `gbif_rules.csv` for the full matrix.

| Column | Description |
|--------|-------------|
| `status` | ACCEPTED, SYNONYM, or DOUBTFUL |
| `matchType` | EXACT, FUZZY, or HIGHERRANK |
| `GBIF species value` | "same" or "different" (comparing species epithets) |
| `GBIF genus value` | "same" or "different" (comparing genera) |
| `Type specimen` | "YES" or "NO" |
| `name to use` | "original", "GBIF", or "not a possible combination" |
| `text to add to 'description' column...` | Optional description text (supports `[original]` placeholder) |
| `check ENA with GBIF name?` | "yes" or empty |
| `manual verification needed` | "yes" or empty |

## Output Files

The script generates three output files, prefixed with the input filename:

### 1. `{input}_request_taxid.tsv`

Tab-separated file for names where **original** should be used.

| Column | Description |
|--------|-------------|
| `verbatimScientificName` | The original name to use |
| `description` | GBIF species page hyperlink |

### 2. `{input}_check_ENA.csv`

CSV file for names where **GBIF name** should be used — these need checking against ENA/NCBI.

| Column | Description |
|--------|-------------|
| `verbatimScientificName` | The original name (to look up under GBIF's accepted name) |

### 3. `{input}_annotated.csv`

Complete copy of the input file with additional columns:

| Column | Description |
|--------|-------------|
| `name_to_use` | Decision: "original", "gbif", or "not a possible combination" |
| `description_text` | Text for taxonomy request description field |
| `check_ENA_with_GBIF` | "yes" if ENA check needed |
| `manual_verification_needed` | "yes" if manual review required |

## Decision Logic

The simplified decision rules (in order of precedence):

```
1. DOUBTFUL status           → Original (don't trust doubtful matches)
2. HIGHERRANK match          → Original (GBIF couldn't match to species)
3. ACCEPTED + EXACT          → Original (perfect match, name is accepted)
4. SYNONYM + TYPE specimen 
   + species epithet differs → Original (preserve type specimen names)
5. Everything else           → GBIF (use the accepted name)
```

### Type Specimen Handling

Type specimens receive special treatment: when GBIF returns a SYNONYM with a different species epithet, the original name is preserved. This maintains nomenclatural stability by keeping the original species epithet associated with the type.

## Example Output

```
$ python gbif_name_processor.py -i XE-4013_output.csv -r gbif_rules.csv

Created: XE-4013_output_request_taxid.tsv (479 rows)
Created: XE-4013_output_check_ENA.csv (24 rows)
Created: XE-4013_output_annotated.csv (503 rows)

Summary:
  Original: 479
  GBIF: 24
  Not possible: 0
  Unknown (no matching rule): 0
```

## Notes

- Input should contain **species-level names only**. Genus-only or higher-rank inputs may produce unexpected results.
- The "not a possible combination" entries in the rules file represent logically impossible scenarios (e.g., EXACT match with different genus AND species).
- If "Unknown (no matching rule)" appears in the summary, check that your rules file covers all relevant status/matchType combinations.