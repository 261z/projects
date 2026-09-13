from ..config import settings


def selected_model(task: str) -> str:
    return settings.fast_model if task in {"routing", "classification", "extraction"} else settings.primary_model
