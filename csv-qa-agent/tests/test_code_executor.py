"""Unit tests for code_executor module."""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from code_executor import (
    CodeExecutionError,
    ExecutionTimeoutError,
    execute_code,
    _check_imports,
    _format_result,
)


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "name": ["Alice", "Bob", "Charlie"],
        "score": [85, 92, 78],
        "city": ["NYC", "LA", "NYC"],
    })


class TestExecuteCode:
    def test_simple_assignment(self, sample_df):
        result, formatted = execute_code('result = df["score"].mean()', sample_df)
        assert result == 85.0

    def test_result_must_exist(self, sample_df):
        with pytest.raises(CodeExecutionError, match="did not assign"):
            execute_code('x = 42', sample_df)

    def test_dataframe_result(self, sample_df):
        result, formatted = execute_code(
            'result = df[df["city"] == "NYC"]', sample_df
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2

    def test_series_result(self, sample_df):
        result, formatted = execute_code(
            'result = df["score"]', sample_df
        )
        assert isinstance(result, pd.Series)

    def test_syntax_error(self, sample_df):
        with pytest.raises(CodeExecutionError):
            execute_code('result = def', sample_df)

    def test_runtime_error(self, sample_df):
        with pytest.raises(CodeExecutionError):
            execute_code('result = df["nonexistent_col"].sum()', sample_df)

    def test_numpy_available(self, sample_df):
        result, _ = execute_code('result = np.mean([1, 2, 3])', sample_df)
        assert result == 2.0

    def test_df_not_mutated(self, sample_df):
        original_len = len(sample_df)
        execute_code('df.drop(0, inplace=True)\nresult = len(df)', sample_df)
        assert len(sample_df) == original_len  # original not touched


class TestCheckImports:
    def test_blocks_os(self):
        with pytest.raises(CodeExecutionError, match="Blocked import"):
            _check_imports("import os")

    def test_blocks_subprocess(self):
        with pytest.raises(CodeExecutionError, match="Blocked import"):
            _check_imports("import subprocess")

    def test_blocks_from_import(self):
        with pytest.raises(CodeExecutionError, match="Blocked import"):
            _check_imports("from os import path")

    def test_allows_pandas(self):
        _check_imports("import pandas as pd")  # should not raise

    def test_allows_numpy(self):
        _check_imports("import numpy as np")  # should not raise

    def test_syntax_error_passthrough(self):
        # Syntax errors should not raise in _check_imports (let exec handle it)
        _check_imports("this is not valid python")  # should not raise

    def test_blocks_open_call(self):
        with pytest.raises(CodeExecutionError, match=r"Blocked function call: 'open\(\)'"):
            _check_imports("open('secret.txt')")

    def test_blocks_eval_call(self):
        with pytest.raises(CodeExecutionError, match=r"Blocked function call: 'eval\(\)'"):
            _check_imports("eval('1+1')")

    def test_blocks_exec_call(self):
        with pytest.raises(CodeExecutionError, match=r"Blocked function call: 'exec\(\)'"):
            _check_imports("exec('x = 1')")


    def test_blocks_builtins_import(self):
        with pytest.raises(CodeExecutionError, match="Blocked import"):
            _check_imports("import builtins")

    def test_empty_code_raises(self, sample_df):
        with pytest.raises(CodeExecutionError, match="empty"):
            execute_code("", sample_df)

    def test_none_df_raises(self):
        with pytest.raises(CodeExecutionError, match="None"):
            execute_code("result = 1", None)



class TestFormatResult:
    def test_string(self):
        assert _format_result("hello") == "hello"

    def test_number(self):
        assert _format_result(42) == "42"

    def test_float(self):
        assert _format_result(3.14) == "3.14"

    def test_dataframe(self, sample_df):
        result = _format_result(sample_df)
        assert "Alice" in result
        assert "Bob" in result

    def test_series(self):
        s = pd.Series([1, 2, 3], name="test")
        result = _format_result(s)
        assert "1" in result
