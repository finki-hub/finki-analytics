from typing import TypedDict

from app.data.connection import Database
from app.extractors.core import extract_answer_from_llm
from app.schemas.events import UsageEvent


class FaqDirectExtractionData(TypedDict):
    event_type: str
    event_id: str
    user_question: str
    document_content: str


def prepare_direct_faq_data(event: UsageEvent) -> FaqDirectExtractionData | None:
    """
    Validates if an event has a direct targetUserMessage and returns
    the necessary data for background extraction.
    """
    if not isinstance(event.payload, dict):
        return None

    document_content = event.payload.get("content")
    if not isinstance(document_content, str) or not document_content:
        return None

    target_user_message = event.payload.get("targetUserMessage")
    if not isinstance(target_user_message, dict):
        return None

    user_question = target_user_message.get("content")
    if not isinstance(user_question, str) or not user_question:
        return None

    return FaqDirectExtractionData(
        event_type=event.event_type,
        event_id=event.event_id or "",
        user_question=user_question,
        document_content=document_content,
    )


async def perform_direct_faq_extraction_and_update(
    db_connection: Database,
    data: FaqDirectExtractionData,
) -> None:
    """
    Performs LLM answer extraction and updates MongoDB for direct FAQ events.
    """
    print(
        f"Background task (Direct FAQ): Starting answer extraction for event {data['event_id']} "
        f"and question: '{data['user_question'][:50]}...'",
    )
    extracted_answer = await extract_answer_from_llm(
        question=data["user_question"],
        context=data["document_content"],
    )

    update_fields = {}
    if extracted_answer is not None:
        update_fields["extracted_answer"] = extracted_answer
    update_fields["identified_user_question"] = data["user_question"]

    if update_fields:
        try:
            coll = db_connection.get_collection(data["event_type"])
            result = await coll.update_one(
                {"event_id": data["event_id"]},
                {"$set": update_fields},
            )
            if result.modified_count > 0:
                print(
                    f"Background task (Direct FAQ): Successfully updated event {data['event_id']} "
                    f"with answer and identified question.",
                )
            else:
                print(
                    f"Background task (Direct FAQ): Event {data['event_id']} not found or no change after extraction.",
                )
        except Exception as e:
            print(
                f"Background task (Direct FAQ): Error updating event {data['event_id']} in MongoDB: {e}",
            )
    else:
        print(
            f"Background task (Direct FAQ): No answer extracted and no question identified for event {data['event_id']}.",
        )
