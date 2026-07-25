"""No-network smoke check for the Screening Agent."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.screening import ScreeningAgent
from tools.registry import ToolRegistry


def main() -> None:
    tools = ToolRegistry()
    tools.register(
        "screen.run",
        lambda papers, question, **_: {
            "engine": "gemini_api",
            "summary": {"keep": 1},
            "papers": [{"Title": papers[0]["title"], "Decision": "KEEP"}],
        },
    )
    update = ScreeningAgent(tools).execute(
        {
            "topic": "Explainable AI in Healthcare",
            "search_results": [{"title": "A test paper", "abstract": "Abstract"}],
            "inclusion_criteria": ["Healthcare"],
            "exclusion_criteria": [],
        }
    )
    assert update["lifecycle"] == "SCREENING"
    assert update["screening_results"] == [
        {"Title": "A test paper", "Decision": "KEEP"}
    ]
    assert update["artifacts"]["screening"]["engine"] == "gemini_api"
    print("Screening Agent smoke check passed.")


if __name__ == "__main__":
    main()
