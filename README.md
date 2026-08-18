# CSV / Data Q&A Agent

A Python agent that takes a CSV or Excel dataset and a plain-English question, then produces a **computed** answer by generating and executing real pandas code — never guessing numbers.

Built for the Rooman AI Challenge — Category 2: Data & Documents (Advanced).

## How It Works (Anti-Hallucination)

The LLM does **not** answer questions directly. Instead:

```
┌──────────┐    ┌───────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Upload  │───▶│ Summarize │───▶│ Generate │───▶│ Execute  │───▶│  Return  │
│  Dataset │    │  Schema   │    │  Code    │    │  Locally │    │ Result + │
│          │    │  (only)   │    │ (pandas) │    │ (safe)   │    │  Code    │
└──────────┘    └───────────┘    └──────────┘    └──────────┘    └──────────┘
```

1. **Load data** — The dataset is loaded into a pandas DataFrame locally.
2. **Summarize schema** — Only column names, dtypes, stats, and 5 sample rows are sent to the LLM (not the full dataset).
3. **Generate code** — The LLM writes pandas code that assigns the answer to a variable named `result`.
4. **Execute locally** — The code runs in a restricted, sandboxed namespace with timeout and import blocking.
5. **Show receipts** — Both the generated code and the computed result are displayed and logged.

If execution fails, the error is sent back to the LLM for **one automatic retry** before giving up.

This generate-code → execute → return pattern ensures every number comes from actual computation on your data.

## Project Structure

```
csv-qa-agent/
├── app.py                  # CLI entry point (interactive or single question)
├── streamlit_app.py        # Premium web UI (Streamlit)
├── data_loader.py          # Load CSV/XLSX/JSON/TSV, build schema summary
├── llm_client.py           # Groq/Anthropic API wrapper, code extraction
├── code_executor.py        # Sandboxed exec with timeout & import blocking
├── prompts.py              # System prompt templates with few-shot examples
├── run_tests.py            # Batch runner for 15 test questions (live LLM)
├── populate_sample_log.py  # Populate qa_log.json without API key
├── generate_sample_data.py # Generate the 100-row sample dataset
├── sample_data/
│   └── dataset.csv         # Sample restaurant dataset (100 rows, 12 columns)
├── outputs/
│   └── qa_log.json         # Q&A transcript (deliverable)
├── tests/
│   ├── test_data_loader.py
│   ├── test_code_executor.py
│   └── test_prompts.py
├── .env.example
├── requirements.txt
└── README.md
```

## Setup

### 1. Clone and install

```bash
cd csv-qa-agent
pip install -r requirements.txt
```

### 2. Configure API key

```bash
cp .env.example .env
```

Add a **Groq** or **Anthropic** key to `.env`:

```
GROQ_API_KEY=gsk_...
# or
ANTHROPIC_API_KEY=sk-ant-...
```

| Provider | Default Model | Get a Key |
|----------|--------------|-----------|
| **Groq** (default) | `meta-llama/llama-4-scout-17b-16e-instruct` | [console.groq.com](https://console.groq.com/) |
| **Anthropic** | `claude-sonnet-4-20250514` | [console.anthropic.com](https://console.anthropic.com/) |

Groq is used automatically when `GROQ_API_KEY` is set. Set `LLM_PROVIDER=anthropic` to force Anthropic.

### 3. Generate sample data (optional)

The repo includes `sample_data/dataset.csv`. To regenerate:

```bash
python generate_sample_data.py
```

## Usage

### 🌐 Web UI (Streamlit)

```bash
streamlit run streamlit_app.py
```

Features:
- Drag-and-drop CSV/Excel/JSON upload
- Chat-style Q&A interface
- Interactive data preview with statistics
- Expandable code blocks showing generated pandas code
- Q&A history sidebar
- Dark-mode glassmorphism design

### 💻 Interactive CLI

```bash
python app.py
```

```
Question> What is the average rating in Mumbai?
```

Type `quit` or `exit` to stop. Each Q&A is appended to `outputs/qa_log.json`.

### Single question

```bash
python app.py -q "Which city has the most restaurants?"
```

### Custom dataset

```bash
python app.py --data path/to/your/file.csv
python app.py --data path/to/data.xlsx -q "Your question here"
```

### Run all test questions (live LLM)

```bash
python run_tests.py
```

Runs 15 predefined questions spanning lookup, filter, groupby, sort, time trends, and cross-column analysis. Results are saved to `outputs/qa_log.json`.

### Populate sample log (no API key)

```bash
python populate_sample_log.py
```

Runs the same 15 questions using representative pandas code and the same execution pipeline. Useful for verifying setup without an API key.

### Run unit tests

```bash
python -m pytest tests/ -v
```

## Sample Dataset

`sample_data/dataset.csv` contains **100 restaurants** across 8 Indian cities with 12 columns:

| Column | Description |
|--------|-------------|
| `name` | Restaurant name |
| `city` | City (Bangalore, Mumbai, Delhi, Chennai, Hyderabad, Pune, Kolkata, Jaipur) |
| `area` | Neighborhood / locality |
| `cuisine` | Cuisine type (20 varieties) |
| `restaurant_type` | Dine-out / Delivery / Café / Takeaway |
| `rating` | Rating (2.5–4.9) |
| `cost_for_two` | Average cost for two (INR) |
| `votes` | Number of user votes |
| `online_order` | Yes/No |
| `book_table` | Yes/No |
| `cost_category` | Budget / Mid-range / Premium |
| `listed_date` | Date listed (2023–2024) |

## Test Questions (15)

The batch runner covers these question types:

1. **Simple lookup** — "What is the rating of Biryani Blues?"
2. **Filter + count** — "How many restaurants in Mumbai have online ordering?"
3. **Groupby / aggregate** — "What is the average rating for each cuisine type?"
4. **Sort / top-N** — "Which 5 restaurants have the highest number of votes?"
5. **Trend over time** — "How many restaurants were listed each month?"
6. **Multi-condition filter** — "Average cost for two among restaurants rated 4.5+?"
7. **Count by category** — "Which city has the most restaurants?"
8. **Min/max lookup** — "What is the cheapest restaurant?"
9. **Boolean filter** — "How many offer both online ordering and table booking?"
10. **Filtered aggregation** — "Total votes for all North Indian restaurants?"
11. **Area analysis** — "Which neighborhood has the most restaurants?"
12. **Type breakdown** — "How many restaurants per restaurant_type?"
13. **Category comparison** — "Average rating by cost_category?"
14. **Cuisine economics** — "Which cuisine has the highest average cost_for_two?"
15. **Percentage calculation** — "For each city, what % have online ordering?"

See `outputs/qa_log.json` for the agent's answers, generated code, and timestamps.

## Security & Safety Features

| Feature | Description |
|---------|-------------|
| **AST import blocking** | Dangerous imports (`os`, `sys`, `subprocess`, etc.) are blocked before execution |
| **Execution timeout** | 10-second limit prevents infinite loops or expensive operations |
| **Restricted namespace** | Only `df`, `pd`, `np`, `plt`, and builtins are available |
| **DataFrame copy** | Generated code operates on a copy — original data is never mutated |
| **Deterministic output** | `temperature=0` for consistent code generation |

## Design Choices

- **Dual-provider support** — Groq (fast, free tier) or Anthropic (strong at pandas), auto-detected from env vars.
- **Schema-only prompts** — keeps token usage low and prevents the model from memorizing wrong values.
- **Few-shot examples** — system prompt includes example Q&A pairs for higher accuracy.
- **JSON log as deliverable** — transparent audit trail of every question, code snippet, result, and model used.
- **Streamlit web UI** — drag-and-drop upload + chat interface for non-CLI users.

## Tradeoffs & Future Improvements

| Improvement | Why |
|-------------|-----|
| **Chart generation** | Return matplotlib/plotly figures for visual questions |
| **Multi-file joins** | Load and join multiple CSVs for richer analysis |
| **Smarter retry logic** | Multiple retries with escalating hints; validate code AST before exec |
| **Result caching** | Cache `(question, schema_hash) → result` to avoid repeat API calls |
| **Stronger sandbox** | Use subprocess with `--jail` or container isolation |
| **Conversation memory** | Multi-turn chat with context from previous Q&A pairs |
| **Auto-visualization** | Detect when a chart would be helpful and generate one automatically |

## Requirements

- Python 3.11+
- Groq API key (free) or Anthropic API key
- Dependencies: see `requirements.txt`

## License

MIT — built for the Rooman AI Challenge.
