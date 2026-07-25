"""Standalone smoke check for the Phase 1 query-tool adapter.

Run directly with Python; pytest and external services are not required.
"""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.query_tools import register_query_tools
from tools.registry import ToolRegistry


def main() -> None:
    registry = ToolRegistry()
    register_query_tools(registry)

    assert registry.ids() == ("query.generate", "query.validate")
    generated = registry.get("query.generate")("Explainable AI in Healthcare")
    assert generated["source"] == "deterministic_autonomous", generated
    result = registry.get("query.validate")(generated["query"])
    assert result["valid"] is True, result
    print("Query tool smoke check passed.")


if __name__ == "__main__":
    main()
