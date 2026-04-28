from typing import Dict, Any

def get_style_config(preferences, level) -> Dict[str, Any]:
    """
    Returns strict configuration for both prompt engineering and output enforcement.
    """
    if not preferences:
        return {
            "type": "explanation",
            "require_code_first": False
        }

    if "code" in preferences:
        return {
            "type": "code-heavy",
            "require_code_first": True,
            "max_lines": 12,
            "simple_language": True if level == "beginner" else False
        }

    if "short" in preferences:
        return {
            "type": "short",
            "require_code_first": False,
            "max_lines": 5
        }

    return {
        "type": "explanation",
        "require_code_first": False
    }

def get_response_style(preferences, level) -> str:
    config = get_style_config(preferences, level)
    return config["type"]
