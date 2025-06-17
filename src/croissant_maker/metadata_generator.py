"""Croissant metadata generator for datasets."""

import json
import tempfile
from pathlib import Path
from datetime import datetime
import mlcroissant as mlc

from croissant_maker.files import discover_files
from croissant_maker.handlers.registry import find_handler, register_all_handlers
from croissant_maker.handlers.utils import get_clean_record_name

# Register all handlers
register_all_handlers()


def serialize_datetime(obj):
    """Convert datetime objects to ISO format strings for JSON serialization."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class MetadataGenerator:
    """
    Generates Croissant metadata for datasets with automatic type inference.

    This class discovers files in a dataset directory, processes them using
    registered file handlers, and generates rich Croissant JSON-LD metadata
    that describes the dataset structure and types.
    """

    def __init__(self, dataset_path: str):
        """
        Initialize the metadata generator for a dataset.

        Args:
            dataset_path: Path to the directory containing dataset files

        Raises:
            ValueError: If the dataset path is not a directory
        """
        self.dataset_path = Path(dataset_path).resolve()
        if not self.dataset_path.is_dir():
            raise ValueError(f"Dataset path {dataset_path} is not a directory")

    def generate_metadata(self) -> dict:
        """
        Generate complete Croissant metadata for the dataset.

        Discovers all files in the dataset, processes them with appropriate
        handlers, and creates a comprehensive metadata structure following
        the Croissant specification.

        Returns:
            Dictionary containing the generated Croissant metadata

        Raises:
            ValueError: If no supported files are found in the dataset
        """
        # Discover and process files
        files = discover_files(str(self.dataset_path))
        file_metadata = []

        for file_path in files:
            full_path = self.dataset_path / file_path
            handler = find_handler(full_path)
            if handler:
                try:
                    metadata = handler.extract_metadata(full_path)
                    metadata["relative_path"] = str(file_path)
                    file_metadata.append(metadata)
                except Exception as e:
                    print(f"Warning: Failed to process {file_path}: {e}")

        if not file_metadata:
            raise ValueError("No supported files found in the dataset")

        # Create Croissant metadata structure
        dataset_name = self.dataset_path.name

        # TODO: Improve metadata extraction:
        # - Parse README, CITATION, LICENSE, and other metadata files for description, creators, license, citation, and URLs
        # - Allow user to override or provide these via CLI/arguments (e.g., url, creators, citeAs, keywords, version, date_published)
        # - Add support for extracting and including keywords for discoverability
        metadata = mlc.Metadata(
            name=dataset_name,
            description=f"Dataset containing {len(file_metadata)} files with automatically inferred types",
            url=f"file://{self.dataset_path}",
            license=["https://creativecommons.org/licenses/by/4.0/"],
            creators=[
                mlc.Person(name="Dataset Generator", email="generated@example.com")
            ],
            date_published=datetime.now(),
            version="1.0.0",
            cite_as=f"Generated Dataset. (2024). {dataset_name} Dataset. Created with automated type inference.",
        )

        file_objects = []
        record_sets = []

        for i, file_meta in enumerate(file_metadata):
            file_id = f"file_{i}"

            # Create FileObject for each file
            # What this section does well:
            # - Correctly creates a cr:FileObject for each discovered file.
            # - Uses relative contentUrl, which is best practice.
            # - Calculates sha256 checksum for reproducibility.
            # - Populates name, encoding_formats, and content_size.
            file_obj = mlc.FileObject(
                id=file_id,
                name=file_meta["file_name"],
                content_url=file_meta["relative_path"],
                encoding_formats=[file_meta["encoding_format"]],
                content_size=str(file_meta["file_size"]),
                sha256=file_meta["sha256"],
            )
            file_objects.append(file_obj)

            # Create RecordSet and Fields for files with structured data that have column types
            # What this section does well:
            # - Creates a cr:RecordSet for each file with structured data.
            # - Automatically infers data types for columns (sc:Text, sc:Integer, etc.).
            # - Correctly sets up the source with fileObject and column extraction.
            # - Generates unique and descriptive IDs for fields and record sets.
            #
            # TODO: Add support for more advanced Croissant features.
            # - references: Detect and add `references` for foreign key relationships
            #   (e.g., subject_id, hadm_id). This is high-impact.
            # - enumerations: For categorical columns, generate sc:Enumeration RecordSets.
            if "column_types" in file_meta:
                fields = []
                for col_name, col_type in file_meta["column_types"].items():
                    field = mlc.Field(
                        id=f"{file_id}_{col_name}",
                        name=col_name,
                        description=f"Column '{col_name}' from {file_meta['file_name']}",
                        data_types=[col_type],
                        source=mlc.Source(
                            id=f"{file_id}_source_{col_name}",
                            file_object=file_id,
                            extract=mlc.Extract(column=col_name),
                        ),
                    )
                    fields.append(field)

                record_set = mlc.RecordSet(
                    id=f"recordset_{i}",
                    name=get_clean_record_name(file_meta["file_name"]),
                    description=f"Records from {file_meta['file_name']} ({file_meta.get('num_rows', 'unknown')} rows)",
                    fields=fields,
                )
                record_sets.append(record_set)

        metadata.distribution = file_objects
        metadata.record_sets = record_sets

        return metadata.to_json()

    def save_metadata(self, output_path: str, validate: bool = True) -> None:
        """
        Generate and save Croissant metadata to a file.

        Args:
            output_path: Path where the metadata file should be saved
            validate: Whether to validate the metadata before saving

        Raises:
            ValueError: If validation fails or file cannot be saved
        """
        metadata_dict = self.generate_metadata()
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        if validate:
            # Validate using temporary file before saving to final location
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".jsonld", delete=False
            ) as tmp_file:
                json.dump(
                    metadata_dict,
                    tmp_file,
                    indent=2,
                    ensure_ascii=False,
                    default=serialize_datetime,
                )
                tmp_path = tmp_file.name

            try:
                # Validate by attempting to load with mlcroissant
                mlc.Dataset(tmp_path)
                self._save_to_file(metadata_dict, output_file)
            except Exception as e:
                raise ValueError(f"Validation failed: {e}")
            finally:
                # Clean up the temporary file
                Path(tmp_path).unlink(missing_ok=True)
        else:
            self._save_to_file(metadata_dict, output_file)

    def _save_to_file(self, metadata_dict: dict, output_file: Path) -> None:
        """
        Save metadata dictionary to a JSON-LD file.

        Args:
            metadata_dict: The metadata to save
            output_file: Path where the file should be saved
        """
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(
                metadata_dict,
                f,
                indent=2,
                ensure_ascii=False,
                default=serialize_datetime,
            )
