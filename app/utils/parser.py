from typing import TypedDict

from app.schemas.events import UsageEvent


class FaqEventData(TypedDict):
    user_question: str
    document_content: str


def get_faq_event_data(event: UsageEvent) -> FaqEventData | None:
    """
    Safely extracts user question and document content from an FAQ event.
    Returns a FaqEventData TypedDict if valid, otherwise None.
    """
    if event.event_type != "faq":
        return None

    payload = event.payload
    if not isinstance(payload, dict):
        return None

    target_user_message = payload.get("targetUserMessage")
    if not isinstance(target_user_message, dict):
        return None

    user_question = target_user_message.get("content")
    if not isinstance(user_question, str):
        return None

    document_content = payload.get("content")
    if not isinstance(document_content, str):
        return None

    return FaqEventData(user_question=user_question, document_content=document_content)
