import re
import json


def clean_llm_response(response: str) -> str:
    response = response.strip()
    if response.startswith("```"):
        response = response.split("\n", 1)[-1]
        response = response.rsplit("\n```", 1)[0]
        response = response.rsplit("```", 1)[0]

    response = response.replace("`", "")
    response = re.sub(r"^json\n|^JSON\n", "", response, flags=re.MULTILINE)
    response = re.sub(r"#.*$", "", response, flags=re.MULTILINE)
    response = re.sub(r"\s+", " ", response)
    response = response.strip()

    if response.startswith("{") and response.endswith("}"):
        try:
            parsed = json.loads(response)
            return json.dumps(parsed, indent=2)
        except json.JSONDecodeError:
            pass

    return response


def clean_whitespaes(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
