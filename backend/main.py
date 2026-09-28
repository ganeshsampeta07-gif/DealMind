from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .agent import agent, process_chat, get_customer_memories, get_customer_timeline
from .config import FRONTEND_URL
from .models import APIChatResponse, ChatRequest, ChatResponse

app = FastAPI(title="DealMind API", version="1.0.0")

allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
if FRONTEND_URL:
    allowed_origins.append(FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "DealMind API is running."}


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "DealMind"}


@app.post("/chat", response_model=APIChatResponse)
def chat_api_endpoint(payload: ChatRequest):
    try:
        result = agent.process_message(payload.message, payload.customer_name)
        return APIChatResponse(
            response=result["response"],
            memories=result.get("memories_used", []),
        )
    except Exception as exc:  # pragma: no cover - safety net
        raise HTTPException(
            status_code=500,
            detail="The DealMind service is temporarily unavailable.",
        ) from exc


@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(payload: ChatRequest):
    try:
        result = process_chat(payload.message, payload.customer_name)
        return ChatResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - safety net
        raise HTTPException(status_code=500, detail="The AI service is temporarily unavailable.") from exc


@app.post("/api/memory")
def create_memory_endpoint(payload: dict):
    return {"status": "accepted", "message": "Memory ingestion endpoint ready."}


@app.get("/api/customer/{customer_name}/memories")
def customer_memories(customer_name: str):
    return get_customer_memories(customer_name)


@app.get("/api/customer/{customer_name}/timeline")
def customer_timeline(customer_name: str):
    return get_customer_timeline(customer_name)


@app.post("/api/customer")
def create_customer(payload: dict):
    return {"status": "created", "customer": payload.get("name", "unknown")}
