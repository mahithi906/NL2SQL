import os
from sqlalchemy import create_engine, text

# Load the DB path
os.environ.setdefault("DATABASE_URL", "sqlite:///data/adventureworks.sqlite3")

engine = create_engine(os.environ["DATABASE_URL"])

with engine.connect() as conn:
    tables = conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    ).fetchall()
    print("Tables found:", [t[0] for t in tables])

    for t in [t[0] for t in tables]:
        print(f"\nPreview of table: {t}")
        rows = conn.execute(text(f"SELECT * FROM {t} LIMIT 5;")).fetchall()
        print(rows)
