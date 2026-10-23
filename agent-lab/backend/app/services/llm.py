from openai import OpenAI

from app.config import settings


def get_chat_reply(user_message: str) -> str:
    if not settings.openai_api_key:
        raise RuntimeError("OpenAI API key is not set")

    client = OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": "you are helpful assistant"},
            {"role": "user", "content": user_message},
        ],
    )
    return response.choices[0].message.content or ""
