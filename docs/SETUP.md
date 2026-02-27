# Local Bootstrap

The easiest way to set up the environment and install dependencies is to use the bootstrap script:

```bash
./scripts/bootstrap.sh
```

## Configuration

Before starting the UI, ensure your `.env` file contains the required provider keys (Mistral is strictly required for OCR):

```env
MISTRAL_API_KEY=your_mistral_key
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
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
