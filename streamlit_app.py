"""Root Streamlit entrypoint for CSV/Data Q&A Agent."""
import os
import runpy
import sys
from pathlib import Path

# Load Streamlit secrets into environment variables if running on Streamlit Cloud
try:
    import streamlit as st
    for key in ("GROQ_API_KEY", "ANTHROPIC_API_KEY", "LLM_PROVIDER", "GROQ_MODEL", "ANTHROPIC_MODEL"):
        if hasattr(st, "secrets") and key in st.secrets and not os.getenv(key):
            os.environ[key] = str(st.secrets[key])
except Exception:
    pass

pkg_dir = Path(__file__).resolve().parent / "csv-qa-agent"
if str(pkg_dir) not in sys.path:
    sys.path.insert(0, str(pkg_dir))

if __name__ == "__main__":
    target = pkg_dir / "streamlit_app.py"
    runpy.run_path(str(target), run_name="__main__")
