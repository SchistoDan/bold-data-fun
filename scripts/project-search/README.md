# UKBOL Project Search Tool

## Overview

This Python script identifies BOLD database records from specified projects that meet specific filtering criteria related to species gaps, BAGS conservation grades, and UK biogeographic representation. It is designed to process large datasets efficiently (~50,000 species, 2-3 million BOLD records).

## Purpose

The tool helps identify priority specimens for taxonomic verification by flagging records that:
- Represent potential undocumented species (BIN gaps)
- Have high priority (BAGS grades D and E)
- Are the sole UK representatives for their Barcode Index Number (BIN)

## Requirements

### Software
- Python 3.6 or higher
- pandas library (`pip install pandas`)

### Input Files

#### 1. Species List (`--species`)
**Format:** CSV file  
**Structure:** One species per line, with synonyms separated by semicolons  
**Example:**
```
Agyneta gulosa
Micaria alpina; Micaria alpinus
Walckenaeria clavicornis
```

**Details:**
- First name on each line is the valid/canonical species name
- Subsequent names (after `;`) are synonyms
- Species names are matched case-insensitively
- Two-word names match against the `species` field in BOLD data
- Three-word names match against the `subspecies` field in BOLD data

#### 2. BAGS Assessment (`--bags`)
**Format:** TSV (Tab-Separated Values)  
**Required Columns:**
- `taxonid`: Taxonomic identifier (matches BOLD `taxonid` field)
- `BAGS`: BAGS grade (A, B, C, D, E, F)

**Details:**
- BAGS = Barcode Audit and Grading System
- Grade E = multiple species in one BIN
- Grade D = less than 3 specimens in one BIN
- Subspecies inherit the species-level BAGS grade

#### 3. BOLD Database Records (`--bold`)
**Format:** TSV (Tab-Separated Values)  
**Required Columns:**
- `processid`: Unique specimen identifier (format: PROJECTNNN-YY)
- `taxonid`: Taxonomic identifier (links to BAGS data)
- `species`: Binomial species name (2 words)
- `subspecies`: Trinomial subspecies name (3 words) or "None"
- `bin_uri`: Barcode Index Number (format: BOLD:AAANNNN)
- `country_iso`: ISO country code (e.g., "GB" for United Kingdom)
- `phylum`, `class`, `order`, `family`: Taxonomic hierarchy

**Details:**
- File may contain mixed character encodings (handled automatically)
- Records filtered to specified projects based on `processid` prefix

#### 4. Project List (`--projects`)
**Format:** Plain text file  
**Structure:** One project code per line  
**Example:**
```
AALAR
AADBE
AAHYM
```

**Details:**
- Project codes match the prefix of BOLD `processid` values
- Example: processid "AALAR174-18" matches project "AALAR"

## Filtering Logic

### 1. BIN Gaps (`gaps`)
**Definition:** Records in BINs that contain NO species from the input species list

**Logic:**
```
For each BIN in BOLD data:
    1. Check if ANY record in that BIN has a species from our list
    2. If NO records match → all records in that BIN are "gaps"
```

**Interpretation:** These records may represent species not included in the UK species list, potentially indicating:
- Undocumented species
- Misidentifications
- Non-native species
- Species requiring taxonomic review

### 2. BAGS Grade E (`BAGS_E`)
**Definition:** Records where the species has BAGS grade E

**Logic:**
```
For each record:
    1. Look up taxonid in BAGS data
    2. If BAGS grade = 'E' → flag record
```

**Interpretation:** Priority specimens that should be identified by an expert to help untangle the E grade

### 3. BAGS Grade D (`BAGS_D`)
**Definition:** Records where the species has BAGS grade D

**Logic:**
```
For each record:
    1. Look up taxonid in BAGS data
    2. If BAGS grade = 'D' → flag record
```

**Interpretation:** Priority specimens that should be identified by an expert to increase the number of specimens in the BIN

### 4. UK Representatives (`UK_rep`)
**Definition:** UK records that are the only UK records in their BIN

**Logic:**
```
For each BIN:
    1. Count records with country_iso = 'GB' (UK records)
    2. Count records with country_iso != 'GB' (non-UK records)
    3. If BIN has both UK AND non-UK records → all UK records are flagged
```

**Interpretation:** Priority specimens for expert ID as they represent the only UK occurrence of their BIN.

## Output Files

### 1. Detailed Output (`project_search_output.tsv`)
**Format:** TSV file  
**Content:** All records matching at least one criterion

**Structure:**
- All original BOLD data columns
- Four additional boolean columns at the end:
  - `gaps`: True/False
  - `BAGS_E`: True/False
  - `BAGS_D`: True/False
  - `UK_rep`: True/False

**Notes:**
- Each record appears only once, even if it matches multiple criteria
- Multiple criteria are indicated by multiple True values in flag columns

### 2. Summary Output (`project_search_summary.tsv`)
**Format:** TSV file  
**Content:** Family-level aggregation of results

**Columns (in order):**
1. `Phylum`: Taxonomic phylum
2. `Class`: Taxonomic class
3. `Order`: Taxonomic order
4. `Family`: Taxonomic family
5. `gaps`: Count of gap records in this family
6. `BAGS_E`: Count of BAGS E records in this family
7. `BAGS_D`: Count of BAGS D records in this family
8. `UK_rep`: Count of UK representative records in this family

**Sorting:** Results sorted by taxonomic hierarchy (Phylum → Class → Order → Family)

### 3. Log File (`project_search_log.txt`)
**Format:** Plain text  
**Content:** Processing details including:
- Timestamp of execution
- Input file statistics (counts loaded)
- Filtering results (counts per criterion)
- Output statistics
- Any warnings or errors

## Usage

### Basic Command
```bash
python project_search.py \
    --species uksi_animals.csv \
    --bags assessed_BAGS.tsv \
    --bold result_output.tsv \
    --projects bioscan_projects.txt
```

### Arguments
- `--species`: Path to species CSV file (required)
- `--bags`: Path to BAGS TSV file (required)
- `--bold`: Path to BOLD TSV file (required)
- `--projects`: Path to projects text file (required)

### Output Location
All output files are created in the same directory as the script:
- `project_search_output.tsv`
- `project_search_summary.tsv`
- `project_search_log.txt`

## Performance Considerations

### Optimization Strategies
1. **Dictionary-based lookups:** O(1) species name matching using hash tables
2. **Set operations:** Efficient filtering using Python sets
3. **Pandas operations:** Vectorized operations where possible
4. **Encoding handling:** Automatic detection and handling of mixed encodings


## Example Workflow

### 1. Prepare Input Files
```
my_project/
├── uksi_animals.csv          (42,848 species)
├── assessed_BAGS.tsv         (47,447 taxa)
├── result_output.tsv         (2,500,000 records)
├── bioscan_projects.txt      (87 projects)
└── project_search.py
```

### 2. Run Script
```bash
cd my_project
python project_search.py \
    --species uksi_animals.csv \
    --bags assessed_BAGS.tsv \
    --bold result_output.tsv \
    --projects bioscan_projects.txt
```

### 3. Review Outputs
```
my_project/
├── project_search_output.tsv     (detailed results)
├── project_search_summary.tsv    (family summary)
└── project_search_log.txt        (processing log)
```
