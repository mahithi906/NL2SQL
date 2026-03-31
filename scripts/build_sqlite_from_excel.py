# scripts/build_sqlite_from_excel.py
import pandas as pd
import sqlite3
from pathlib import Path

EXCEL_PATH = Path(r"dataset/AdventureWorks2019Export.xls")

DB_PATH = Path("data/adventureworks.sqlite3")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def build_sqlite():
    print("Reading Excel file:", EXCEL_PATH.resolve())

    # Load all sheets in the Excel
    xls = pd.ExcelFile(EXCEL_PATH)
    # Recreate DB from scratch
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    print("Created SQLite database at:", DB_PATH.resolve())

    # Convert each sheet -> table
    for sheet_name in xls.sheet_names:
        print(f"Processing sheet: {sheet_name}")
        df = pd.read_excel(EXCEL_PATH, sheet_name=sheet_name)
        table_name = sheet_name.strip().replace(" ", "_").lower()
        print(f"Writing table '{table_name}' with {len(df)} rows")
        df.to_sql(table_name, conn, if_exists="replace", index=False)

    conn.close()
    print("\nDONE! SQLite DB created successfully.")


if __name__ == "__main__":
    build_sqlite()
