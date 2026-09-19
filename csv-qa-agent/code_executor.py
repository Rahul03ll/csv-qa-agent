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
    "signal", "multiprocessing", "pickle", "shelve", "builtins",
    "tempfile", "io", "pty", "posix", "nt", "webbrowser",
    "ftplib", "smtplib", "telnetlib", "asyncio", "threading",
    "inspect", "gc", "code", "codecs", "platform", "venv",
})

BLOCKED_FUNCTIONS = frozenset({
    "open", "eval", "exec", "compile", "__import__", "breakpoint", "exit", "quit", "input",
})

BLOCKED_NAMES = frozenset({
    "open", "eval", "exec", "compile", "__import__", "breakpoint", "exit", "quit", "input",
    "__builtins__",
})

BLOCKED_ATTRIBUTES = frozenset({
    "__subclasses__", "__globals__", "__code__", "__closure__", "__bases__", "__mro__",
    "__builtins__",
    "to_csv", "to_excel", "to_parquet", "to_feather", "to_pickle", "to_sql",
    "to_hdf", "to_stata", "to_clipboard", "to_xml",
    "read_pickle", "read_csv", "read_excel", "read_sql", "read_table",
    "read_parquet", "read_feather", "read_hdf",
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
    """Inspect AST for blocked imports, dangerous builtins, attributes, and evasion patterns."""
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
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in BLOCKED_FUNCTIONS:
                raise CodeExecutionError(
                    f"Blocked function call: '{node.func.id}()' is not allowed for security.",
                    code,
                )
        elif isinstance(node, ast.Name):
            if node.id in BLOCKED_NAMES and node.id not in BLOCKED_FUNCTIONS:
                raise CodeExecutionError(
                    f"Blocked access to restricted name: '{node.id}' is not allowed for security.",
                    code,
                )
        elif isinstance(node, ast.Attribute):
            if node.attr in BLOCKED_ATTRIBUTES:
                raise CodeExecutionError(
                    f"Blocked attribute access: '.{node.attr}' is not allowed for security.",
                    code,
                )
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            val = node.value
            if val.startswith("__") and val.endswith("__"):
                raise CodeExecutionError(
                    f"Blocked dunder reference: '{val}' is not allowed for security.",
                    code,
                )


def _format_result(result: Any) -> str:
    """Convert result to a readable string for display and logging."""
    if isinstance(result, pd.DataFrame):
        return result.to_string(index=True)
    if isinstance(result, pd.Series):
        return result.to_string()
    if hasattr(result, "savefig"):
        return "[Matplotlib Figure generated]"
    return str(result)


def _safe_import(name: str, *args: Any, **kwargs: Any) -> Any:
    """Restricted importer verifying module name against blocked list."""
    root = name.split(".")[0]
    if root in BLOCKED_MODULES:
        raise CodeExecutionError(
            f"Blocked import: '{name}' is not allowed for security.", ""
        )
    return __import__(name, *args, **kwargs)


def _get_safe_builtins() -> dict[str, Any]:
    """Construct a restricted __builtins__ dictionary without dangerous functions."""
    import builtins
    safe = {
        k: getattr(builtins, k)
        for k in dir(builtins)
        if k not in BLOCKED_NAMES and not (k.startswith("__") and k.endswith("__"))
    }
    safe["__import__"] = _safe_import
    return safe


def _exec_with_timeout(code: str, namespace: dict, timeout: int) -> None:
    """Run exec() in a thread with a timeout and restricted builtins."""
    exc_holder: list[BaseException] = []
    safe_builtins = _get_safe_builtins()

    def _target():
        try:
            exec(compile(code, "<generated>", "exec"), {"__builtins__": safe_builtins}, namespace)
        except BaseException as exc:
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
    if not code or not code.strip():
        raise CodeExecutionError("Generated code cannot be empty.", code or "")
    if df is None:
        raise CodeExecutionError("Input DataFrame cannot be None.", code)

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
        plt.close("all")
        namespace["plt"] = plt
        namespace["matplotlib"] = matplotlib
    except ImportError:
        pass

    try:
        _exec_with_timeout(code, namespace, EXECUTION_TIMEOUT)
    except (CodeExecutionError, ExecutionTimeoutError):
        raise
    except BaseException as exc:
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
