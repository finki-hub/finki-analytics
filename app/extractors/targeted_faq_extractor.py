import openai
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
)

from app.data.connection import Database
from app.utils.settings import Settings

settings = Settings()
openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

EXTRACTION_SYSTEM_PROMPT: ChatCompletionSystemMessageParam = {
    "role": "system",
    "content": (
        "Ти си искусен асистент чија единствена задача е да пронајде "
        "директен одговор на дадено прашање во дадениот текст. "
        "Твојот одговор мора да биде *точен извадок* од текстот, без никакво сумирање, "
        "преформулирање или додавање дополнителни информации. "
        "Ако одговорот не е експлицитно присутен во текстот, одговори со 'Не е пронајдено'."
        "Одговорот секогаш врати го на македонски јазик."
    ),
}


async def process_and_update(
    db_connection: Database,
    event_type: str,
    event_id: str,
    question: str,
    context: str,
) -> None:
    """
    Internal helper to perform the LLM call and update the MongoDB document.
    This will run as a background task.
    """
    print(
        f"Background task: Starting answer extraction for event {event_id} "
        f"and question: '{question[:50]}...'",
    )
    extracted_answer = await extract_answer_from_llm(question=question, context=context)

    if extracted_answer is not None:
        try:
            coll = db_connection.get_collection(event_type)
            result = await coll.update_one(
                {"event_id": event_id},
                {"$set": {"extracted_answer": extracted_answer}},
            )

            if result.modified_count > 0:
                print(
                    f"Background task: Successfully updated event {event_id} "
                    f"with answer: '{extracted_answer[:50]}...'",
                )
            else:
                print(
                    f"Background task: Event {event_id} not found or no change after extraction.",
                )
        except Exception as e:
            print(f"Background task: Error updating event {event_id} in MongoDB: {e}")
    else:
        print(f"Background task: No answer extracted for event {event_id}.")


async def extract_answer_from_llm(
    question: str,
    context: str,
    model_name: str = "gpt-4o-mini",
) -> str | None:
    """
    Performs the actual LLM call to extract the answer.
    """
    if not question or not context:
        print("Warning: Question or context is missing for LLM call.")
        return None

    messages: list[ChatCompletionMessageParam] = [
        EXTRACTION_SYSTEM_PROMPT,
        {
            "role": "user",
            "content": f"Текст: {context}\n\nПрашање: {question}\n\nОдговор:",
        },
    ]

    try:
        chat_completion = await openai_client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.0,
            max_tokens=256,
        )

        message_content = chat_completion.choices[0].message.content

        if message_content is None:
            print("Warning: LLM returned None content.")
            return None

        answer = message_content.strip()

        if answer == "Не е пронајдено":
            return None

        return answer  # noqa: TRY300
    except openai.APIError as e:
        print(f"LLM Call Error ({e.type}, {e.code}): {e.message}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during LLM call: {e}")
        return None
