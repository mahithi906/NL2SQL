from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd

app = FastAPI()


class QueryRequest(BaseModel):
    query: str


@app.post("/nl2sql")
def nl2sql(req: QueryRequest):
    # TODO: Run your NL→SQL model here
    sql = "SELECT * FROM customers LIMIT 5"

    # TODO: Execute SQL on DB
    df = pd.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]})

    return {"sql": sql, "rows": df.to_dict(orient="records")}
