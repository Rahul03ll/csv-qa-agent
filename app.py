"""Root CLI entrypoint for CSV/Data Q&A Agent."""
import sys
from pathlib import Path

# Add csv-qa-agent package directory to sys.path
pkg_dir = Path(__file__).resolve().parent / "csv-qa-agent"
if str(pkg_dir) not in sys.path:
    sys.path.insert(0, str(pkg_dir))

from app import main

if __name__ == "__main__":
    main()
