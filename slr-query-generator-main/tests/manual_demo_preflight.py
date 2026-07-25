"""Check only the Python packages required by the hackathon demo runtime."""

import importlib


REQUIRED_MODULES = {
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "langgraph": "langgraph",
    "supabase": "supabase",
    "httpx": "httpx",
    "pandas": "pandas",
    "google.genai": "google-genai",
}


def main() -> None:
    missing = []
    for module, package in REQUIRED_MODULES.items():
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append(package)
    if missing:
        print("Missing demo packages: " + ", ".join(missing))
        raise SystemExit(1)
    print("Demo runtime preflight passed.")


if __name__ == "__main__":
    main()
