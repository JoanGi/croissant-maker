# File Filtering & Discovery

This document explains the file discovery and filtering mechanisms in `croissant-maker`.

## Overview

By default, `croissant-maker` recursively scans the input directory and processes every supported file it finds. For larger datasets, or when you only want to generate metadata for a subset of files, you can use the filtering options.

## Features

### Inclusion Filtering (`--include`, `-I`)
Specify one or more glob patterns to include only matching files.
- `croissant-maker -i dataset --include "*.csv"`
- `croissant-maker -i dataset -I "data/*.parquet" -I "metadata/*.json"`

### Exclusion Filtering (`--exclude`, `-E`)
Specify patterns to ignore certain files or directories. Exclusion happens *after* inclusion.
- `croissant-maker -i dataset --exclude "tmp/*"`
- `croissant-maker -i dataset -I "*.jpg" -E "thumbnails/*"`

### Dry Run (`--dry-run`)
Preview which files will be included in the metadata generation without actually running the processing logic.
- `croissant-maker -i dataset --include "*.csv" --dry-run`

## Implementation Details

### File Discovery (`croissant_maker.files`)
The core discovery logic is in `discover_files()`. It uses `pathlib.Path.rglob("*")` to find all files and then applies filters using `Path.match()`.

The filtering priority is:
1. **Discovery**: All files are found recursively.
2. **Inclusion**: If `include_patterns` is provided, only files matching at least one pattern are kept.
3. **Exclusion**: Any files matching an `exclude_patterns` are removed.

### Metadata Generator (`croissant_maker.metadata_generator`)
The `MetadataGenerator` class stores the include/exclude patterns and passes them to the discovery utility. This ensures that the generated `distribution` (FileObjects) and `recordSet` (RecordSets) only contain the filtered subset.

### CLI (`croissant_maker.__main__`)
The CLI uses `typer` to handle multi-value options for `--include` and `--exclude`. It also implements the early-exit logic for `--list-files` to provide a fast "dry-run" experience.
