# Contributing to urlfinderlib

This guide covers how to set up your development environment and contribute to urlfinderlib.

## Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- `libmagic` system library

### Installing uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew
brew install uv

# Or with pip
pip install uv
```

### Installing libmagic

The `python-magic` dependency requires the `libmagic` system library:

```bash
# macOS
brew install libmagic

# Ubuntu/Debian
sudo apt-get install libmagic1

# Fedora
sudo dnf install file-libs
```

## Project Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/ace-ecosystem/urlfinderlib.git
   cd urlfinderlib
   ```

2. Install dependencies:
   ```bash
   uv sync --dev
   ```

   This creates a virtual environment in `.venv/` and installs all dependencies.

3. Activate the virtual environment (optional - `uv run` handles this automatically):
   ```bash
   source .venv/bin/activate
   ```

## Running Tests

Run the full test suite with coverage:

```bash
uv run pytest
```

Run specific tests:

```bash
# Run a specific test file
uv run pytest tests/test_url.py

# Run a specific test
uv run pytest tests/test_url.py::test_is_url

# Run with verbose output
uv run pytest -vv
```

The project requires 100% test coverage. Coverage reports are displayed after each test run.

## Code Formatting

The project uses [Black](https://black.readthedocs.io/) for code formatting with a line length of 120 characters.

```bash
# Format all Python files
uv run black .

# Check formatting without making changes
uv run black --check .
```

## Building the Package

Build source distribution and wheel:

```bash
uv build
```

This creates distribution files in the `dist/` directory.

## Using the CLI

The `urlfinder` command-line tool finds URLs in files:

```bash
# Run via uv
uv run urlfinder /path/to/file

# Or after activating the virtual environment
urlfinder /path/to/file
```

## Project Structure

```
urlfinderlib/
├── urlfinderlib/           # Main package
│   ├── __init__.py
│   ├── __main__.py         # CLI entry point
│   ├── urlfinderlib.py     # Core URL finding logic
│   ├── url.py              # URL class
│   ├── helpers.py          # Helper functions
│   ├── finders/            # Content-type specific finders
│   │   ├── csv.py
│   │   ├── data.py
│   │   ├── html.py
│   │   ├── ical.py
│   │   ├── pdf.py
│   │   ├── text.py
│   │   └── xml.py
│   └── tokenizer/          # Text tokenization
├── tests/                  # Test suite
├── .github/workflows/      # CI/CD pipelines
├── pyproject.toml          # Project configuration
└── uv.lock                 # Dependency lockfile
```

## Dependency Management

Add a new runtime dependency:

```bash
uv add package-name
```

Add a new development dependency:

```bash
uv add --dev package-name
```

Update dependencies:

```bash
uv lock --upgrade
uv sync --dev
```

## Continuous Integration

The project uses GitHub Actions for CI/CD:

- **Build and Test** (`main.yml`): Runs on pull requests, tests against Python 3.10-3.13
- **Publish to PyPI** (`pypi.yml`): Triggers on version tags (`v*`)

## Releasing

1. Update the version in `pyproject.toml`
2. Commit and push changes
3. Create and push a version tag:
   ```bash
   git tag v0.18.7
   git push origin v0.18.7
   ```

The GitHub Action will automatically build and publish to PyPI.
