"""No-network smoke check for the API-backed legacy screening adapter."""

from pathlib import Path
import sys
from types import ModuleType
from unittest.mock import patch

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.screening import GEMINI_API_ENGINE, run_screening


def main() -> None:
    legacy_module = ModuleType("bulk_screen")

    def screen_csv(**options):
        assert options["mode"] == GEMINI_API_ENGINE
        assert options["screening_engine"] == GEMINI_API_ENGINE
        assert options["gemini_api_key"] == "test-key"
        input_rows = pd.read_csv(options["csv_path"])
        pd.DataFrame(
            [{"Title": input_rows.iloc[0]["Title"], "Decision": "KEEP"}]
        ).to_csv(options["output_path"], index=False)
        return {"keep": 1, "reject": 0}

    legacy_module.screen_csv = screen_csv
    with patch.dict(sys.modules, {"bulk_screen": legacy_module}):
        result = run_screening(
            [{"title": "A test paper", "abstract": "A test abstract"}],
            "Is the paper relevant?",
            inclusion_criteria=["Healthcare"],
            api_key="test-key",
        )

    assert result["engine"] == GEMINI_API_ENGINE
    assert result["summary"]["keep"] == 1
    assert result["papers"] == [{"Title": "A test paper", "Decision": "KEEP"}]
    print("Screening tool smoke check passed.")


if __name__ == "__main__":
    main()
