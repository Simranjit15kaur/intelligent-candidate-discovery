from fastapi import FastAPI
from app.db.session import create_db_and_tables
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(
    title = "Intelligent Candidate Discovery",
    version = "0.1.0",
    lifespan = lifespan
) 

@app.get("/health")
def health():
    return {"status" : "ok"}
