from typing import TypedDict

from app.data.connection import Database
from app.extractors.core import (
    DiscordMessage,
    extract_answer_from_llm,
    identify_relevant_message_with_llm,
)
from app.schemas.events import UsageEvent


class FaqContextExtractionData(TypedDict):
    event_type: str
    event_id: str
    identified_question: str
    document_content: str


async def prepare_context_faq_data(
    event: UsageEvent,
) -> FaqContextExtractionData | None:
    """
    Identifies the question from event.payload.context and returns
    the necessary data for background extraction.
    This function must be async because it calls an LLM.
    """
    if not isinstance(event.payload, dict):
        return None

    document_content = event.payload.get("content")
    if not isinstance(document_content, str) or not document_content:
        return None

    message_context_list = event.payload.get("context")
    if not isinstance(message_context_list, list):
        return None

    valid_messages: list[DiscordMessage] = []
    for msg in message_context_list:
        if (
            isinstance(msg, dict)
            and isinstance(msg.get("content"), str)
            and msg.get("content")
            and isinstance(
                msg.get("authorId"),
                str | type(None),
            )
            and isinstance(msg.get("messageId"), str | type(None))
            and isinstance(msg.get("timestamp"), str | type(None))
        ):
            valid_messages.append(  # noqa: PERF401
                DiscordMessage(
                    authorId=msg.get("authorId", ""),
                    content=msg["content"],
                    messageId=msg.get("messageId", ""),
                    timestamp=msg.get("timestamp", ""),
                ),
            )

    if not valid_messages:
        print(
            f"Warning: No valid messages in context for event {event.event_id} to identify question.",
        )
        return None

    identified_question = await identify_relevant_message_with_llm(
        document_content=document_content,
        message_context=valid_messages,
    )

    if not identified_question:
        return None

    return FaqContextExtractionData(
        event_type=event.event_type,
        event_id=event.event_id or "",
        identified_question=identified_question,
        document_content=document_content,
    )


async def perform_context_faq_extraction_and_update(
    db_connection: Database,
    data: FaqContextExtractionData,
) -> None:
    """
    Performs LLM answer extraction and updates MongoDB for contextual FAQ events.
    """
    print(
        f"Background task (Contextual FAQ): Starting answer extraction for event {data['event_id']} "
        f"and identified question: '{data['identified_question'][:50]}...'",
    )
    extracted_answer = await extract_answer_from_llm(
        question=data["identified_question"],
        context=data["document_content"],
    )

    update_fields = {}
    if extracted_answer is not None:
        update_fields["extracted_answer"] = extracted_answer
    update_fields["identified_user_question"] = data["identified_question"]

    if update_fields:
        try:
            coll = db_connection.get_collection(data["event_type"])
            result = await coll.update_one(
                {"event_id": data["event_id"]},
                {"$set": update_fields},
            )
            if result.modified_count > 0:
                print(
                    f"Background task (Contextual FAQ): Successfully updated event {data['event_id']} "
                    f"with answer and identified question.",
                )
            else:
                print(
                    f"Background task (Contextual FAQ): Event {data['event_id']} not found or no change after extraction.",
                )
        except Exception as e:
            print(
                f"Background task (Contextual FAQ): Error updating event {data['event_id']} in MongoDB: {e}",
            )
    else:
        print(
            f"Background task (Contextual FAQ): No answer extracted and no question identified for event {data['event_id']}.",
        )
