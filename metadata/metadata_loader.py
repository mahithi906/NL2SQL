import csv
import os


def get_tables():
    """
    Load metadata.csv and return a dictionary keyed by table name.

    Structure:
    {
        "Product": {
            "name": "Product",
            "description": "...",
            "columns": [
                {
                    "name": "ProductID",
                    "description": "...",
                    "data_type": "int",
                    "sample_values": "[1,2,3]"
                },
                ...
            ]
        }
    }
    """

    base = os.path.dirname(__file__)
    path = os.path.join(base, "metadata.csv")

    tables = {}

    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                tbl = row.get("TableName")
                if not tbl:
                    continue

                # If table not already added → initialize entry
                if tbl not in tables:
                    tables[tbl] = {
                        "name": tbl,
                        "description": row.get("TableDescription", ""),
                        "columns": [],
                    }

                # Append column info
                tables[tbl]["columns"].append(
                    {
                        "name": row.get("ColumnName", ""),
                        "description": row.get(
                            "ColoumnDescription", ""
                        ),  # ✅ CSV typo preserved
                        "data_type": row.get("DataType", ""),
                        "sample_values": row.get("SampleValues", ""),
                    }
                )

    except FileNotFoundError:
        # No metadata available
        pass

    return tables
