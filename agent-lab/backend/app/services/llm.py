import json

from openai import OpenAI

from app.config import settings
from app.services.tools import TOOL_DEFINITION, run_tool


def get_chat_reply(
    history: list[dict[str, str]],
    system_prompt: str = "you are helpful assistant. Use tools to get the information you need.",
) -> str:
    if not settings.openai_api_key:
        raise RuntimeError("OpenAI API key is not set")

    client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)

    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt}
    ]
    messages.extend(history)

    response = client.chat.completions.create(
        model=settings.openai_model,
        messages= messages,
        tools=[TOOL_DEFINITION],
    )
    message = response.choices[0].message

    if message.tool_calls:
        messages.append(message)
        for tool_call in message.tool_calls:
            arguments = json.loads(tool_call.function.arguments or "{}")
            result = run_tool(tool_call.function.name, arguments)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                }
            )

        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            tools=[TOOL_DEFINITION],
        )
        message = response.choices[0].message

    return message.content or ""