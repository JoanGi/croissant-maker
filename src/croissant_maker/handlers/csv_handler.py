"""CSV file handler for tabular data processing."""

from pathlib import Path
import pandas as pd

from croissant_maker.handlers.base_handler import FileTypeHandler
from croissant_maker.handlers.utils import analyze_data_sample, compute_file_hash


class CSVHandler(FileTypeHandler):
    """
    Handler for CSV and compressed CSV files with automatic type inference.

    Supports:
    - Standard CSV files (.csv)
    - Gzip-compressed CSV files (.csv.gz)
    - Bzip2-compressed CSV files (.csv.bz2)
    - XZ-compressed CSV files (.csv.xz)
    - Automatic column type detection using pandas
    - SHA256 hash computation for file integrity
    - Sample data extraction for preview
    """

    def can_handle(self, file_path: Path) -> bool:
        """
        Check if the file is a CSV or compressed CSV file.

        Args:
            file_path: Path to check

        Returns:
            True if file has supported CSV extension
        """
        name_lower = file_path.name.lower()
        return (
            file_path.suffix.lower() == ".csv"
            or name_lower.endswith(".csv.gz")
            or name_lower.endswith(".csv.bz2")
            or name_lower.endswith(".csv.xz")
        )

    def extract_metadata(self, file_path: Path) -> dict:
        """
        Extract comprehensive metadata from a CSV file.

        Reads a sample of the CSV file to infer column types, extracts
        file statistics, computes integrity hashes, and prepares all
        metadata needed for Croissant generation.

        Args:
            file_path: Path to the CSV file

        Returns:
            Dictionary containing:
            - Basic file info (path, name, size, hash)
            - Format information (encoding, compression)
            - Data structure (columns, types, row count)
            - Sample data for preview

        Raises:
            ValueError: If the CSV file cannot be read or processed
            FileNotFoundError: If the file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        try:
            # Read a sample for type inference (1000 rows for good accuracy)
            df = pd.read_csv(file_path, nrows=1000)

            if df.empty:
                raise ValueError(f"CSV file is empty: {file_path}")

            # Extract file properties
            file_size = file_path.stat().st_size
            sha256_hash = compute_file_hash(file_path)

            # Analyze the data structure and types
            data_analysis = analyze_data_sample(df)

            # Determine encoding format based on file extension
            name_lower = file_path.name.lower()
            if name_lower.endswith(".csv.gz"):
                encoding_format = "application/gzip"
            elif name_lower.endswith(".csv.bz2"):
                encoding_format = "application/x-bzip2"
            elif name_lower.endswith(".csv.xz"):
                encoding_format = "application/x-xz"
            else:
                encoding_format = "text/csv"

            return {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "file_size": file_size,
                "sha256": sha256_hash,
                "encoding_format": encoding_format,
                **data_analysis,  # Includes column_types, num_rows, columns, sample_data
            }

        except pd.errors.EmptyDataError:
            raise ValueError(f"CSV file contains no data: {file_path}")
        except pd.errors.ParserError as e:
            raise ValueError(f"Failed to parse CSV file {file_path}: {e}")
        except UnicodeDecodeError as e:
            raise ValueError(f"Encoding error in CSV file {file_path}: {e}")
        except Exception as e:
            raise ValueError(f"Failed to process CSV file {file_path}: {e}")
