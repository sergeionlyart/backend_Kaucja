# Local Bootstrap

The easiest way to set up the environment and install dependencies is to use the bootstrap script:

```bash
./scripts/bootstrap.sh
```

## Running the UI

Start the Gradio application using the startup wrapper (which automatically activates the `.venv` and handles port selection):

```bash
./scripts/start.sh
```

## Running Smoke Diagnostics

To verify your API keys and provider connectivity without starting the full UI:

```bash
./scripts/smoke.sh
```

## Quality Gates and Local Checks

Run checks before committing:

```bash
source .venv/bin/activate
ruff format .
ruff check .
pytest -q
```
