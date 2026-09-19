"""Unit tests for data_loader module."""

import sys
from pathlib import Path

import pandas as pd
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_loader import build_schema_summary, load_dataset, _parse_date_columns


@pytest.fixture
def sample_df():
    """Create a small test DataFrame."""
    return pd.DataFrame({
        "name": ["Alice", "Bob", "Charlie"],
        "city": ["NYC", "LA", "NYC"],
        "rating": [4.5, 3.2, 4.8],
        "votes": [100, 200, 150],
        "listed_date": ["2024-01-15", "2024-02-20", "2024-03-10"],
    })


@pytest.fixture
def csv_file(tmp_path, sample_df):
    """Write sample data to a temp CSV."""
    path = tmp_path / "test.csv"
    sample_df.to_csv(path, index=False)
    return path


@pytest.fixture
def json_file(tmp_path, sample_df):
    """Write sample data to a temp JSON."""
    path = tmp_path / "test.json"
    sample_df.to_json(path)
    return path


class TestLoadDataset:
    def test_load_csv(self, csv_file):
        df = load_dataset(csv_file)
        assert df.shape == (3, 5)
        assert list(df.columns) == ["name", "city", "rating", "votes", "listed_date"]

    def test_load_json(self, json_file):
        df = load_dataset(json_file)
        assert df.shape[0] == 3

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_dataset("nonexistent.csv")

    def test_unsupported_format(self, tmp_path):
        path = tmp_path / "data.xyz"
        path.write_text("hello")
        with pytest.raises(ValueError, match="Unsupported"):
            load_dataset(path)

    def test_auto_date_parsing(self, csv_file):
        df = load_dataset(csv_file)
        assert pd.api.types.is_datetime64_any_dtype(df["listed_date"])


class TestParseDateColumns:
    def test_parses_date_column(self):
        df = pd.DataFrame({"created_date": ["2024-01-01", "2024-06-15"]})
        result = _parse_date_columns(df)
        assert pd.api.types.is_datetime64_any_dtype(result["created_date"])

    def test_ignores_non_date_column(self):
        df = pd.DataFrame({"name": ["Alice", "Bob"]})
        result = _parse_date_columns(df)
        assert pd.api.types.is_string_dtype(result["name"])


class TestBuildSchemaSummary:
    def test_contains_shape(self, sample_df):
        schema = build_schema_summary(sample_df)
        assert "3 rows × 5 columns" in schema

    def test_contains_columns(self, sample_df):
        schema = build_schema_summary(sample_df)
        assert "name:" in schema
        assert "rating:" in schema

    def test_numeric_stats(self, sample_df):
        schema = build_schema_summary(sample_df)
        assert "min=" in schema
        assert "max=" in schema
        assert "mean=" in schema

    def test_categorical_unique_counts(self, sample_df):
        schema = build_schema_summary(sample_df)
        # With pandas 3.x+, string columns include unique counts
        assert "unique" in schema or "3 non-null" in schema

    def test_sample_rows_displayed(self, sample_df):
        schema = build_schema_summary(sample_df, sample_rows=2)
        assert "Alice" in schema
        assert "Bob" in schema

    def test_boolean_column_handling(self):
        df = pd.DataFrame({"active": [True, False, True]})
        schema = build_schema_summary(df)
        assert "boolean (True: 2, False: 1)" in schema

    def test_empty_dataframe_handling(self):
        df = pd.DataFrame({"col_num": pd.Series(dtype="float64"), "col_str": pd.Series(dtype="object")})
        schema = build_schema_summary(df)
        assert "0 rows × 2 columns" in schema
        assert "empty dataset" in schema

    def test_categorical_column_handling(self):
        df = pd.DataFrame({"category": pd.Categorical(["A", "B", "A", "C"])})
        schema = build_schema_summary(df)
        assert "3 unique" in schema

