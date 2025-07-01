"""Tests for Croissant Maker CLI."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from croissant_maker.__main__ import app

runner = CliRunner()


@pytest.fixture
def csv_dataset(tmp_path: Path) -> Path:
    """Create a CSV dataset for testing."""
    dataset_dir = tmp_path / "test_dataset"
    dataset_dir.mkdir()
    csv_content = "id,name,age\n1,Alice,25\n2,Bob,30"
    (dataset_dir / "data.csv").write_text(csv_content)
    return dataset_dir


def test_basic_generation(csv_dataset: Path, tmp_path: Path) -> None:
    """Test basic metadata generation with defaults."""
    output = tmp_path / "output.jsonld"

    result = runner.invoke(
        app, ["--input", str(csv_dataset), "--output", str(output), "--no-validate"]
    )

    assert result.exit_code == 0

    with open(output) as f:
        metadata = json.load(f)

    assert metadata["name"] == "test_dataset"
    assert "Dataset containing" in metadata["description"]


def test_comprehensive_overrides(csv_dataset: Path) -> None:
    """Test comprehensive metadata overrides with multiple creators."""
    output_dir = Path("tests/output")
    output_dir.mkdir(exist_ok=True)
    output = output_dir / "example-with-overrides.jsonld"

    result = runner.invoke(
        app,
        [
            "--input",
            str(csv_dataset),
            "--output",
            str(output),
            "--name",
            "Machine Learning Dataset",
            "--description",
            "Example dataset with comprehensive metadata",
            "--url",
            "https://example.com/dataset",
            "--license",
            "MIT",
            "--dataset-version",
            "2.1.0",
            "--creator",
            "John Doe,john@example.com,https://johndoe.com",
            "--creator",
            "Jane Smith,jane@example.com",  # No URL
            "--creator",
            "Bob Wilson,,https://bob.com",  # No email
            "--creator",
            "Alice Johnson",  # Name only
            "--citation",
            "Doe et al. (2024). Machine Learning Dataset v2.1.",
            "--no-validate",
        ],
    )

    assert result.exit_code == 0

    with open(output) as f:
        metadata = json.load(f)

    # Check overridden fields
    assert metadata["name"] == "Machine Learning Dataset"
    assert metadata["description"] == "Example dataset with comprehensive metadata"
    assert metadata["url"] == "https://example.com/dataset"
    assert metadata["license"] == "https://opensource.org/licenses/MIT"
    assert metadata["version"] == "2.1.0"
    assert metadata["citeAs"] == "Doe et al. (2024). Machine Learning Dataset v2.1."

    # Check creators with different info levels
    creators = metadata["creator"]
    assert len(creators) == 4
    assert creators[0]["name"] == "John Doe"
    assert creators[0]["email"] == "john@example.com"
    assert creators[0]["url"] == "https://johndoe.com"
    assert creators[1]["name"] == "Jane Smith"
    assert creators[1]["email"] == "jane@example.com"
    assert "url" not in creators[1]
    assert creators[2]["name"] == "Bob Wilson"
    assert "email" not in creators[2]
    assert creators[2]["url"] == "https://bob.com"
    assert creators[3]["name"] == "Alice Johnson"
    assert "email" not in creators[3]
    assert "url" not in creators[3]


def test_error_handling() -> None:
    """Test error handling for invalid inputs."""
    # Invalid directory
    result = runner.invoke(app, ["--input", "/nonexistent", "--no-validate"])
    assert result.exit_code == 1
    assert "Error:" in result.stdout


def test_help_and_version() -> None:
    """Test help and version commands."""
    # Help
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "--creator" in result.stdout

    # Version
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "croissant-maker" in result.stdout

    # Usage when no args
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "Usage:" in result.stdout
