# Local Bootstrap

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Run checks:

```bash
ruff format .
ruff check .
pytest -q
```

Run UI:

```bash
python -m app.ui.gradio_app
```
