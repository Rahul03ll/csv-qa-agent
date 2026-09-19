"""Root Streamlit entrypoint for CSV/Data Q&A Agent."""
import runpy
import sys
from pathlib import Path

pkg_dir = Path(__file__).resolve().parent / "csv-qa-agent"
if str(pkg_dir) not in sys.path:
    sys.path.insert(0, str(pkg_dir))

if __name__ == "__main__":
    target = pkg_dir / "streamlit_app.py"
    runpy.run_path(str(target), run_name="__main__")
