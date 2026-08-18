"""Sandboxed execution of LLM-generated pandas code.

Safety features:
- AST inspection blocks dangerous imports (os, sys, subprocess, etc.)
- Execution timeout (10 seconds)
- Restricted namespace (only df, pd, np, and builtins)
- Matplotlib figure capture for chart questions
"""

import ast
import io
import threading
from typing import Any

import numpy as np
import pandas as pd

BLOCKED_MODULES = frozenset({
    "os", "sys", "subprocess", "shutil", "pathlib", "socket",
    "http", "urllib", "requests", "importlib", "ctypes",
    "signal", "multiprocessing", "pickle", "shelve",
})

EXECUTION_TIMEOUT = 10  # seconds


class CodeExecutionError(Exception):
    """Raised when generated code fails to execute."""

    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code


class ExecutionTimeoutError(CodeExecutionError):
    """Raised when generated code exceeds the execution time limit."""
    pass


def _check_imports(code: str) -> None:
    """Inspect AST for blocked import statements."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return  # let exec() raise the real error

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in BLOCKED_MODULES:
                    raise CodeExecutionError(
                        f"Blocked import: '{alias.name}' is not allowed for security.",
                        code,
                    )
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root = node.module.split(".")[0]
                if root in BLOCKED_MODULES:
                    raise CodeExecutionError(
                        f"Blocked import: 'from {node.module}' is not allowed for security.",
                        code,
                    )


def _format_result(result: Any) -> str:
    """Convert result to a readable string for display and logging."""
    if isinstance(result, pd.DataFrame):
        return result.to_string(index=True)
    if isinstance(result, pd.Series):
        return result.to_string()
    return str(result)


def _exec_with_timeout(code: str, namespace: dict, timeout: int) -> None:
    """Run exec() in a thread with a timeout."""
    exc_holder: list[Exception] = []

    def _target():
        try:
            exec(compile(code, "<generated>", "exec"), {"__builtins__": __builtins__}, namespace)
        except Exception as exc:
            exc_holder.append(exc)

    thread = threading.Thread(target=_target, daemon=True)
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        raise ExecutionTimeoutError(
            f"Code execution exceeded {timeout}s timeout.", code
        )
    if exc_holder:
        raise exc_holder[0]


def execute_code(code: str, df: pd.DataFrame) -> tuple[Any, str]:
    """
    Execute pandas code in a restricted namespace.

    Returns (result_object, formatted_result_string).
    Raises CodeExecutionError on failure.
    """
    # Safety: block dangerous imports before execution
    _check_imports(code)

    namespace: dict[str, Any] = {
        "df": df.copy(),
        "pd": pd,
        "np": np,
    }

    # Try to make matplotlib available for chart questions
    try:
        import matplotlib
        matplotlib.use("Agg")  # non-interactive backend
        import matplotlib.pyplot as plt
        namespace["plt"] = plt
        namespace["matplotlib"] = matplotlib
    except ImportError:
        pass

    try:
        _exec_with_timeout(code, namespace, EXECUTION_TIMEOUT)
    except (CodeExecutionError, ExecutionTimeoutError):
        raise
    except Exception as exc:
        raise CodeExecutionError(str(exc), code) from exc

    # Capture matplotlib figure if one was created
    fig = None
    try:
        import matplotlib.pyplot as plt
        if plt.get_fignums():
            fig = plt.gcf()
            namespace["result_fig"] = fig
    except (ImportError, Exception):
        pass

    if "result" not in namespace:
        raise CodeExecutionError(
            "Generated code did not assign a variable named `result`.", code
        )

    result = namespace["result"]
    return result, _format_result(result)
