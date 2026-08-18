"""Streamlit web UI for the CSV/Data Q&A Agent.

Premium dark-mode interface with:
- Drag-and-drop CSV/Excel/JSON upload
- Chat-style Q&A with expandable code blocks
- Interactive data preview
- Q&A history sidebar
- Chart rendering support
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

from code_executor import CodeExecutionError, execute_code
from data_loader import build_schema_summary, load_dataset

# ---------------------------------------------------------------------------
# Page config & custom CSS
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="CSV Q&A Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Global */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Main container glassmorphism */
.main .block-container {
    max-width: 1100px;
    padding-top: 2rem;
}

/* Dark card style */
div[data-testid="stExpander"] {
    background: rgba(30, 30, 46, 0.6);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    margin-bottom: 0.5rem;
}

/* Chat messages */
.stChatMessage {
    border-radius: 12px !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
}

/* Success metric cards */
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(168,85,247,0.15));
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 12px;
    padding: 1rem;
}

/* Upload area */
div[data-testid="stFileUploader"] {
    border: 2px dashed rgba(99,102,241,0.4) !important;
    border-radius: 12px !important;
    background: rgba(30, 30, 46, 0.4) !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%);
    border-right: 1px solid rgba(255,255,255,0.06);
}

section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #a78bfa;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.5rem !important;
    transition: all 0.3s ease !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #818cf8, #a78bfa) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 15px rgba(99,102,241,0.4) !important;
}

/* Code blocks */
code {
    background: rgba(30, 30, 46, 0.8) !important;
    border-radius: 6px !important;
}

/* Status badges */
.status-success {
    background: linear-gradient(135deg, #059669, #10b981);
    color: white;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
}
.status-error {
    background: linear-gradient(135deg, #dc2626, #ef4444);
    color: white;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
}

/* Animated gradient header */
.gradient-header {
    background: linear-gradient(135deg, #6366f1, #8b5cf6, #a78bfa, #6366f1);
    background-size: 300% 300%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: gradient-shift 4s ease infinite;
    font-size: 2.2rem;
    font-weight: 700;
    margin-bottom: 0;
}
@keyframes gradient-shift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* Subtle card borders */
.glass-card {
    background: rgba(30, 30, 46, 0.5);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}

/* Dataframe styling */
div[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.08);
}

/* Tab styling */
button[data-baseweb="tab"] {
    font-weight: 500 !important;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

DEFAULT_DATASET = Path(__file__).parent / "sample_data" / "dataset.csv"
LOG_PATH = Path(__file__).parent / "outputs" / "qa_log.json"

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "df" not in st.session_state:
    st.session_state.df = None
if "schema" not in st.session_state:
    st.session_state.schema = None
if "qa_log" not in st.session_state:
    st.session_state.qa_log = []
if "dataset_name" not in st.session_state:
    st.session_state.dataset_name = None


def _load_qa_log() -> list[dict]:
    if LOG_PATH.exists():
        with open(LOG_PATH, encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_qa_log(entries: list[dict]) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False, default=str)


def _try_generate_code(schema: str, question: str, error=None, previous_code=None) -> str:
    """Generate code via LLM, handling import errors gracefully."""
    from llm_client import generate_code
    return generate_code(schema, question, error=error, previous_code=previous_code)


def _get_model_info() -> dict:
    try:
        from llm_client import get_model_info
        return get_model_info()
    except Exception:
        return {"provider": "unknown", "model": "unknown"}


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<p class="gradient-header">📊 CSV Q&A</p>', unsafe_allow_html=True)
    st.caption("Ask plain-English questions, get computed answers")

    st.divider()

    # File upload
    st.markdown("### 📁 Dataset")
    uploaded = st.file_uploader(
        "Upload CSV, Excel, or JSON",
        type=["csv", "xlsx", "xls", "json", "tsv"],
        help="Drag and drop your dataset here",
    )

    use_sample = st.button("📦 Use Sample Dataset", use_container_width=True)

    if uploaded:
        try:
            suffix = Path(uploaded.name).suffix.lower()
            if suffix == ".csv":
                df = pd.read_csv(uploaded)
            elif suffix == ".tsv":
                df = pd.read_csv(uploaded, sep="\t")
            elif suffix in (".xlsx", ".xls"):
                df = pd.read_excel(uploaded)
            elif suffix == ".json":
                df = pd.read_json(uploaded)
            else:
                st.error(f"Unsupported format: {suffix}")
                df = None

            if df is not None:
                # Auto-parse dates
                for col in df.select_dtypes(include=["object"]).columns:
                    if any(kw in col.lower() for kw in ("date", "time")):
                        try:
                            df[col] = pd.to_datetime(df[col], format="mixed")
                        except (ValueError, TypeError):
                            pass
                st.session_state.df = df
                st.session_state.schema = build_schema_summary(df)
                st.session_state.dataset_name = uploaded.name
                st.success(f"Loaded **{uploaded.name}**")
        except Exception as e:
            st.error(f"Failed to load: {e}")

    if use_sample and DEFAULT_DATASET.exists():
        df = load_dataset(DEFAULT_DATASET)
        st.session_state.df = df
        st.session_state.schema = build_schema_summary(df)
        st.session_state.dataset_name = DEFAULT_DATASET.name
        st.success(f"Loaded **{DEFAULT_DATASET.name}**")

    # Model info
    st.divider()
    st.markdown("### 🤖 Model")
    info = _get_model_info()
    st.markdown(f"**Provider:** `{info['provider']}`")
    st.markdown(f"**Model:** `{info['model']}`")

    # History
    st.divider()
    st.markdown("### 📜 Q&A History")
    log = _load_qa_log()
    if log:
        for i, entry in enumerate(reversed(log[-10:])):
            status_badge = "✅" if entry.get("status") == "success" else "❌"
            q_short = entry.get("question", "")[:50]
            with st.expander(f"{status_badge} {q_short}...", expanded=False):
                st.markdown(f"**Q:** {entry.get('question')}")
                if entry.get("result"):
                    st.code(str(entry["result"])[:500], language="text")
                if entry.get("code"):
                    st.code(entry["code"], language="python")
    else:
        st.caption("No history yet. Ask a question!")

    if log:
        if st.button("🗑️ Clear History", use_container_width=True):
            _save_qa_log([])
            st.session_state.qa_log = []
            st.rerun()

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
st.markdown('<p class="gradient-header">CSV Q&A Agent</p>', unsafe_allow_html=True)
st.markdown(
    "Upload a dataset and ask questions in plain English. "
    "The agent generates & executes real pandas code — never guesses.",
    unsafe_allow_html=True,
)

# Dataset preview
if st.session_state.df is not None:
    df = st.session_state.df

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Rows", f"{df.shape[0]:,}")
    col2.metric("Columns", f"{df.shape[1]}")
    col3.metric("Numeric Cols", f"{len(df.select_dtypes(include='number').columns)}")
    col4.metric("Text Cols", f"{len(df.select_dtypes(include='object').columns)}")

    # Data preview tabs
    tab_preview, tab_schema, tab_stats = st.tabs(["📋 Data Preview", "🏗️ Schema", "📊 Statistics"])

    with tab_preview:
        st.dataframe(df.head(20), use_container_width=True, height=350)

    with tab_schema:
        st.code(st.session_state.schema, language="text")

    with tab_stats:
        st.dataframe(df.describe(include="all").T, use_container_width=True)

    st.divider()

    # Chat interface
    st.markdown("### 💬 Ask a Question")

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🧑‍💻" if msg["role"] == "user" else "🤖"):
            st.markdown(msg["content"])
            if msg.get("code"):
                with st.expander("🔍 View generated code", expanded=False):
                    st.code(msg["code"], language="python")

    # Chat input
    if question := st.chat_input("What would you like to know about the data?"):
        # Show user message
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(question)

        # Generate and execute
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🔄 Generating code..."):
                try:
                    code = _try_generate_code(st.session_state.schema, question)
                except Exception as e:
                    st.error(f"LLM Error: {e}")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"❌ Failed to generate code: {e}",
                    })
                    st.stop()

            with st.spinner("⚡ Executing..."):
                max_retries = 1
                result_text = None
                final_code = code
                error_msg = None

                for attempt in range(max_retries + 1):
                    try:
                        _, formatted = execute_code(final_code, df)
                        result_text = formatted
                        break
                    except CodeExecutionError as exc:
                        if attempt < max_retries:
                            st.warning(f"Retry {attempt + 1}: {exc}")
                            try:
                                final_code = _try_generate_code(
                                    st.session_state.schema,
                                    question,
                                    error=str(exc),
                                    previous_code=exc.code,
                                )
                            except Exception as e2:
                                error_msg = str(e2)
                                break
                        else:
                            error_msg = str(exc)

            if result_text is not None:
                st.markdown(f"**Answer:**\n```\n{result_text}\n```")
                with st.expander("🔍 View generated code", expanded=False):
                    st.code(final_code, language="python")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"**Answer:**\n```\n{result_text}\n```",
                    "code": final_code,
                })

                # Log
                model_info = _get_model_info()
                entry = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "question": question,
                    "code": final_code,
                    "result": result_text,
                    "status": "success",
                    "model": model_info.get("model", "unknown"),
                    "provider": model_info.get("provider", "unknown"),
                }
                log = _load_qa_log()
                log.append(entry)
                _save_qa_log(log)
            else:
                st.error(f"❌ Execution failed: {error_msg}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"❌ Execution failed: {error_msg}",
                })

else:
    # No dataset loaded — show welcome
    st.markdown("---")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown("""
        ### 🚀 Get Started

        1. **Upload a dataset** using the sidebar  
           *or click "Use Sample Dataset"*
        2. **Ask questions** in plain English
        3. **Get computed answers** with full code transparency

        The agent generates pandas code from your question,
        executes it on your data, and shows both the result
        and the code that produced it.
        """)

    with col_right:
        st.markdown("""
        ### 💡 Example Questions

        - *"What is the average rating by city?"*
        - *"Which 5 restaurants have the most votes?"*
        - *"How many restaurants are in each cost category?"*
        - *"What's the cheapest restaurant?"*
        - *"Show monthly listing trends"*
        """)

    st.info("👈 Upload a dataset or click **Use Sample Dataset** in the sidebar to begin.", icon="📊")
