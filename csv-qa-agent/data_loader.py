"""Load CSV/Excel/JSON/TSV files and produce a compact schema summary for the LLM.

Features:
- Supports .csv, .tsv, .xlsx, .xls, .json formats
- Auto-detects and parses date columns
- Builds a rich schema with descriptive statistics
"""

from pathlib import Path

import pandas as pd


SUPPORTED_FORMATS = {".csv", ".tsv", ".xlsx", ".xls", ".json"}


def load_dataset(file_path: str | Path) -> pd.DataFrame:
    """Load a dataset into a pandas DataFrame.

    Supports CSV, TSV, Excel (.xlsx/.xls), and JSON files.
    Automatically parses date-like columns.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    suffix = path.suffix.lower()

    if suffix == ".csv":
        try:
            df = pd.read_csv(path)
        except UnicodeDecodeError:
            df = pd.read_csv(path, encoding="latin1")
    elif suffix == ".tsv":
        df = pd.read_csv(path, sep="\t")
    elif suffix in (".xlsx", ".xls"):
        df = pd.read_excel(path)
    elif suffix == ".json":
        df = pd.read_json(path)
    else:
        raise ValueError(
            f"Unsupported file type: {suffix}. "
            f"Supported: {', '.join(sorted(SUPPORTED_FORMATS))}"
        )

    # Clean column headers (strip leading/trailing whitespace and UTF-8 BOM)
    df.columns = [str(c).lstrip("\ufeff").strip() for c in df.columns]

    # Auto-detect date columns
    df = _parse_date_columns(df)

    return df


def _parse_date_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Try to parse object columns that look like dates."""
    for col in df.select_dtypes(include=["object", "string"]).columns:
        if any(kw in str(col).lower() for kw in ("date", "time", "created", "updated")):
            try:
                df[col] = pd.to_datetime(df[col], format="mixed", dayfirst=False)
            except (ValueError, TypeError):
                pass  # not a date column, leave as-is
    return df


def build_schema_summary(df: pd.DataFrame, sample_rows: int = 5) -> str:
    """Build a compact schema string with columns, dtypes, stats, and sample rows.

    This is what gets sent to the LLM — it never sees the full dataset.
    """
    lines = [
        f"Shape: {df.shape[0]} rows x {df.shape[1]} columns",
        "",
        "Columns and dtypes:",
    ]

    for col in df.columns:
        non_null = int(df[col].notna().sum())
        dtype_str = str(df[col].dtype)
        col_info = f"  - {col}: {dtype_str} ({non_null} non-null)"

        # Add descriptive stats inline
        if pd.api.types.is_bool_dtype(df[col]):
            true_count = int(df[col].sum())
            false_count = non_null - true_count
            col_info += f" | boolean (True: {true_count}, False: {false_count})"
        elif pd.api.types.is_numeric_dtype(df[col]):
            if len(df) > 0 and non_null > 0:
                stats = df[col].describe()
                if "min" in stats and "max" in stats and "mean" in stats:
                    col_info += (
                        f" | min={stats['min']:.2f}, max={stats['max']:.2f}, "
                        f"mean={stats['mean']:.2f}"
                    )
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            if len(df) > 0 and non_null > 0:
                col_info += f" | range: {df[col].min()} to {df[col].max()}"
        elif (
            pd.api.types.is_string_dtype(df[col])
            or pd.api.types.is_object_dtype(df[col])
            or isinstance(df[col].dtype, pd.CategoricalDtype)
        ):
            nunique = int(df[col].nunique())
            col_info += f" | {nunique} unique"
            if 0 < nunique <= 15:
                top_vals = df[col].value_counts().head(8).index.tolist()
                col_info += f" | values: {top_vals}"

        lines.append(col_info)

    lines.append("")
    sample_count = min(sample_rows, len(df))
    lines.append(f"Sample rows (first {sample_count}):")
    if sample_count > 0:
        sample = df.head(sample_count)
        lines.append(sample.to_string(index=False))
    else:
        lines.append("  (empty dataset)")

    return "\n".join(lines)
