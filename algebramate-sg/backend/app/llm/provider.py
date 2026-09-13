from __future__ import annotations

import httpx

from ..config import settings


class AgentRouterUnavailable(RuntimeError):
    pass


async def chat(messages: list[dict[str, str]], *, task: str = "primary", json_mode: bool = False) -> str:
    if not settings.agent_router_api_key or not settings.agent_router_base_url:
        raise AgentRouterUnavailable("Agent Router is not configured")
    model = settings.fast_model if task == "fast" else settings.primary_model
    base = settings.agent_router_base_url.rstrip("/")
    endpoint = base if base.endswith("/chat/completions") else f"{base}/chat/completions"
    payload: dict = {"model": model, "messages": messages, "temperature": 0.2}
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(endpoint, json=payload, headers={"Authorization": f"Bearer {settings.agent_router_api_key}"})
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
    except (httpx.HTTPError, KeyError, IndexError) as exc:
        raise AgentRouterUnavailable("The explanation service is temporarily unavailable") from exc
