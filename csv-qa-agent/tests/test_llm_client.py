"""Unit tests for llm_client module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from llm_client import extract_code, get_model_info


class TestExtractCode:
    def test_extracts_from_fenced_block(self):
        text = "Here is the code:\n```python\nresult = df['rating'].mean()\n```\nHope that helps!"
        assert extract_code(text) == "result = df['rating'].mean()"

    def test_extracts_from_plain_fenced_block(self):
        text = "```\nresult = len(df)\n```"
        assert extract_code(text) == "result = len(df)"

    def test_extracts_with_reasoning_tags(self):
        text = "<think>\nThinking about calculating mean rating...\n</think>\n```python\nresult = df['rating'].mean()\n```"
        assert extract_code(text) == "result = df['rating'].mean()"

    def test_extracts_raw_code(self):
        text = "result = df['votes'].sum()"
        assert extract_code(text) == "result = df['votes'].sum()"

    def test_extracts_from_py_tag(self):
        text = "Here is the code:\n```py\nresult = df['score'].max()\n```\nDone"
        assert extract_code(text) == "result = df['score'].max()"

    def test_extracts_from_python3_tag(self):
        text = "```python3\nresult = df.shape[0]\n```"
        assert extract_code(text) == "result = df.shape[0]"

    def test_extracts_with_thought_tags(self):
        text = "<thought>Need to count rows</thought>\n```python\nresult = len(df)\n```"
        assert extract_code(text) == "result = len(df)"

    def test_extracts_with_unclosed_reasoning_tags(self):
        text = "<think>Analyzing dataset columns...\n```python\nresult = df['city'].nunique()\n```"
        assert extract_code(text) == "result = df['city'].nunique()"


class TestGetModelInfo:
    def test_get_model_info_returns_dict(self):
        info = get_model_info()
        assert isinstance(info, dict)
        assert "provider" in info
        assert "model" in info
