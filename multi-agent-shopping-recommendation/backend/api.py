# backend/api.py

from fastapi import FastAPI, Request
from pydantic import BaseModel
from main_agent_executor import agent_executor

app = FastAPI()

class QueryInput(BaseModel):
    query: str

@app.post("/recommend")
async def recommend_products(input: QueryInput):
    result = agent_executor.invoke({"input": input.query})
    return {"response": result.get("output", "No response")}
