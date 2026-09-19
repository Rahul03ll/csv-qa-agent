"""Run a batch of test questions and save results to qa_log.json.

Requires an LLM API key (GROQ_API_KEY or ANTHROPIC_API_KEY) in .env.
"""

import json
import sys
from pathlib import Path

from app import DEFAULT_DATASET, DEFAULT_LOG, answer_question, load_log, save_log
from data_loader import build_schema_summary, load_dataset

TEST_QUESTIONS = [
    # Simple lookup
    "What is the rating of Biryani Blues?",
    # Filter + count
    "How many restaurants in Mumbai have online ordering?",
    # Groupby / aggregate
    "What is the average rating for each cuisine type? Sort from highest to lowest.",
    # Sort / top-N
    "Which 5 restaurants have the highest number of votes? Show name, city, and votes.",
    # Trend over time
    "How many restaurants were listed each month? Show as a table.",
    # Multi-condition filter
    "What is the average cost for two among restaurants rated 4.5 or above?",
    # Count by category
    "Which city has the most restaurants and how many?",
    # Min/max
    "What is the cheapest restaurant (lowest cost_for_two) and where is it located?",
    # Boolean filter
    "How many restaurants offer both online ordering and table booking?",
    # Filtered aggregation
    "What is the total number of votes for all North Indian restaurants?",
    # New columns — area
    "Which area (neighborhood) has the most restaurants? Show the top 5.",
    # New columns — restaurant type
    "How many restaurants are in each restaurant_type category?",
    # New columns — cost category
    "What is the average rating for each cost_category (Budget, Mid-range, Premium)?",
    # Cross-column analysis
    "Which cuisine has the highest average cost_for_two? Show top 5 cuisines.",
    # Complex query
    "For each city, what percentage of restaurants have online ordering?",
]


def main() -> None:
    dataset = DEFAULT_DATASET
    log_path = DEFAULT_LOG

    if not dataset.exists():
        print(f"Dataset not found: {dataset}", file=sys.stderr)
        sys.exit(1)

    df = load_dataset(dataset)
    schema = build_schema_summary(df)
    log: list[dict] = []

    print(f"Running {len(TEST_QUESTIONS)} test questions on {dataset.name}...")
    print(f"Dataset: {df.shape[0]} rows x {df.shape[1]} columns\n")

    for i, question in enumerate(TEST_QUESTIONS, 1):
        print(f"[{i}/{len(TEST_QUESTIONS)}] {question}")
        try:
            record = answer_question(df, schema, question, verbose=True)
            log.append(record)
            save_log(log_path, log)
            status = record["status"]
            print(f"  -> {status}\n")
        except Exception as exc:
            print(f"  -> FAILED: {exc}\n", file=sys.stderr)
            log.append(
                {
                    "question": question,
                    "code": None,
                    "result": None,
                    "status": "error",
                    "error": str(exc),
                }
            )
            save_log(log_path, log)

    successes = sum(1 for e in log if e.get("status") == "success")
    print(f"\nDone. {successes}/{len(TEST_QUESTIONS)} succeeded. Log: {log_path}")


if __name__ == "__main__":
    main()
