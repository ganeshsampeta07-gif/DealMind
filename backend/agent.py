from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from .hindsight_service import hindsight_service
from .llm_service import llm_service
from .prompts import SYSTEM_PROMPT


def extract_customer_name(message: str) -> Optional[str]:
    match = re.search(r"\b(?:with|for|about|customer|client)\s+([A-Z][a-zA-Z'-]+)", message)
    if match:
        return match.group(1).strip()

    # Catch statements such as "Ravi is interested ..." without treating an
    # ordinary sentence opener (for example, "Prepare") as the customer.
    match = re.match(
        r"\s*([A-Z][a-zA-Z'-]+)\s+(?:is|has|prefers|wants|needs|thinks|believes|uses|likes|plans)\b",
        message,
    )
    if match:
        return match.group(1).strip()
    return None


def _memory_text(memory: Any) -> str:
    """Convert Hindsight result variants into readable memory text."""
    if isinstance(memory, str):
        return memory.strip()
    if isinstance(memory, dict):
        for key in ("content", "value", "summary", "text", "memory", "result"):
            value = memory.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
            if isinstance(value, dict):
                nested = _memory_text(value)
                if nested:
                    return nested
    return ""


def _recall_items(payload: Any) -> List[Any]:
    if isinstance(payload, dict):
        items = payload.get("results", payload.get("memories", payload.get("items", [])))
    else:
        items = payload
    if items is None:
        return []
    if isinstance(items, list):
        return items
    return [items]


def _fact_category(value: str, proposed: str = "") -> str:
    category = proposed.lower().strip().replace(" ", "_")
    allowed = {
        "preference", "pricing_concern", "objection", "competitor", "interest",
        "buying_intent", "decision_criteria", "requirement", "follow_up",
    }
    if category in allowed:
        return category

    text = value.lower()
    if any(term in text for term in ("prefer", "likes", "likes to", "would rather")):
        return "preference"
    if any(term in text for term in ("expensive", "price", "pricing", "cost", "budget")):
        return "pricing_concern"
    if any(term in text for term in ("competitor", "comparing", "compare", "zoho", "salesforce")):
        return "competitor"
    if any(term in text for term in ("interested", "interest", "likes our", "wants our")):
        return "interest"
    if any(term in text for term in ("buy", "purchase", "ready to", "plans to")):
        return "buying_intent"
    if any(term in text for term in ("follow up", "follow-up", "call back", "next meeting")):
        return "follow_up"
    return "requirement"


def _fallback_facts(message: str, customer: str) -> List[Dict[str, str]]:
    """Conservatively capture explicit durable facts if extraction JSON is invalid."""
    candidates = re.split(r"[.!?;]+|,\s*(?:and\s+)?|\s+and\s+", message)
    durable_cues = (
        "prefer", "interested", "expensive", "price", "pricing", "cost", "budget",
        "compar", "competitor", "need", "require", "want", "buy", "purchase", "follow up",
    )
    facts: List[Dict[str, str]] = []
    for candidate in candidates:
        clause = candidate.strip().strip(",")
        if not clause or not any(cue in clause.lower() for cue in durable_cues):
            continue
        clause = re.sub(r"^(?:he|she|they|it)\s+", "", clause, flags=re.IGNORECASE)
        if clause[:1].islower() or re.match(r"^(?:prefers|needs|wants|likes|is|has|plans)\b", clause, re.I):
            clause = f"{customer} {clause}"
        elif re.match(r"^(?:thinks|believes)\b", clause, re.I):
            clause = f"{customer} {clause}"
        if customer.lower() not in clause.lower() and clause[:1].isupper():
            # Resolve a leading first-person subject only when the clause itself
            # makes a durable customer claim.
            clause = f"{customer} {clause[0].lower()}{clause[1:]}"
        facts.append({"type": _fact_category(clause), "value": clause.strip()})
    return facts


def _parse_extracted_facts(raw: str, message: str, customer: str) -> List[Dict[str, str]]:
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)
    try:
        data = json.loads(cleaned)
    except (TypeError, json.JSONDecodeError):
        data = None

    extracted = data.get("facts", []) if isinstance(data, dict) else []
    facts: List[Dict[str, str]] = []
    if isinstance(extracted, list):
        for item in extracted:
            if isinstance(item, str):
                value, category = item.strip(), ""
            elif isinstance(item, dict):
                value = str(item.get("value", item.get("fact", ""))).strip()
                category = str(item.get("type", item.get("category", "")))
            else:
                continue
            if value and len(value) <= 500:
                facts.append({"type": _fact_category(value, category), "value": value})

    return facts or _fallback_facts(message, customer)


class DealMindAgent:
    """Coordinates customer-memory recall, personalized generation, and retention."""

    def __init__(self, memory_service=None, language_model=None):
        self.memory_service = memory_service or hindsight_service
        self.language_model = language_model or llm_service

    def process_message(self, message: str, customer_name: Optional[str] = None) -> Dict[str, Any]:
        message = message.strip()
        if not message:
            raise ValueError("Message cannot be empty.")

        customer = customer_name or extract_customer_name(message) or "unknown"
        recall_query = f"Customer: {customer}. Relevant information for this request: {message}"
        recalled_items = _recall_items(
            self.memory_service.recall_memory(customer=customer, query=recall_query, limit=10)
        )
        memories = [text for text in (_memory_text(item) for item in recalled_items) if text]
        memory_context = "\n".join(f"- {item}" for item in memories) or "No relevant memories found."

        user_prompt = (
            "CURRENT USER REQUEST\n"
            f"{message}\n\n"
            "RECALLED HINDSIGHT MEMORIES\n"
            f"{memory_context}\n\n"
            "Use the recalled memories to personalize practical sales guidance for the current request. "
            "Clearly distinguish remembered facts from suggestions, and do not invent customer facts."
        )
        response = self.language_model.generate_response(SYSTEM_PROMPT, user_prompt)

        extraction_prompt = (
            "Extract only explicit, useful, durable customer facts from CURRENT USER MESSAGE below. "
            "Include preferences, pricing concerns or objections, competitors, product interest, buying intent, "
            "decision criteria, requirements, and concrete follow-up details. Do not include requests, temporary "
            "details, advice, or inferred facts. Resolve pronouns to the customer name when clear. "
            'Return only valid JSON in this schema: {"facts":[{"type":"preference|pricing_concern|objection|'
            'competitor|interest|buying_intent|decision_criteria|requirement|follow_up","value":"fact sentence"}]}. '
            "Use an empty facts array if there are no such facts.\n\n"
            f"CUSTOMER: {customer}\nCURRENT USER MESSAGE: {message}"
        )
        extracted = self.language_model.generate_response(
            "You extract factual customer memory candidates. Return only the requested JSON.",
            extraction_prompt,
        )
        facts = _parse_extracted_facts(extracted or "", message, customer)

        stored_facts: List[str] = []
        if customer != "unknown":
            for fact in facts:
                self.memory_service.retain_memory(
                    customer=customer,
                    memory_type=fact["type"],
                    value=fact["value"],
                    source="dealmind_conversation",
                    context=f"Conversation message: {message}",
                    metadata={"customer": customer, "source": "dealmind_agent"},
                )
                stored_facts.append(fact["value"])

        return {
            "response": response,
            "memories_used": memories,
            "memory_count": len(memories),
            "customer": customer,
            "stored_facts": stored_facts,
        }


agent = DealMindAgent()


def process_chat(message: str, customer_name: Optional[str] = None) -> Dict[str, Any]:
    return agent.process_message(message, customer_name)


def get_customer_memories(customer_name: str):
    return {"customer": customer_name, "memories": []}


def get_customer_timeline(customer_name: str):
    return {"customer": customer_name, "timeline": []}
