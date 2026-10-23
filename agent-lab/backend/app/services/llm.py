from openai import OpenAI

from app.config import settings


def get_chat_reply(history: list[dict[str, str]]) -> str:
    """history example:
    [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
        {"role": "user", "content": "how are you"},
    ]
    """
    if not settings.openai_api_key:
        raise RuntimeError("OpenAI API key is not set")

    client = OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )

    messages = [
        {"role": "system", "content": "you are helpful assistant"}  
    ]
    messages.extend(history)

    response = client.chat.completions.create(
        model=settings.openai_model,
        messages= messages,
    )
    return response.choices[0].message.content or ""
