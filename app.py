import streamlit as st
import pandas as pd
import time
import io
from openai import OpenAI

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Description Translator",
    page_icon="🌐",
    layout="centered",
)

# ── Styling ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* App background */
.stApp {
    background: #0d0d0f;
    color: #e8e6e0;
}

/* Main container */
.block-container {
    max-width: 780px;
    padding-top: 3rem;
    padding-bottom: 4rem;
}

/* Header */
.app-header {
    margin-bottom: 2.5rem;
}
.app-header h1 {
    font-size: 2rem;
    font-weight: 600;
    letter-spacing: -0.03em;
    color: #f0ede6;
    margin: 0 0 0.35rem;
}
.app-header p {
    font-size: 0.9rem;
    color: #6b6860;
    margin: 0;
    font-weight: 300;
}

/* Cards / sections */
.section-card {
    background: #16151a;
    border: 1px solid #2a2830;
    border-radius: 12px;
    padding: 1.5rem 1.75rem;
    margin-bottom: 1.25rem;
}
.section-label {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #4a4860;
    margin-bottom: 1rem;
}

/* Progress area */
.progress-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
}
.progress-count {
    font-family: 'DM Mono', monospace;
    font-size: 0.8rem;
    color: #6b6860;
}

/* Status badge */
.status-done   { color: #5ecb8a; }
.status-error  { color: #e05c5c; }
.status-active { color: #a78bfa; }

/* Streamlit overrides */
div[data-testid="stTextInput"] input,
div[data-testid="stSelectbox"] select,
div[data-testid="stTextArea"] textarea {
    background: #1c1b22 !important;
    border: 1px solid #2a2830 !important;
    border-radius: 8px !important;
    color: #e8e6e0 !important;
    font-family: 'DM Sans', sans-serif !important;
}
div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus {
    border-color: #7c6af7 !important;
    box-shadow: 0 0 0 2px rgba(124,106,247,0.2) !important;
}

.stButton > button {
    background: #7c6af7 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    padding: 0.55rem 1.5rem !important;
    font-size: 0.9rem !important;
    transition: opacity 0.15s !important;
}
.stButton > button:hover { opacity: 0.85 !important; }
.stButton > button:disabled { opacity: 0.35 !important; }

/* Download button */
.stDownloadButton > button {
    background: #1c1b22 !important;
    color: #a78bfa !important;
    border: 1px solid #3d3a50 !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
}

/* File uploader */
div[data-testid="stFileUploader"] {
    background: #16151a !important;
    border: 1px dashed #2a2830 !important;
    border-radius: 12px !important;
}

/* Progress bar */
div[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, #7c6af7, #a78bfa) !important;
    border-radius: 4px !important;
}

/* Expander */
div[data-testid="stExpander"] {
    background: #16151a !important;
    border: 1px solid #2a2830 !important;
    border-radius: 10px !important;
}

/* Metric */
div[data-testid="metric-container"] {
    background: #16151a;
    border: 1px solid #2a2830;
    border-radius: 10px;
    padding: 1rem 1.25rem;
}

/* Dataframe */
div[data-testid="stDataFrame"] {
    border: 1px solid #2a2830;
    border-radius: 10px;
    overflow: hidden;
}

/* Alerts */
div[data-testid="stAlert"] {
    border-radius: 8px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
LANGUAGES = [
    "French", "Spanish", "German", "Italian", "Portuguese",
    "Dutch", "Polish", "Swedish", "Danish", "Norwegian",
    "Japanese", "Chinese (Simplified)", "Chinese (Traditional)",
    "Korean", "Arabic", "Hindi", "Turkish", "Russian",
    "Other (specify below)",
]

DEFAULT_PROMPT = (
    "You are a professional translator. Translate the following product description "
    "from English into {language}. Preserve tone, formatting, and any brand-specific "
    "terminology. Return only the translated text with no explanation or preamble."
)

MODELS = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]

# ── API key from Streamlit secrets ─────────────────────────────────────────────
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
except (KeyError, FileNotFoundError):
    st.error(
        "⚠️  No API key found. Add `OPENAI_API_KEY` to your app's Streamlit secrets. "
        "See the README for instructions."
    )
    st.stop()

# ── Session state defaults ─────────────────────────────────────────────────────
for key, default in {
    "results": None,
    "errors": [],
    "running": False,
    "done": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ── Helper: call OpenAI ────────────────────────────────────────────────────────
def translate_text(client, text, language, system_prompt, model, retries=3):
    prompt = system_prompt.replace("{language}", language)
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text},
                ],
                temperature=0.2,
            )
            return response.choices[0].message.content.strip(), None
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # exponential back-off
            else:
                return None, str(e)


# ── UI ─────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <h1>🌐 Description Translator</h1>
    <p>Upload a CSV · translate descriptions with GPT · download results</p>
</div>
""", unsafe_allow_html=True)

# ── Step 1: Configuration ──────────────────────────────────────────────────────
with st.expander("⚙️  Configuration", expanded=not st.session_state.done):
    col1, col2 = st.columns([2, 1])
    with col1:
        lang_choice = st.selectbox("Target language", LANGUAGES)
    with col2:
        model_choice = st.selectbox("Model", MODELS)

    if lang_choice == "Other (specify below)":
        custom_lang = st.text_input("Specify language", placeholder="e.g. Catalan")
        language = custom_lang
    else:
        language = lang_choice

    system_prompt = st.text_area(
        "System prompt  (use `{language}` as a placeholder)",
        value=DEFAULT_PROMPT,
        height=110,
    )

# ── Step 2: Upload ─────────────────────────────────────────────────────────────
st.markdown("### Upload CSV")
uploaded = st.file_uploader(
    "CSV must contain a `url` column and a `description` column (case-insensitive)",
    type="csv",
)

df_preview = None
url_col = desc_col = None

if uploaded:
    try:
        df_preview = pd.read_csv(uploaded)
        cols_lower = {c.lower(): c for c in df_preview.columns}
        url_col  = cols_lower.get("url")
        desc_col = cols_lower.get("description")

        if not url_col or not desc_col:
            st.error(f"Could not find `url` and `description` columns. Found: {list(df_preview.columns)}")
            df_preview = None
        else:
            st.success(f"{len(df_preview):,} rows detected  ·  columns: {list(df_preview.columns)}")
            with st.expander("Preview first 5 rows"):
                st.dataframe(df_preview.head(), use_container_width=True)
    except Exception as e:
        st.error(f"Could not read CSV: {e}")

# ── Step 3: Run ────────────────────────────────────────────────────────────────
can_run = bool(df_preview is not None and language)

if st.button("▶  Run Translation", disabled=not can_run):
    client = OpenAI(api_key=OPENAI_API_KEY)
    total = len(df_preview)

    results_data = []
    errors = []

    st.markdown("---")
    st.markdown("**Translation in progress…**")
    progress_bar = st.progress(0)
    status_text  = st.empty()
    metrics_cols = st.columns(3)
    done_count   = metrics_cols[0].empty()
    err_count    = metrics_cols[1].empty()
    eta_display  = metrics_cols[2].empty()

    start_time = time.time()

    for i, row in df_preview.iterrows():
        idx = list(df_preview.index).index(i)
        pct = idx / total

        desc = str(row[desc_col]) if pd.notna(row[desc_col]) else ""
        url  = str(row[url_col])  if pd.notna(row[url_col])  else ""

        status_text.markdown(
            f"<span style='font-size:0.82rem;color:#6b6860;font-family:DM Mono,monospace;'>"
            f"Translating row {idx+1} / {total} — {url[:60]}</span>",
            unsafe_allow_html=True,
        )

        if desc.strip():
            translation, error = translate_text(client, desc, language, system_prompt, model_choice)
        else:
            translation, error = "", None  # blank descriptions pass through

        if error:
            errors.append({"row": idx + 1, "url": url, "error": error})
            translation = ""

        row_result = row.to_dict()
        row_result[f"description_{language.lower().replace(' ', '_').replace('(', '').replace(')', '')}"] = translation
        row_result["translation_status"] = "error" if error else "done"
        results_data.append(row_result)

        # Update UI
        elapsed = time.time() - start_time
        rows_done = idx + 1
        avg = elapsed / rows_done
        remaining = int(avg * (total - rows_done))
        mins, secs = divmod(remaining, 60)

        progress_bar.progress(min(pct + 1/total, 1.0))
        done_count.metric("Translated", rows_done)
        err_count.metric("Errors", len(errors))
        eta_display.metric("ETA", f"{mins}m {secs}s" if remaining > 0 else "Done")

    # Finalise
    st.session_state.results = pd.DataFrame(results_data)
    st.session_state.errors  = errors
    st.session_state.done    = True
    status_text.markdown(
        "<span style='color:#5ecb8a;font-weight:500;'>✓ Translation complete</span>",
        unsafe_allow_html=True,
    )

# ── Step 4: Download ───────────────────────────────────────────────────────────
if st.session_state.done and st.session_state.results is not None:
    st.markdown("---")
    st.markdown("### Results")

    res = st.session_state.results
    done_n  = (res["translation_status"] == "done").sum()
    error_n = (res["translation_status"] == "error").sum()

    c1, c2, c3 = st.columns(3)
    c1.metric("Total rows", len(res))
    c2.metric("Translated", int(done_n))
    c3.metric("Errors", int(error_n))

    if st.session_state.errors:
        with st.expander(f"⚠️  {error_n} rows had errors — click to review"):
            st.dataframe(pd.DataFrame(st.session_state.errors), use_container_width=True)

    csv_out = res.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇  Download translated CSV",
        data=csv_out,
        file_name=f"translated_{language.lower().replace(' ', '_')}.csv",
        mime="text/csv",
    )

    if error_n > 0:
        errors_only = res[res["translation_status"] == "error"]
        st.download_button(
            label="⬇  Download errors only (for re-run)",
            data=errors_only.to_csv(index=False).encode("utf-8"),
            file_name="translation_errors.csv",
            mime="text/csv",
        )

    st.markdown("---")
    if st.button("↺  Start a new run"):
        st.session_state.results = None
        st.session_state.errors  = []
        st.session_state.done    = False
        st.rerun()
