from fastapi import FastAPI
from app.routes import router as api_router

app = FastAPI(title="Sample FastAPI App")
app.include_router(api_router)


@app.get("/")
def read_root():
    return {"message": "Welcome to the Sample FastAPI app"}
