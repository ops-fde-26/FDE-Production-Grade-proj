from datetime import datetime, timezone

TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "get_current_time",
        "description": "get the current date and time in UTC",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
}


def get_current_time() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def run_tool(name: str, arguments: dict[str, str]) -> str:
    if name == "get_current_time":
        return get_current_time()
    return f"unknown tool {name}"
