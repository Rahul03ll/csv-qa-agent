"""Populate qa_log.json with computed answers (no API required).

Uses representative pandas code for each test question to demonstrate
the generate-code → execute → log pipeline. Run run_tests.py with
an API key for live LLM-generated code.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from code_executor import execute_code
from data_loader import load_dataset

DATASET = Path(__file__).parent / "sample_data" / "dataset.csv"
LOG = Path(__file__).parent / "outputs" / "qa_log.json"

QUESTIONS_AND_CODE = [
    (
        "What is the rating of Biryani Blues?",
        'result = df.loc[df["name"] == "Biryani Blues", "rating"].iloc[0]',
    ),
    (
        "How many restaurants in Mumbai have online ordering?",
        'result = len(df[(df["city"] == "Mumbai") & (df["online_order"] == "Yes")])',
    ),
    (
        "What is the average rating for each cuisine type? Sort from highest to lowest.",
        'result = df.groupby("cuisine")["rating"].mean().sort_values(ascending=False)',
    ),
    (
        "Which 5 restaurants have the highest number of votes? Show name, city, and votes.",
        'result = df.nlargest(5, "votes")[["name", "city", "votes"]]',
    ),
    (
        "How many restaurants were listed each month? Show as a table.",
        'df["listed_date"] = pd.to_datetime(df["listed_date"])\nresult = df.groupby(df["listed_date"].dt.to_period("M")).size().reset_index(name="count")',
    ),
    (
        "What is the average cost for two among restaurants rated 4.5 or above?",
        'result = df[df["rating"] >= 4.5]["cost_for_two"].mean()',
    ),
    (
        "Which city has the most restaurants and how many?",
        'counts = df["city"].value_counts()\nresult = f"{counts.index[0]} with {counts.iloc[0]} restaurants"',
    ),
    (
        "What is the cheapest restaurant (lowest cost_for_two) and where is it located?",
        'row = df.loc[df["cost_for_two"].idxmin()]\nresult = f"{row[\'name\']} in {row[\'city\']}, {row[\'area\']} (₹{row[\'cost_for_two\']} for two)"',
    ),
    (
        "How many restaurants offer both online ordering and table booking?",
        'result = len(df[(df["online_order"] == "Yes") & (df["book_table"] == "Yes")])',
    ),
    (
        "What is the total number of votes for all North Indian restaurants?",
        'result = df[df["cuisine"] == "North Indian"]["votes"].sum()',
    ),
    (
        "Which area (neighborhood) has the most restaurants? Show the top 5.",
        'result = df["area"].value_counts().head(5)',
    ),
    (
        "How many restaurants are in each restaurant_type category?",
        'result = df["restaurant_type"].value_counts()',
    ),
    (
        "What is the average rating for each cost_category (Budget, Mid-range, Premium)?",
        'result = df.groupby("cost_category")["rating"].mean().sort_values(ascending=False)',
    ),
    (
        "Which cuisine has the highest average cost_for_two? Show top 5 cuisines.",
        'result = df.groupby("cuisine")["cost_for_two"].mean().sort_values(ascending=False).head(5)',
    ),
    (
        "For each city, what percentage of restaurants have online ordering?",
        'grouped = df.groupby("city")["online_order"].apply(lambda x: (x == "Yes").mean() * 100).round(1)\nresult = grouped.sort_values(ascending=False)',
    ),
]


def main() -> None:
    df = load_dataset(DATASET)
    log = []

    for question, code in QUESTIONS_AND_CODE:
        try:
            _, formatted = execute_code(code, df)
            log.append(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "question": question,
                    "code": code,
                    "result": formatted,
                    "status": "success",
                    "source": "sample_log (representative code; use run_tests.py for LLM-generated code)",
                }
            )
            print(f"OK: {question}")
        except Exception as e:
            log.append(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "question": question,
                    "code": code,
                    "result": None,
                    "status": "error",
                    "error": str(e),
                    "source": "sample_log",
                }
            )
            print(f"FAIL: {question} -> {e}")

    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False, default=str)

    successes = sum(1 for e in log if e["status"] == "success")
    print(f"\nWrote {len(log)} entries ({successes} success) to {LOG}")


if __name__ == "__main__":
    main()
