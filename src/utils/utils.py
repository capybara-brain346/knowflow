import re


def clean_llm_response(response: str) -> str:
    response = response.strip()
    if response.startswith("```"):
        response = response.split("\n", 1)[-1]
        response = response.rsplit("```", 1)[0]
    return response.strip().replace("`", "")


def clean_whitespaes(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
