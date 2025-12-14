import json
import os

CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".ai_assistant_config.json")


def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f)
    except Exception as e:
        print("Warning: failed to save config:", e)


def default_model_for_provider(provider: str):
    if provider == "openai":
        return "gpt-3.5-turbo"
    if provider == "gemini":
        return "text-bison-001"
    return None


def model_options_for_provider(provider: str):
    if provider == "openai":
        return ["gpt-3.5-turbo", "gpt-4", "gpt-4o"]
    if provider == "gemini":
        return ["text-bison-001"]
    return []
