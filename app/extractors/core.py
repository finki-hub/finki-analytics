from typing import TypedDict

import openai
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
)

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

IDENTIFY_QUESTION_SYSTEM_PROMPT: ChatCompletionSystemMessageParam = {
    "role": "system",
    "content": (
        "Даден ти е документ и листа на пораки од разговор. Твоја задача е да идентификуваш "
        "која порака (ако воопшто има таква) од листата е најрелевантно прашање или барање "
        "што може да биде одговорено од дадениот документ. "
        "Ако пронајдеш релевантна порака, врати го само нејзиниот *точен текст* без никакви додатоци. "
        "Ако ниту една порака не е релевантно прашање за документот, одговори со 'Нема релевантна порака'."
        "Одговори секогаш на македонски јазик."
    ),
}


class DiscordMessage(TypedDict):
    authorId: str
    content: str
    messageId: str
    timestamp: str


async def extract_answer_from_llm(
    question: str,
    context: str,
    model_name: str = "gpt-4o-mini",
) -> str | None:
    """
    Performs the actual LLM call to extract the answer from a document
    given a direct question.
    """
    if not question or not context:
        print("Warning: Question or context is missing for LLM answer extraction.")
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
            print("Warning: LLM returned None content for answer extraction.")
            return None

        answer = message_content.strip()

        if answer == "Не е пронајдено":
            return None

        return answer  # noqa: TRY300
    except openai.APIError as e:
        print(f"LLM Answer Extraction Call Error ({e.type}, {e.code}): {e.message}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during LLM answer extraction: {e}")
        return None


async def identify_relevant_message_with_llm(
    document_content: str,
    message_context: list[DiscordMessage],
    model_name: str = "gpt-4o-mini",
) -> str | None:
    """
    Identifies the most relevant user message from a list of Discord messages
    that acts as a question for the given document content, using an LLM.
    """
    if not document_content or not message_context:
        print(
            "Warning: Document content or message context is missing for LLM question identification.",
        )
        return None

    formatted_messages = "\n".join(
        [
            f'- Порака: "{msg.get("content", "")}"'
            for msg in message_context
            if msg.get("content")
        ],
    )

    if not formatted_messages:
        print(
            "Warning: No valid messages found in context to process for LLM identification.",
        )
        return None

    user_query = (
        f"Документ:\n{document_content}\n\n"
        f"Листа на пораки:\n{formatted_messages}\n\n"
        "Најрелевантна порака (точен текст):"
    )

    messages: list[ChatCompletionMessageParam] = [
        IDENTIFY_QUESTION_SYSTEM_PROMPT,
        {"role": "user", "content": user_query},
    ]

    try:
        chat_completion = await openai_client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.0,
            max_tokens=150,
        )

        identified_message = chat_completion.choices[0].message.content
        if identified_message is None:
            return None

        identified_message = identified_message.strip()

        if identified_message == "Нема релевантна порака":
            return None

        return identified_message  # noqa: TRY300
    except openai.APIError as e:
        print(
            f"LLM Question Identification Call Error ({e.type}, {e.code}): {e.message}",
        )
        return None
    except Exception as e:
        print(f"An unexpected error occurred during LLM question identification: {e}")
        return None
