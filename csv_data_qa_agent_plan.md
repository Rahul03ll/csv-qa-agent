# CSV / Data Q&A Agent — Build Plan
Rooman AI Challenge — Category 2: Data & Documents (Advanced)

## 1. The One Job
"My agent takes a CSV/Excel dataset and a plain-English question, and produces a correct, computed answer — showing the exact figure or table behind it, never a guess."

## 2. Why This Agent
- Extends your Zomato Data Analytics Dashboard (Pandas, SQLite, Streamlit, Plotly) rather than starting cold — dataset loading, cleaning, and insight generation are things you've already built once.
- "Advanced" difficulty, but the generate-code → execute → return pattern is a well-documented approach, not an open research problem.
- Directly demonstrates backend engineering discipline: don't trust the LLM's arithmetic — make it write and run real code, then show the receipts.

## 3. Stack
- Python 3.11+
- Anthropic Claude API (Sonnet or Haiku) — swap for OpenAI/Groq if you prefer
- `pandas`, `openpyxl` (for .xlsx), `python-dotenv`
- Optional: Streamlit for a UI — skip if time is short, a CLI satisfies the rubric

## 4. Suggested File Structure
```
csv-qa-agent/
├── app.py              # CLI entry point (loop: ask → answer)
├── data_loader.py       # load CSV/XLSX, build schema summary
├── llm_client.py         # wraps Claude API call, extracts code block
├── code_executor.py     # sandboxed exec of generated pandas code
├── prompts.py            # system prompt template
├── sample_data/
│   └── dataset.csv
├── outputs/
│   └── qa_log.json       # saved Q&A transcript — this IS your deliverable
├── .env.example
├── requirements.txt
└── README.md
```

## 5. Build Steps

1. **Setup** — `pip install anthropic pandas openpyxl python-dotenv`. Store `ANTHROPIC_API_KEY` in `.env`.
2. **data_loader.py** — load the file with `pandas.read_csv`/`read_excel`. Produce a compact schema string: column names, dtypes, and 3–5 sample rows. Don't dump the full dataset into the prompt — summarize it, and let the generated code query the real dataframe.
3. **prompts.py** — system prompt: *"You are a data analyst. Given this dataframe schema, write pandas code that computes the answer to the user's question. Assign the final answer to a variable named `result`. Return ONLY a Python code block, no explanation."*
4. **llm_client.py** — send schema + question to Claude, extract the code block from the response (strip markdown fences).
5. **code_executor.py** — `exec()` the code in a restricted namespace containing only `df` and `pd`. Catch exceptions; on failure, feed the error back to the LLM for one retry before giving up.
6. **app.py** — loop: prompt for a question → get code → execute → print both `result` and the code that produced it. This transparency is exactly what the "avoid hallucination" deliverable asks for.
7. **Logging** — after each Q&A, append `{question, code, result}` to `outputs/qa_log.json`. This becomes your "8–10 questions with answers" deliverable directly.
8. **Test data** — reuse a version of your Zomato dataset, or grab any public CSV (sales, sports stats, weather) with enough columns to support groupby/filter/aggregate questions.
9. **Write 8–10 test questions** spanning types: simple lookup, filter, groupby/aggregate, sort/top-N, trend-over-time. Run them all, save the log.
10. **README** — install steps, `.env` setup, how to run end-to-end, and a dedicated "How numbers are computed" section (a required deliverable for this specific agent — explain the generate-code-then-execute loop).
11. **Tradeoff notes** — what you'd add with more time: chart generation (matplotlib), multi-file joins, smarter retry logic, result caching.

## 6. Deliverables Checklist (Agent-Specific)
- [ ] Sample dataset (CSV/Excel)
- [ ] 8–10 questions with the agent's answers
- [ ] Note explaining how numbers are computed (anti-hallucination)

## 7. Standard Submission Checklist (All Agents)
- [ ] Public GitHub repo — all commits within the 24-hour window
- [ ] README: install, API key config, run instructions, design choices
- [ ] A runnable agent
- [ ] Sample inputs and outputs
- [ ] Tradeoff notes

## 8. Scoring Reminder

| Criterion | Points |
|---|---|
| Working end-to-end agent | 30 |
| Approach & method | 25 |
| Code quality / organization | 20 |
| README clarity and reproducibility | 15 |
| Tradeoff notes and reasoning | 10 |

## 9. Rough Time Budget (24 hrs)
- Hrs 0–2: setup, `data_loader.py`, `prompts.py`, one manual test question
- Hrs 2–6: `llm_client.py` + `code_executor.py` + retry loop working end-to-end
- Hrs 6–8: `app.py` loop, logging to `qa_log.json`
- Hrs 8–10: run all 8–10 test questions, fix edge cases
- Hrs 10–12: README + tradeoff notes
- Remainder: buffer, optional Streamlit UI, polish, commit hygiene
