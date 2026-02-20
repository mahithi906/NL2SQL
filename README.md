# Sample FastAPI App

This is a minimal FastAPI sample app.

Run locally:

- Create a virtual environment:

```bash
python -m venv .venv
```

- Activate (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
```

- Install dependencies:

```bash
pip install -r requirements.txt
```

- Start the server:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API endpoints:

- `GET /` — welcome message
- `GET /api/items` — list items
- `POST /api/items` — create item (JSON: `name`, optional `description`)
- `GET /api/items/{id}` — retrieve item
