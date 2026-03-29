"""File discovery utilities for Croissant Maker."""

from pathlib import Path
from typing import List, Optional


def discover_files(
    dir_path: str,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
) -> List[Path]:
    """
    Recursively discover all files in a directory and return their relative paths.

    Args:
        dir_path: Path to the directory to scan.
        include_patterns: Optional list of glob patterns to include.
        exclude_patterns: Optional list of glob patterns to exclude.

    Returns:
        List of relative file paths found in the directory.

    Raises:
        FileNotFoundError: If the directory does not exist or is not a directory.
        PermissionError: If the directory cannot be accessed.
    """
    try:
        directory = Path(dir_path).resolve()
        if not directory.is_dir():
            raise FileNotFoundError(f"{dir_path} is not a directory")

        files = [
            file.relative_to(directory)
            for file in directory.rglob("*")
            if file.is_file()
        ]

        if include_patterns:
            files = [f for f in files if any(f.match(p) for p in include_patterns)]

        if exclude_patterns:
            files = [f for f in files if not any(f.match(p) for p in exclude_patterns)]

        return files
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Directory not found: {e}")
    except PermissionError as e:
        raise PermissionError(f"Permission denied: {e}")
