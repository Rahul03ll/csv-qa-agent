"""CLI entry point for the CSV/Data Q&A agent.

Modes:
- Interactive: ask questions in a loop
- Single question: pass -q "your question"

Every Q&A pair is logged to outputs/qa_log.json with the generated code,
result, timestamp, and model used — providing full transparency.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from code_executor import CodeExecutionError, execute_code
from data_loader import build_schema_summary, load_dataset
from llm_client import generate_code, get_model_info

DEFAULT_DATASET = Path(__file__).parent / "sample_data" / "dataset.csv"
DEFAULT_LOG = Path(__file__).parent / "outputs" / "qa_log.json"
MAX_RETRIES = 1


def load_log(log_path: Path) -> list[dict]:
    """Load existing Q&A log entries from disk."""
    if log_path.exists():
        with open(log_path, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_log(log_path: Path, entries: list[dict]) -> None:
    """Save Q&A log entries to disk."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False, default=str)


def answer_question(
    df,
    schema: str,
    question: str,
    *,
    verbose: bool = True,
) -> dict:
    """Generate code, execute with retry, return Q&A record."""
    try:
        model_info = get_model_info()
    except Exception:
        model_info = {"provider": "unknown", "model": "unknown"}

    code = generate_code(schema, question)
    if verbose:
        print("\n--- Generated code ---")
        print(code)
        print("--- Executing ---\n")

    for attempt in range(MAX_RETRIES + 1):
        try:
            _, formatted = execute_code(code, df)
            record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "question": question,
                "code": code,
                "result": formatted,
                "status": "success",
                "model": model_info.get("model", "unknown"),
                "provider": model_info.get("provider", "unknown"),
            }
            if verbose:
                print("--- Result ---")
                print(formatted)
            return record
        except CodeExecutionError as exc:
            if attempt < MAX_RETRIES:
                if verbose:
                    print(f"Execution failed: {exc}. Retrying with error feedback...\n")
                code = generate_code(
                    schema,
                    question,
                    error=str(exc),
                    previous_code=exc.code,
                )
                if verbose:
                    print("--- Retry code ---")
                    print(code)
                    print("--- Executing ---\n")
            else:
                record = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "question": question,
                    "code": exc.code,
                    "result": None,
                    "status": "error",
                    "error": str(exc),
                    "model": model_info.get("model", "unknown"),
                    "provider": model_info.get("provider", "unknown"),
                }
                if verbose:
                    print(f"Failed after retry: {exc}")
                return record

    raise RuntimeError("Unexpected execution loop exit")


def run_interactive(dataset_path: Path, log_path: Path) -> None:
    """Run the agent in interactive CLI mode."""
    df = load_dataset(dataset_path)
    schema = build_schema_summary(df)
    log = load_log(log_path)

    print(f"\n{'='*60}")
    print(f"  CSV Q&A Agent — Loaded: {dataset_path.name}")
    print(f"  {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"{'='*60}")
    print("Ask questions about the data. Type 'quit' or 'exit' to stop.\n")

    while True:
        try:
            question = input("Question> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not question:
            continue
        if question.lower() in ("quit", "exit", "q"):
            print("Goodbye.")
            break

        record = answer_question(df, schema, question)
        log.append(record)
        save_log(log_path, log)
        print(f"\n(Saved to {log_path})\n")


def run_single(question: str, dataset_path: Path, log_path: Path, *, quiet: bool) -> dict:
    """Run a single question and return the result record."""
    df = load_dataset(dataset_path)
    schema = build_schema_summary(df)
    record = answer_question(df, schema, question, verbose=not quiet)

    if not quiet:
        log = load_log(log_path)
        log.append(record)
        save_log(log_path, log)

    return record


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CSV/Data Q&A Agent — ask plain-English questions, get computed answers."
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=DEFAULT_DATASET,
        help="Path to CSV, Excel, JSON, or TSV dataset",
    )
    parser.add_argument(
        "--log",
        type=Path,
        default=DEFAULT_LOG,
        help="Path to Q&A log JSON file",
    )
    parser.add_argument(
        "-q",
        "--question",
        type=str,
        help="Single question (non-interactive mode)",
    )
    parser.add_argument(
        "--no-log",
        action="store_true",
        help="Do not append to qa_log.json (use with -q)",
    )
    args = parser.parse_args()

    if not args.data.exists():
        print(f"Error: dataset not found at {args.data}", file=sys.stderr)
        sys.exit(1)

    if args.question:
        record = run_single(
            args.question,
            args.data,
            args.log,
            quiet=args.no_log,
        )
        if args.no_log:
            print(json.dumps(record, indent=2))
        sys.exit(0 if record["status"] == "success" else 1)

    run_interactive(args.data, args.log)


if __name__ == "__main__":
    main()
