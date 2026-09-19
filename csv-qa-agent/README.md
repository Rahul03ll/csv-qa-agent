# 📊 CSV / Tabular Data Q&A Agent

> **Zero-hallucination conversational tabular analytics powered by deterministic pandas code execution and Groq high-speed LLM inference.**

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Groq](https://img.shields.io/badge/Groq-Ultra--Fast%20Inference-f55036.svg?logo=groq&logoColor=white)](https://console.groq.com/)
[![Pandas](https://img.shields.io/badge/pandas-2.0%2B-150458.svg?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B.svg?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/tests-66%20passed-success.svg)](https://pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Author](https://img.shields.io/badge/author-Rahul%20Roy-blueviolet)](https://github.com/Rahul03ll)

---

## 🎯 Overview

The **CSV / Data Q&A Agent** is an enterprise-grade tabular question-answering agent developed for the **Rooman AI Challenge — Category 2: Data & Documents (Advanced)**. 

Traditional LLMs frequently hallucinate counts, aggregations, percentages, and financial metrics when asked about tabular data. This project implements an **Anti-Hallucination Architecture**: the language model never attempts direct arithmetic. Instead, it inspects a compact metadata summary of the schema and writes executable `pandas` code that runs inside a hardened, sandboxed local interpreter.

---

## 🛡️ Anti-Hallucination Architecture

```
┌─────────────────┐       ┌────────────────────────┐       ┌──────────────────────┐
│  User Dataset   │ ────▶ │  Metadata Extraction   │ ────▶ │   LLM Code Generator │
│ (CSV/XLSX/JSON) │       │  - Shape, Dtypes       │       │  - Temperature = 0   │
└─────────────────┘       │  - Stats, Unique Vals  │       │  - Assigns `result`  │
                          │  (No Raw Data Leaked!) │       └──────────┬───────────┘
                          └────────────────────────┘                  │ Python Code
                                                                      ▼
┌─────────────────┐       ┌────────────────────────┐       ┌──────────────────────┐
│ Verified Output │ ◀──── │ Transparent Audit Log  │ ◀──── │   Security Sandbox   │
│ - Exact Result  │       │ - outputs/qa_log.json  │       │  - AST Import Blocks │
│ - Verifiable    │       │ - Timestamps, Provider │       │  - Builtin Lockdown  │
│   Pandas Code   │       │ - Full Code Receipts   │       │  - 10s Timeout Limit │
└─────────────────┘       └────────────────────────┘       └──────────────────────┘
```

### Key Architectural Tenets

1. **Schema-Only Context Window**: Raw dataset rows never leave your machine. Only schema metadata (column names, inferred dtypes, null counts, min/max/mean distributions, and top categorical frequencies) is passed into the prompt.
2. **Deterministic Code Generation**: Prompted with strict temperature (`0.0`) and few-shot examples to output strictly validated Python code assigning an answer to `result`.
3. **Hardened Multi-Layer Sandbox**:
   - **AST Verification**: Proactively blocks malicious modules (`os`, `sys`, `subprocess`, `shutil`, `socket`, `ctypes`, `requests`, `builtins`, `tempfile`, `io`, etc.), dangerous builtins (`open()`, `eval()`, `exec()`, `compile()`, `__import__()`), dunder escapes (`__subclasses__`, `__globals__`), and filesystem write methods (`to_csv()`, `to_pickle()`, `read_pickle()`).
   - **Runtime Namespace Lockdown**: Replaces raw `__builtins__` with a filtered dictionary preventing runtime builtin evaluation evasion.
   - **Timeout Protection**: Thread-based 10-second timeout halts infinite loops or runaway operations.
   - **Immutability**: Generated code executes on a deep copy (`df.copy()`), preventing data corruption.
   - **Automatic Error Recovery**: If execution encounters an error, a feedback loop provides the traceback to the LLM for one targeted self-correction retry before termination.
4. **Complete Audit Trail**: Every Q&A interaction records the user prompt, generated code, computed result, latency timestamp, and active model to `outputs/qa_log.json`.

---

## 📁 Repository Structure

```
csv-qa-agent/
├── app.py                    # Root CLI entrypoint runner
├── streamlit_app.py          # Root Streamlit entrypoint runner
├── pytest.ini                # Pytest configuration and pythonpath discovery
├── requirements.txt          # Root dependency specification (pip install -r requirements.txt)
├── .env.example              # Sample environment variables (GROQ_API_KEY, ANTHROPIC_API_KEY)
├── .gitignore                # Comprehensive Python, environment & cache ignore patterns
├── LICENSE                   # Standard MIT License attributed to Rahul Roy (2025-2026)
├── README.md                 # Project architecture, benchmarks, and quickstart documentation
└── csv-qa-agent/
    ├── app.py                # Dual-mode CLI (interactive REPL & single-shot question runner)
    ├── streamlit_app.py      # Premium glassmorphism dark-mode web application
    ├── data_loader.py        # Multi-format ingestion (CSV/TSV/Excel/JSON), auto-date parser & schema builder
    ├── llm_client.py         # Multi-provider client (Groq / Anthropic) with code block & reasoning extractor
    ├── code_executor.py      # Hardened AST sandbox, timeout manager & result formatter
    ├── prompts.py            # Few-shot system prompts, retry instructions & schema formatting
    ├── run_tests.py          # Automated batch test runner evaluating 15 live queries with LLM
    ├── populate_sample_log.py# Deterministic offline evaluation & log builder (no API key required)
    ├── generate_sample_data.py# 100-row realistic Indian restaurant multi-city dataset generator
    ├── requirements.txt      # Pinned production dependencies
    ├── sample_data/
    │   └── dataset.csv       # Sample 100-row, 12-column benchmark dataset
    ├── outputs/
    │   └── qa_log.json       # Structured Q&A audit log & benchmark receipts
    └── tests/
        ├── test_code_executor.py  # 34 unit tests for sandboxing, timeouts, AST blocks & execution
        ├── test_data_loader.py    # 15 unit tests for format ingestion, booleans & schema summary
        ├── test_llm_client.py     # 9 unit tests for code extraction & reasoning tag handling
        └── test_prompts.py        # 8 unit tests for prompt structure, placeholders & few-shots
```

---

## 🚀 Quickstart & Installation

### 1. Prerequisites

- Python **3.10+** (tested on Python 3.10 and 3.11)
- [Groq Cloud Account](https://console.groq.com/) (free high-speed API key) or [Anthropic Console](https://console.anthropic.com/)

### 2. Clone & Setup Virtual Environment

```bash
git clone https://github.com/Rahul03ll/csv-qa-agent.git
cd csv-qa-agent

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure API Credentials

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` with your API credentials:

```ini
# Recommended: Free & ultra-fast inference
GROQ_API_KEY=gsk_your_groq_api_key_here

# Optional: Anthropic Claude key
# ANTHROPIC_API_KEY=sk-ant-your_anthropic_api_key_here

# Provider selection: "groq" (default) or "anthropic"
# LLM_PROVIDER=groq

# Optional model override (defaults to openai/gpt-oss-20b on Groq)
# GROQ_MODEL=openai/gpt-oss-20b
```

---

## 🖥️ Usage

### 🌐 1. Interactive Web Application (Streamlit)

Launch the modern dark-mode dashboard with drag-and-drop file upload, expandable code receipts, data previews, and query history:

```bash
streamlit run streamlit_app.py
```

**Features**:
- 📁 Upload custom datasets (`.csv`, `.tsv`, `.xlsx`, `.xls`, `.json`) or test immediately with the preloaded 100-row sample dataset.
- 💬 Chat interface with typing indicators and real-time execution feedback.
- 🔍 Collapsible **"View generated code"** drawers for total transparency.
- 📊 Data preview tabs with interactive dataframe viewing, schema dtypes, and summary statistics (`describe(include='all')`).
- 📜 History sidebar displaying recent queries with execution status badges.

---

### 💻 2. Interactive CLI REPL

Run an interactive question-answering session directly in your terminal:

```bash
python app.py
```

```text
============================================================
  CSV Q&A Agent — Loaded: dataset.csv
  100 rows × 12 columns
============================================================
Ask questions about the data. Type 'quit' or 'exit' to stop.

Question> What is the average rating for each cuisine type? Sort from highest to lowest.

--- Generated code ---
result = df.groupby("cuisine")["rating"].mean().sort_values(ascending=False)
--- Executing ---

--- Result ---
cuisine
Rajasthani      4.800000
Korean          4.700000
Japanese        4.600000
Hyderabadi      4.550000
...

(Saved to outputs/qa_log.json)
```

---

### ⚡ 3. Single-Query CLI Mode

Execute one-off analytical queries headlessly:

```bash
python app.py -q "Which city has the highest average restaurant rating?"
```

Target custom datasets on the fly:

```bash
python app.py --data path/to/sales.xlsx -q "What was the total revenue in Q3?"
```

Output raw JSON results for downstream scripting:

```bash
python app.py --data dataset.csv -q "How many rows are in the dataset?" --no-log
```

---

### 🧪 4. Batch Benchmark & Test Verification

Run all **53 automated unit tests** (code executor sandbox, AST blockers, boolean/categorical schema summaries, prompt templates, and code extractors):

```bash
pytest tests/ -v
```

Execute the offline 15-query test suite (no API key required):

```bash
python populate_sample_log.py
```

Run live end-to-end evaluation against Groq/Anthropic for all 15 benchmark questions:

```bash
python run_tests.py
```

---

## 📊 Benchmark Dataset & Sample Queries

The included `sample_data/dataset.csv` contains 100 realistic Indian restaurant listings spanning 8 metropolitan cities with 12 heterogeneous attributes:

| Field | Type | Sample Values / Description |
|---|---|---|
| `name` | string | *Biryani Blues, Sushi Zen, Tandoor Express, Kebab King* |
| `city` | string | *Bangalore, Mumbai, Delhi, Chennai, Hyderabad, Pune, Kolkata, Jaipur* |
| `area` | string | *Koramangala, Bandra, Connaught Place, Banjara Hills* |
| `cuisine` | string | *North Indian, South Indian, Mughlai, Italian, Japanese, BBQ, Thai* |
| `restaurant_type` | string | *Dine-out, Delivery, Café, Takeaway* |
| `rating` | float | Float range from `2.5` to `4.9` |
| `cost_for_two` | integer | Realistic dining cost for two in INR (`₹150` – `₹3,000`) |
| `votes` | integer | User review counts (`50` to `5,000`) |
| `online_order` | string | *Yes* / *No* |
| `book_table` | string | *Yes* / *No* |
| `cost_category` | string | *Budget* (≤₹400), *Mid-range* (₹401–₹1000), *Premium* (>₹1000) |
| `listed_date` | datetime | Date format (`YYYY-MM-DD`) between Jan 2023 and Jul 2024 |

### The 15 Benchmark Query Categories

| # | Category | Natural Language Query | Generated Pandas Code |
|---|---|---|---|
| 1 | **Lookup** | "What is the rating of Biryani Blues?" | `result = df.loc[df["name"] == "Biryani Blues", "rating"].iloc[0]` |
| 2 | **Filter + Count** | "How many restaurants in Mumbai have online ordering?" | `result = len(df[(df["city"] == "Mumbai") & (df["online_order"] == "Yes")])` |
| 3 | **Groupby & Sort** | "Average rating by cuisine type, sorted highest to lowest?" | `result = df.groupby("cuisine")["rating"].mean().sort_values(ascending=False)` |
| 4 | **Top-N** | "Which 5 restaurants have the highest votes?" | `result = df.nlargest(5, "votes")[["name", "city", "votes"]]` |
| 5 | **Time Series** | "How many restaurants were listed each month?" | `df["listed_date"] = pd.to_datetime(df["listed_date"])`<br>`result = df.groupby(df["listed_date"].dt.to_period("M")).size().reset_index(name="count")` |
| 6 | **Multi-Filter** | "Average cost for two among restaurants rated 4.5+?" | `result = df[df["rating"] >= 4.5]["cost_for_two"].mean()` |
| 7 | **Categorical Max** | "Which city has the most restaurants and how many?" | `counts = df["city"].value_counts()`<br>`result = f"{counts.index[0]} with {counts.iloc[0]} restaurants"` |
| 8 | **Extrema Lookup**| "What is the cheapest restaurant and where is it located?" | `row = df.loc[df["cost_for_two"].idxmin()]`<br>`result = f"{row['name']} in {row['city']}, {row['area']} (₹{row['cost_for_two']})"` |
| 9 | **Boolean AND** | "How many restaurants offer both online ordering and table booking?" | `result = len(df[(df["online_order"] == "Yes") & (df["book_table"] == "Yes")])` |
| 10 | **Aggregation** | "Total number of votes for all North Indian restaurants?" | `result = df[df["cuisine"] == "North Indian"]["votes"].sum()` |
| 11 | **Top Areas** | "Which area (neighborhood) has the most restaurants?" | `result = df["area"].value_counts().head(5)` |
| 12 | **Frequency** | "How many restaurants in each restaurant_type?" | `result = df["restaurant_type"].value_counts()` |
| 13 | **Economic Segments** | "Average rating for each cost_category?" | `result = df.groupby("cost_category")["rating"].mean().sort_values(ascending=False)` |
| 14 | **Cross Analysis** | "Which cuisine has the highest average cost_for_two?" | `result = df.groupby("cuisine")["cost_for_two"].mean().sort_values(ascending=False).head(5)` |
| 15 | **Percentage Calculation** | "For each city, what percentage of restaurants have online ordering?" | `grouped = df.groupby("city")["online_order"].apply(lambda x: (x == "Yes").mean() * 100).round(1)`<br>`result = grouped.sort_values(ascending=False)` |

---

## 🔒 Security & Defense-in-Depth

| Threat Vector | Mitigation Strategy | Implementation |
|---|---|---|
| **Remote Code Execution (RCE)** | AST node inspection before compilation | `code_executor._check_imports` scans for blacklisted modules & dangerous functions |
| **System File Access** | Blocked builtins & I/O methods | Intercepts `open()`, `compile()`, `exec()`, `eval()`, `__import__()`, `df.to_csv()`, `to_pickle()`, and `pd.read_pickle()` |
| **Builtin Evasion Attacks** | Filtered runtime `__builtins__` dictionary | Custom `safe_builtins` strips execution builtins; AST blocks dunder references (`__subclasses__`, `__globals__`, `__builtins__`) |
| **Denial of Service (DoS)** | Threaded watchdog timer | `EXECUTION_TIMEOUT = 10` terminates execution if thread runtime exceeds 10s |
| **Data Poisoning / Mutation** | In-memory defensive cloning | `namespace["df"] = df.copy()` ensures the underlying dataset cannot be altered |
| **Model Hallucination** | Mathematical computation boundary | LLM is restricted to code synthesis; all arithmetic executed by pandas |
| **Crash Protection** | Type-safe schema serialization | Handles empty dataframes, boolean columns, and categoricals without KeyError |

---

## 👨‍💻 Author

**Rahul Roy**  
*Final-Year B.Tech in Computer Science & Engineering*  
KIIT University, Bhubaneswar, Odisha, India  

- **GitHub**: [@Rahul03ll](https://github.com/Rahul03ll)
- **LinkedIn**: [Rahul Roy](https://linkedin.com/in/rahul-roy-362a12256)
- **Email**: rahulroy2259@gmail.com

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.  
Copyright (c) 2025–2026 **Rahul Roy**.
