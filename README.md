# Croissant Maker

A tool to automatically generate [Croissant](https://mlcommons.org/en/news/croissant-format-for-ml-datasets/) metadata for datasets, starting with those hosted on [PhysioNet](https://physionet.org/).

*Status: Alpha - Initial Setup*

## Installation (Development)

It is highly recommended to use a virtual environment to manage dependencies.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/MIT-LCP/croissant-maker.git
    cd croissant-maker
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # Create a venv
    python3 -m venv .venv

    # Activate the venv
    source .venv/bin/activate
    ```

3.  **Install dependencies:** (Make sure the venv is active)
    ```bash
    pip install -e '.[test]'
    ```
    This installs the package in editable mode along with testing requirements *inside* your virtual environment.

## Usage

After installation, you can use the `croissant-maker` CLI:

```bash
croissant-maker --help
```

### Generate Croissant Metadata

```bash
croissant-maker --input /path/to/dataset --output my-metadata.jsonld
```
- `--input` (`-i`): Path to the dataset directory
- `--output` (`-o`): Output file for the Croissant metadata (default: <dataset-name>-croissant.jsonld)
- Validation is performed by default

### Validate a Croissant Metadata File

Validation checks that the file can be loaded by `mlcroissant` and conforms to the basic structure of the specification.

```bash
croissant-maker validate my-metadata.jsonld
```


## Pre-Commit Hooks & Code Quality

This project uses `pre-commit` with [Ruff](https://docs.astral.sh/ruff/) to automatically lint and format Python code, ensuring PEP 8 compliance and consistency before commits are made. Basic configuration file checks are also included.

**Setup (run once after cloning and installing dev dependencies):**
```bash
# (Ensure dev dependencies are installed: pip install -e '.[dev]')
pre-commit install
```
