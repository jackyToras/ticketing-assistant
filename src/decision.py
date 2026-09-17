"""Grounded Gemini decision generation with strict response validation."""

from typing import Literal

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from src.config import settings
from src.retrieval import PolicyRetriever, RetrievalError
from src.schemas import TicketCreate


Action = Literal[
    "APPROVE_RETURN",
    "REQUEST_PHOTOS",
    "OPEN_SHIPPING_INVESTIGATION",
    "REPLACE_CORRECT_ITEM",
    "REPLACE_DEFECTIVE_ITEM",
    "OFFER_REFUND_OR_REPLACEMENT",
    "REJECT_STANDARD_POLICY",
    "NEEDS_MORE_INFORMATION",
]


class GeneratedDecision(BaseModel):
    action: Action
    confidence: float = Field(ge=0, le=1)
    reason: str = Field(min_length=1, max_length=1000)
    sources: list[str] = Field(min_length=1)


class DecisionServiceError(RuntimeError):
    pass


def create_decision(ticket: TicketCreate) -> GeneratedDecision:
    try:
        retriever = PolicyRetriever()
        ticket_text = ticket.model_dump_json(exclude_none=True)
        contexts = retriever.retrieve(f"Support ticket: {ticket_text}")
    except RetrievalError as exc:
        raise DecisionServiceError(str(exc)) from exc
    except Exception as exc:
        raise DecisionServiceError("Unable to retrieve policy evidence") from exc

    policy_context = "\n\n".join(
        f"SOURCE: {item['source']}\n{item['text']}" for item in contexts
    )
    prompt = f"""You are a support-ticket policy decision assistant.
Use only the policy evidence supplied below. Do not invent policy rules or facts.

If facts required by the applicable policy are missing or ambiguous, return NEEDS_MORE_INFORMATION.
If the policy says the ticket is not eligible, return REJECT_STANDARD_POLICY.
For a damaged order at or below ₹2,000, use OFFER_REFUND_OR_REPLACEMENT.
For a defective product eligible for replacement, use REPLACE_DEFECTIVE_ITEM.

Ticket JSON:
{ticket_text}

Retrieved policy evidence:
{policy_context}

Return the concise decision and cite only source filenames shown in the evidence."""

    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=GeneratedDecision,
                temperature=0,
            ),
        )
        decision = GeneratedDecision.model_validate_json(response.text)
    except Exception as exc:
        raise DecisionServiceError("Gemini could not produce a valid structured decision") from exc

    allowed_sources = {str(item["source"]) for item in contexts}
    if not set(decision.sources).issubset(allowed_sources):
        raise DecisionServiceError("Gemini returned a source outside the retrieved policy evidence")
    return decision
