import os
from dotenv import load_dotenv

load_dotenv()

ACTIVE_LLM = os.getenv("ACTIVE_LLM", "mistral_local").strip().lower()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_API_URL = os.getenv("MISTRAL_API_URL")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL")
MISTRAL_LOCAL_URL = os.getenv("MISTRAL_LOCAL_URL")
MISTRAL_LOCAL_MODEL = os.getenv("MISTRAL_LOCAL_MODEL")


def get_active_llm():
    return ACTIVE_LLM


def get_mistral_config(mode=None):
    """Return the active Mistral endpoint settings.

    If mode is provided, it overrides ACTIVE_LLM. Otherwise the environment
    variable ACTIVE_LLM is used. Defaults to local Mistral when not set.
    """
    active = (mode or ACTIVE_LLM or "mistral_local").strip().lower()
    if active == "mistral_local":
        url = MISTRAL_LOCAL_URL or MISTRAL_API_URL
        if url and not url.endswith("/api/chat"):
            url = url.rstrip("/") + "/api/chat"
        model = MISTRAL_LOCAL_MODEL or MISTRAL_MODEL
    elif active == "mistral_cloud":
        url = MISTRAL_API_URL
        model = MISTRAL_MODEL
    else:
        raise ValueError(
            f"Unsupported LLM mode '{active}'. Expected 'mistral_local' or 'mistral_cloud'."
        )

    headers = {"Content-Type": "application/json"}
    if MISTRAL_API_KEY:
        headers["Authorization"] = f"Bearer {MISTRAL_API_KEY}"

    return {
        "active": active,
        "url": url,
        "model": model,
        "headers": headers,
    }
