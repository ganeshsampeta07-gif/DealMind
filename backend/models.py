from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    customer_name: Optional[str] = None


class APIChatResponse(BaseModel):
    response: str
    memories: List[str] = Field(default_factory=list)


class MemoryRecord(BaseModel):
    customer: str
    type: str
    value: str
    source: Optional[str] = None
    context: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    response: str
    memories_used: List[str] = Field(default_factory=list)
    memory_count: int = 0
    customer: Optional[str] = None


class CustomerMemoryResponse(BaseModel):
    customer: str
    memories: List[Dict[str, Any]] = Field(default_factory=list)


class CustomerTimelineResponse(BaseModel):
    customer: str
    timeline: List[Dict[str, Any]] = Field(default_factory=list)


class MemoryEntry(BaseModel):
    id: Optional[str] = None
    customer: str
    category: str
    content: str
    source: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
