import streamlit as st
import pandas as pd
import json
import re

st.set_page_config(layout="wide")
st.title("HITL: Extraction vs LLM Validation Review Tool")

# =========================
# SELECTED ARTICLES ONLY
# =========================

selected_articles = [
    "001", "010", "018", "050", "077",
    "098", "119", "146", "200", "244"
]

# =========================
# LOAD DATA
# =========================

JSON_FILE = "Final_dataset.json"
EXCEL_FILE = "llm_validations.xlsx"

if "data" not in st.session_state:

    # -------- LOAD EXTRACTION --------
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    data = [
        d for d in data
        if str(d.get("article_id", "")).zfill(3) in selected_articles
    ]

    # -------- LOAD VALIDATION --------
    df = pd.read_excel(EXCEL_FILE)
    df.columns = df.columns.str.strip()

    if "Score (1–5)" in df.columns:
        df = df.rename(columns={"Score (1–5)": "Score"})

    df["Article ID"] = df["Article ID"].astype(str).str.zfill(3)
    df = df[df["Article ID"].isin(selected_articles)]

    validation_dict = df.set_index("Article ID").to_dict(orient="index")

    # -------- MERGE --------
    for d in data:
        aid = str(d.get("article_id", "")).zfill(3)
        d["validation"] = validation_dict.get(aid, {})

    st.session_state.data = data


# =========================
# SELECT SAMPLE
# =========================

display_idx = st.number_input(
    "Select Sample",
    min_value=1,
    max_value=len(st.session_state.data),
    value=1
)

idx = display_idx - 1
sample = st.session_state.data[idx]
val = sample.get("validation", {})

st.markdown(f"## Article {sample.get('article_id')}")

# =========================
# FULL ARTICLE VIEW (NO HIGHLIGHT)
# =========================

article_ids = sorted(list(set([d.get("article_id") for d in st.session_state.data])))

if st.checkbox("Show full article context"):

    selected_article = st.selectbox("Select Article", article_ids)

    article_chunks = [
        d for d in st.session_state.data
        if d.get("article_id") == selected_article
    ]

    st.write("### Full Article")

    with st.container(height=300):
        for c in article_chunks:
            st.markdown(f"[{c.get('chunk_id')}] {c.get('text','')}")

# =========================
# CURRENT CHUNK TEXT (HIGHLIGHTED)
# =========================

st.write("## Current Chunk Text")

def highlight_text(text, entities, status):

    if not entities:
        return text

    color = "lightgreen" if status == "done" else "yellow"

    for ent in entities:
        if not ent.get("text"):
            continue

        pattern = re.escape(ent["text"])

        text = re.sub(
            pattern,
            lambda m: f"<mark style='background-color:{color}'>{m.group(0)}</mark>",
            text,
            flags=re.IGNORECASE
        )

    return text


st.markdown(
    highlight_text(
        sample.get("text", ""),
        sample.get("entities", []),
        sample.get("status")
    ),
    unsafe_allow_html=True
)

# =========================
# LLM EXTRACTION (HIDEABLE)
# =========================

st.write("## LLM Extraction (Ollama)")

with st.expander("NER Extraction", expanded=True):
    for e in sample.get("entities", []):
        st.write(f"- {e.get('text')} → {e.get('label')}")

with st.expander("RE Extraction", expanded=True):
    for r in sample.get("relations", []):
        st.write(f"- {r.get('head')} → {r.get('relation')} → {r.get('tail')}")

# =========================
# LLM VALIDATION OUTPUT
# =========================

st.write("## LLM Evaluation Output")

st.metric("Score", val.get("Score", ""))

st.write("### Correct Entities")
st.write(val.get("Correct Entities", ""))

st.write("### Wrong Entities")
st.write(val.get("Wrong Entities", ""))

st.write("### Missing Entities")
st.write(val.get("Missing Entities", ""))

st.write("### Correct Relations")
st.write(val.get("Correct Relations", ""))

st.write("### Wrong Relations")
st.write(val.get("Wrong Relations", ""))

st.write("### Missing Relations")
st.write(val.get("Missing Relations", ""))

st.write("### Comments")
st.write(val.get("Comments", ""))