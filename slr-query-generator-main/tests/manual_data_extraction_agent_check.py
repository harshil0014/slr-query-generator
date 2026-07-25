"""No-network smoke check for the Data Extraction Agent."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.data_extraction import DataExtractionAgent
from tools.registry import ToolRegistry


def main() -> None:
    tools = ToolRegistry()
    tools.register(
        "extract.structured",
        lambda documents, topic: {
            "records": [{"title": documents[0]["title"], "methodology": "Review"}],
            "failures": [],
        },
    )
    update = DataExtractionAgent(tools).execute(
        {
            "topic": "Explainable AI in Healthcare",
            "screening_results": [
                {"Title": "Included paper", "Decision": "KEEP"},
                {"Title": "Excluded paper", "Decision": "REJECT"},
            ],
            "retrieved_documents": [
                {"title": "Included paper", "markdown": "Included"},
                {"title": "Excluded paper", "markdown": "Excluded"},
            ],
        }
    )
    assert update["lifecycle"] == "DATA_EXTRACTION"
    assert update["extracted_data"] == [{"title": "Included paper", "methodology": "Review"}]
    assert update["artifacts"]["data_extraction"]["included_document_count"] == 1
    print("Data Extraction Agent smoke check passed.")


if __name__ == "__main__":
    main()
