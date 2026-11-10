from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session

app = FastAPI(title="Course Mania")


@app.get("/health")
async def health(s: AsyncSession = Depends(get_session)):
    await s.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}
