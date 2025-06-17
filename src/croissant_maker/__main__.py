"""Command-line interface for Croissant Maker."""

import typer
from pathlib import Path
import importlib.metadata
from rich.progress import Progress, SpinnerColumn, TextColumn

from croissant_maker.metadata_generator import MetadataGenerator

# Create the Typer application instance
app = typer.Typer(
    name="croissant-maker",
    help="🥐 Generate Croissant metadata for datasets with automatic type inference",
    add_completion=False,
    rich_markup_mode="markdown",
)


def _get_version() -> str:
    """Get version from package metadata."""
    try:
        return importlib.metadata.version("croissant-maker")
    except importlib.metadata.PackageNotFoundError:
        return "unknown (not installed as package)"


def _get_default_output_name(input_path: str) -> str:
    """Generate default output filename based on input path."""
    dataset_name = Path(input_path).name
    return f"{dataset_name}-croissant.jsonld"


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    input: str = typer.Option(
        None, "--input", "-i", help="Directory containing dataset files"
    ),
    output: str = typer.Option(None, "--output", "-o", help="Output file path"),
    validate: bool = typer.Option(
        True, "--validate/--no-validate", help="Validate metadata before saving"
    ),
    version: bool = typer.Option(False, "--version", help="Show version and exit"),
) -> None:
    """🥐 **Croissant Maker** - Generate rich metadata for your datasets"""

    if version:
        typer.echo(f"🥐 croissant-maker {_get_version()}")
        return

    if ctx.invoked_subcommand is not None:
        return

    if not input:
        typer.echo("croissant-maker: try 'croissant-maker --help' for more information")
        typer.echo("")
        typer.echo("Usage: croissant-maker --input <dataset-path> [--output <file>]")
        typer.echo("       croissant-maker validate <file>")
        typer.echo("       croissant-maker --version")
        typer.echo("       croissant-maker --help")
        return

    if not output:
        output = _get_default_output_name(input)
        typer.echo(f"📝 Auto-generated output filename: **{output}**")

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
        ) as progress:
            # Initialize generator
            metadata_progress = progress.add_task("🔍 Analyzing dataset...", total=None)
            generator = MetadataGenerator(input)

            # Generate metadata
            progress.update(metadata_progress, description="⚡ Generating metadata...")
            metadata_dict = generator.generate_metadata()

            # Save and optionally validate
            output_file = Path(output)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            if validate:
                progress.update(
                    metadata_progress, description="✅ Validating and saving..."
                )
                generator.save_metadata(output, validate=True)
                progress.update(
                    metadata_progress, description="✅ Validation completed!"
                )
            else:
                progress.update(metadata_progress, description="💾 Saving metadata...")
                generator.save_metadata(output, validate=False)
                progress.update(metadata_progress, description="💾 Save completed!")

        # Show results
        file_count = len(metadata_dict.get("distribution", []))
        record_count = len(metadata_dict.get("recordSet", []))

        typer.echo(
            f"🎉 **Success!** Generated {'validated ' if validate else ''}Croissant metadata"
        )
        typer.echo(f"📁 Files: **{file_count}**")
        typer.echo(f"📋 Record sets: **{record_count}**")
        typer.echo(f"📄 Saved to: **{output}**")

        if not validate:
            typer.echo(
                f"💡 **Tip:** Run `croissant-maker validate {output}` to validate later"
            )

    except ValueError as e:
        typer.echo(f"❌ **Error:** {e}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"❌ **Unexpected error:** {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def validate(
    file_path: str = typer.Argument(..., help="Path to Croissant metadata file"),
) -> None:
    """**Validate** a Croissant metadata file"""
    try:
        import mlcroissant as mlc

        typer.echo(f"🔍 Validating: **{file_path}**")

        dataset = mlc.Dataset(file_path)

        typer.echo("✅ **Valid!** Croissant file passed validation")
        typer.echo(f"📊 Dataset: **{dataset.metadata.name}**")
        typer.echo(f"📝 Description: {dataset.metadata.description}")

        if hasattr(dataset.metadata, "distribution"):
            file_count = (
                len(dataset.metadata.distribution)
                if dataset.metadata.distribution
                else 0
            )
            typer.echo(f"📁 Files: **{file_count}**")

        if hasattr(dataset.metadata, "record_sets"):
            record_count = (
                len(dataset.metadata.record_sets) if dataset.metadata.record_sets else 0
            )
            typer.echo(f"📋 Record sets: **{record_count}**")

    except ImportError:
        typer.echo("❌ **Error:** mlcroissant is required for validation", err=True)
        typer.echo("💡 **Fix:** pip install mlcroissant", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"❌ **Validation failed:** {e}", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
