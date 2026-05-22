import streamlit as st
import pandas as pd
import json

st.set_page_config(layout="wide")
st.title("HITL: Extraction vs Validation (Selected Articles Only)")

# =========================
# SELECTED ARTICLES
# =========================

selected_articles = [
    "001", "010", "018", "050", "077",
    "098", "119", "146", "200", "244"
]

# =========================
# LOAD EXTRACTION (JSON)
# =========================

JSON_FILE = "Final_dataset.json"
EXCEL_FILE = "llm_validations.xlsx"

if "data" not in st.session_state:

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        extraction_data = json.load(f)

    # FILTER JSON (ONLY selected articles)
    extraction_data = [
        x for x in extraction_data
        if str(x.get("article_id", "")).zfill(3) in selected_articles
    ]

    # LOAD VALIDATION (EXCEL)
    df = pd.read_excel(EXCEL_FILE)
    df.columns = df.columns.str.strip()

    if "Score (1–5)" in df.columns:
        df = df.rename(columns={"Score (1–5)": "Score"})

    df["Article ID"] = df["Article ID"].astype(str).str.zfill(3)

    df = df[df["Article ID"].isin(selected_articles)]

    validation_dict = df.set_index("Article ID").to_dict(orient="index")

    # MERGE ONLY SELECTED
    merged = []

    for item in extraction_data:
        aid = str(item.get("article_id", "")).zfill(3)

        item["validation"] = validation_dict.get(aid, {})

        merged.append(item)

    st.session_state.data = merged


# =========================
# SELECT SAMPLE (ONLY 10)
# =========================

idx = st.number_input(
    "Select Sample (Selected Articles Only)",
    min_value=1,
    max_value=len(st.session_state.data),
    value=1
) - 1

sample = st.session_state.data[idx]
val = sample.get("validation", {})

st.markdown(f"## Article {sample.get('article_id')}")

# =========================
# ORIGINAL TEXT
# =========================

st.write("## 🟩 Original Text")
st.write(sample.get("text", ""))


# =========================
# LLM EXTRACTION
# =========================

st.write("## 🟨 LLM Extraction (Ollama)")

st.subheader("NER")
for e in sample.get("entities", []):
    st.write(f"- {e.get('text')} → {e.get('label')}")

st.subheader("RE")
for r in sample.get("relations", []):
    st.write(f"- {r.get('head')} → {r.get('relation')} → {r.get('tail')}")


# =========================
# LLM VALIDATION
# =========================

st.write("## 🟦 LLM Validation Output")

st.metric("Score", val.get("Score", ""))

st.write("Correct Entities")
st.write(val.get("Correct Entities", ""))

st.write("Wrong Entities")
st.write(val.get("Wrong Entities", ""))

st.write("Missing Entities")
st.write(val.get("Missing Entities", ""))

st.write("Correct Relations")
st.write(val.get("Correct Relations", ""))

st.write("Wrong Relations")
st.write(val.get("Wrong Relations", ""))

st.write("Missing Relations")
st.write(val.get("Missing Relations", ""))

st.write("Comments")
st.write(val.get("Comments", ""))