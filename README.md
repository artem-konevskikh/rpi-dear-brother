# Python code for Dear Brother project by Maria Fedorova

## Installation

```bash
# Create and activate a virtual environment with uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package in development mode
uv pip install -e .
```

## Example Usage

```bash
# Run with default settings
emotion-lighting

# Run with custom settings
emotion-lighting --led-count 60 --camera 1 --db custom_database.db
```