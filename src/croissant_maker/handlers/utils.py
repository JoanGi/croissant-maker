"""Shared utilities for file handlers."""

import pandas as pd
import hashlib
import gzip  # Built-in: handles .gz (gzip) compression
import bz2  # Built-in: handles .bz2 (bzip2) compression
import lzma  # Built-in: handles .xz/.lzma (LZMA/xz) compression
import re
import logging
from pathlib import Path
from typing import Dict, Any, Union

# Set up logger for this module
logger = logging.getLogger(__name__)

# Compile regex patterns once for performance
_DATETIME_NAME_PATTERNS = [
    re.compile(pattern)
    for pattern in [
        r".*time$",
        r".*date$",
        r".*timestamp$",
        r"^date",
        r"^time",
        r"intime",
        r"outtime",
        r"charttime",
        r"storetime",
        r"dischtime",
        r"admittime",
        r"createtime",
        r"updatetime",
        r".*_dt$",
        r".*_ts$",
    ]
]

_DATETIME_VALUE_PATTERNS = [
    re.compile(pattern)
    for pattern in [
        r"\d{4}-\d{2}-\d{2}",  # YYYY-MM-DD
        r"\d{2}/\d{2}/\d{4}",  # MM/DD/YYYY
        r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}",  # YYYY-MM-DD HH:MM:SS
        r"\d{2}:\d{2}:\d{2}",  # HH:MM:SS
    ]
]


def infer_column_types(df: pd.DataFrame) -> Dict[str, str]:
    """
    Infer data types for DataFrame columns and map to Croissant types.

    Uses pandas dtype detection combined with content analysis for
    datetime fields that may be stored as strings.

    Args:
        df: DataFrame to analyze

    Returns:
        Dictionary mapping column names to Croissant type strings.
        Returns empty dict if DataFrame is None or empty.
    """
    if df is None or df.empty:
        logger.warning("Empty or None DataFrame provided to infer_column_types")
        return {}

    type_mapping = {}

    for column in df.columns:
        try:
            series = df[column].dropna()

            if len(series) == 0:
                type_mapping[column] = "sc:Text"
                continue

            # Check pandas dtype first
            if pd.api.types.is_integer_dtype(series):
                type_mapping[column] = "sc:Integer"
            elif pd.api.types.is_float_dtype(series):
                type_mapping[column] = "sc:Float"
            elif pd.api.types.is_bool_dtype(series):
                type_mapping[column] = "sc:Boolean"
            elif pd.api.types.is_datetime64_any_dtype(series):
                type_mapping[column] = "sc:Date"
            else:
                # Check if string column contains datetime values
                if _is_likely_datetime_column(column, series):
                    type_mapping[column] = "sc:Date"
                else:
                    type_mapping[column] = "sc:Text"
        except Exception as e:
            # Log warning but don't fail - default to Text for problematic columns
            logger.warning(f"Could not infer type for column '{column}': {e}")
            type_mapping[column] = "sc:Text"

    return type_mapping


def _is_likely_datetime_column(column_name: str, series: pd.Series) -> bool:
    """
    Determine if a column likely contains datetime data.

    Uses column name patterns and value sampling to detect datetime columns.
    """
    # Check column name patterns
    column_lower = column_name.lower()
    name_matches = any(
        pattern.match(column_lower) for pattern in _DATETIME_NAME_PATTERNS
    )

    if not name_matches:
        return False

    # Verify with sample values
    sample_values = series.head(10).astype(str)

    # Check if values match datetime patterns
    for value in sample_values:
        for dt_pattern in _DATETIME_VALUE_PATTERNS:
            if dt_pattern.search(str(value)):
                return True

    return False


def analyze_data_sample(df: pd.DataFrame, max_rows: int = 3) -> Dict[str, Any]:
    """
    Analyze a DataFrame and return useful metadata about the data.

    Args:
        df: DataFrame to analyze
        max_rows: Maximum number of sample rows to include

    Returns:
        Dictionary containing column types, sample data, and basic stats
    """
    return {
        "column_types": infer_column_types(df),
        "num_rows": len(df),
        "num_columns": len(df.columns),
        "columns": list(df.columns),
        "sample_data": df.head(max_rows).to_dict("records") if len(df) > 0 else [],
    }


def compute_file_hash(file_path: Union[str, Path]) -> str:
    """
    Compute SHA256 hash of a file for integrity verification.

    Handles regular and compressed files by reading the uncompressed
    content in chunks for memory efficiency.

    Args:
        file_path: Path to the file (str or Path object)

    Returns:
        Hexadecimal SHA256 hash string

    Raises:
        FileNotFoundError: If the file doesn't exist
        PermissionError: If the file cannot be read
    """
    # Convert to Path only if needed
    if isinstance(file_path, str):
        file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    try:
        sha256_hash = hashlib.sha256()
        name_lower = file_path.name.lower()

        if name_lower.endswith(".gz"):
            with gzip.open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
        elif name_lower.endswith(".bz2"):
            with bz2.open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
        elif name_lower.endswith(".xz"):
            with lzma.open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
        else:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)

        return sha256_hash.hexdigest()

    except (IOError, OSError) as e:
        raise PermissionError(f"Cannot read file {file_path}: {e}")


def get_clean_record_name(file_name: str) -> str:
    """
    Generate a clean record set name from a file name.

    Removes common file extensions in a generic way, not hardcoded to any format.

    Args:
        file_name: Original file name

    Returns:
        Clean name suitable for record set naming. Returns original name if
        cleaning would result in empty string.
    """
    if not file_name or not isinstance(file_name, str):
        logger.warning(f"Invalid file_name provided: {repr(file_name)}")
        return str(file_name) if file_name else "unknown"

    name = file_name.strip()

    # Remove common compression extensions first
    if name.endswith(".gz"):
        name = name[:-3]
    elif name.endswith(".bz2"):
        name = name[:-4]
    elif name.endswith(".xz"):
        name = name[:-3]
    elif name.endswith(".zip"):
        name = name[:-4]

    # Remove common data file extensions
    extensions = [".csv", ".tsv", ".json", ".parquet", ".txt", ".dat"]
    for ext in extensions:
        if name.endswith(ext):
            name = name[: -len(ext)]
            break

    # Ensure we return something valid
    return name if name else file_name
