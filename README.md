# Inventory Management API

A FastAPI backend for managing products, warehouses, stock levels, and inventory movements.

## Local setup

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -e ".[dev]"
copy .env.example .env
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`. Interactive documentation is available at `/docs`.

## Tests

```powershell
pytest
```
