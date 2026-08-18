"""Unit tests for prompts module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from prompts import SYSTEM_PROMPT, RETRY_PROMPT, build_user_message


class TestSystemPrompt:
    def test_contains_placeholder(self):
        assert "{schema}" in SYSTEM_PROMPT

    def test_format_works(self):
        formatted = SYSTEM_PROMPT.format(schema="test schema here")
        assert "test schema here" in formatted
        assert "{schema}" not in formatted

    def test_contains_rules(self):
        assert "result" in SYSTEM_PROMPT
        assert "pandas" in SYSTEM_PROMPT.lower()

    def test_contains_examples(self):
        assert "groupby" in SYSTEM_PROMPT
        assert "idxmax" in SYSTEM_PROMPT


class TestRetryPrompt:
    def test_contains_placeholders(self):
        assert "{error}" in RETRY_PROMPT
        assert "{code}" in RETRY_PROMPT

    def test_format_works(self):
        formatted = RETRY_PROMPT.format(error="KeyError: 'x'", code="result = df['x']")
        assert "KeyError" in formatted
        assert "result = df['x']" in formatted


class TestBuildUserMessage:
    def test_basic(self):
        msg = build_user_message("What is the average?")
        assert "What is the average?" in msg
        assert "Question:" in msg

    def test_preserves_question(self):
        q = "How many rows have rating > 4.0?"
        msg = build_user_message(q)
        assert q in msg
