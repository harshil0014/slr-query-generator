"""No-network smoke check for structured data extraction."""

from pathlib import Path
import sys
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.data_extraction import extract_structured_data


def main() -> None:
    response = (
        '{"objective":"Assess explainability", "methodology":"Review", '
        '"population_or_context":"Healthcare", "data_sources":"PubMed", '
        '"key_findings":"Useful", "limitations":"Small sample", '
        '"relevance_rationale":"Directly relevant"}'
    )
    with patch("tools.data_extraction._ask_gemini", return_value=response):
        result = extract_structured_data(
            [{"title": "A test paper", "doi": "10.1/test", "markdown": "Paper text"}],
            "Explainable AI in Healthcare",
        )
    assert result["failures"] == []
    assert result["records"][0]["methodology"] == "Review"
    assert result["records"][0]["doi"] == "10.1/test"
    print("Data extraction tool smoke check passed.")


if __name__ == "__main__":
    main()
