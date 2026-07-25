from __future__ import annotations

import re
import os
from typing import Any


def generate_boolean_query(topic: str) -> dict[str, Any]:
    """Generate a stable autonomous query without requiring a local model server."""
    clean_topic = topic.replace(chr(34), "").strip()
    if os.getenv("ENABLE_LEGACY_LOCAL_QUERY_GENERATOR", "").lower() in {"1", "true", "yes"}:
        try:
            from direct_ai_generator import generate_query

            query = generate_query(clean_topic).replace("\n", " ").strip()
            return {"query": query, "source": "legacy_direct_ai_generator"}
        except Exception as exc:
            return {
                "query": f'"{clean_topic}"',
                "source": "deterministic_fallback",
                "warning": str(exc),
            }
    return {"query": f'"{clean_topic}"', "source": "deterministic_autonomous"}


def validate_boolean_query(query: str) -> dict[str, Any]:
    compact = str(query or "").strip()
    errors: list[str] = []
    if not compact:
        errors.append("Query is empty.")
    if compact.count("(") != compact.count(")"):
        errors.append("Query has unbalanced parentheses.")
    if not re.search(r'"[^\"]+"', compact):
        errors.append("Query must contain at least one quoted concept.")
    return {"valid": not errors, "errors": errors, "query": compact}


def register_query_tools(registry) -> None:
    registry.register("query.generate", generate_boolean_query)
    registry.register("query.validate", validate_boolean_query)
