import streamlit as st
import pandas as pd
import json

st.set_page_config(layout="wide")
st.title("HITL: Extraction vs Validation Review Tool")

# =========================
# SELECTED ARTICLES
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
        extraction_data = json.load(f)

    extraction_data = [
        x for x in extraction_data
        if str(x.get("article_id", "")).zfill(3) in selected_articles
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
    merged = []
    for item in extraction_data:
        aid = str(item.get("article_id", "")).zfill(3)
        item["validation"] = validation_dict.get(aid, {})
        merged.append(item)

    st.session_state.data = merged


# =========================
# SELECT SAMPLE
# =========================

idx = st.number_input(
    "Select Article",
    min_value=1,
    max_value=len(st.session_state.data),
    value=1
) - 1

sample = st.session_state.data[idx]
val = sample.get("validation", {})

st.markdown(f"## Article {sample.get('article_id')}")

# ======================================================
# 🟩 FULL ARTICLE VIEW (COLLAPSIBLE)
# ======================================================

with st.expander("📄 Show Full Article Context", expanded=False):

    st.write(sample.get("text", "No text available"))

# ======================================================
# 🟨 LLM EXTRACTION (NER + RE)
# ======================================================

st.markdown("## 🟨 LLM Extraction (Ollama)")

col1, col2 = st.columns(2)

with col1:
    with st.expander("NER Output", expanded=True):
        entities = sample.get("entities", [])
        if entities:
            for e in entities:
                st.write(f"- {e.get('text')} → {e.get('label')}")
        else:
            st.write("No entities")

with col2:
    with st.expander("RE Output", expanded=True):
        relations = sample.get("relations", [])
        if relations:
            for r in relations:
                st.write(f"- {r.get('head')} → {r.get('relation')} → {r.get('tail')}")
        else:
            st.write("No relations")

# ======================================================
# 🟦 LLM VALIDATION OUTPUT
# ======================================================

st.markdown("## 🟦 LLM Validation Output")

st.metric("Score", val.get("Score", ""))

with st.expander("Correct Entities", expanded=True):
    st.write(val.get("Correct Entities", ""))

with st.expander("Wrong Entities", expanded=True):
    st.write(val.get("Wrong Entities", ""))

with st.expander("Missing Entities", expanded=True):
    st.write(val.get("Missing Entities", ""))

with st.expander("Correct Relations", expanded=True):
    st.write(val.get("Correct Relations", ""))

with st.expander("Wrong Relations", expanded=True):
    st.write(val.get("Wrong Relations", ""))

with st.expander("Missing Relations", expanded=True):
    st.write(val.get("Missing Relations", ""))

with st.expander("Comments", expanded=False):
    st.write(val.get("Comments", ""))

# ======================================================
# INFO FOOTER
# ======================================================

st.info("Use expand/collapse sections to focus on specific layers: Context → Extraction → Validation")