import re

from src.models import GuardrailResult


DESTRUCTIVE_SQL = re.compile(
    r"\b(drop\s+(table|schema|view)|delete\s+from|update\s+\w+\s+set|"
    r"insert\s+into|alter\s+table|truncate\s+table|"
    r"create\s+(table|schema|view|user)|grant\s+|revoke\s+|"
    r"copy\s+\w+\s+from|unload\s*\()",
    re.IGNORECASE,
)
PROMPT_INJECTION = re.compile(
    r"(ignore (?:all |any |the |your |previous )*(?:rules|instructions)|"
    r"reveal (the )?(system|developer) prompt|bypass (the )?(guardrails|rules))",
    re.IGNORECASE,
)
SECRET_PATTERNS = [
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"(?i)(password|api[_ -]?key|secret|token)\s*[:=]\s*\S+"),
    re.compile(r"(?i)(postgres|redshift)://[^\s]+"),
]


def check_input(text: str, max_length: int = 2000) -> GuardrailResult:
    if not text.strip():
        return GuardrailResult(
            allowed=False,
            reason="empty_input",
            safe_message="Please enter a database metadata question.",
        )
    if len(text) > max_length:
        return GuardrailResult(
            allowed=False,
            reason="input_too_long",
            safe_message=f"Please keep the question below {max_length} characters.",
        )
    if any(pattern.search(text) for pattern in SECRET_PATTERNS):
        return GuardrailResult(
            allowed=False,
            reason="possible_secret",
            safe_message="Please remove credentials, API keys, tokens, and connection strings.",
        )
    if PROMPT_INJECTION.search(text):
        return GuardrailResult(
            allowed=False,
            reason="prompt_injection",
            safe_message="I cannot bypass my metadata and safety rules.",
        )
    if DESTRUCTIVE_SQL.search(text):
        return GuardrailResult(
            allowed=False,
            reason="destructive_sql",
            safe_message=(
                "SchemaSense is read-only and does not support destructive or modifying SQL. "
                "You can ask about tables, columns, keys, and relationships."
            ),
        )
    return GuardrailResult(allowed=True)
