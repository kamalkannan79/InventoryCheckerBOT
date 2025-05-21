from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from helper import interpret_question
from app import run_query_from_intent
import json

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryInput(BaseModel):
    question: str

@app.post("/chat")
async def chat_endpoint(data: QueryInput):
    try:
        intent_str = interpret_question(data.question)
        intent = json.loads(intent_str)
        response = run_query_from_intent(intent)
        return {"response": response}
    except Exception as e:
        return {"error": str(e)}
