import streamlit as st
import json
import os
import copy
import re

st.set_page_config(layout="wide")
st.title("LLM Extraction vs LLM Validation Review Tool")

st.warning("⚠️ Viewing tool: Compare LLM extraction with LLM validation output")

# =========================
# FILES
# =========================

DATASET_FILE = "Final_dataset.json"
SAVE_FILE = "progress.json"

# =========================
# LOAD DATA
# =========================

if "data" not in st.session_state:

    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        with open(DATASET_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

    st.session_state.data = copy.deepcopy(data)

# =========================
# SELECT SAMPLE
# =========================

idx = st.number_input(
    "Select Sample",
    min_value=1,
    max_value=len(st.session_state.data),
    value=1
) - 1

sample = st.session_state.data[idx]

st.markdown(f"## Article {sample.get('article_id', 'N/A')}")

# =========================
# 1. ORIGINAL TEXT
# =========================

st.write("## 🟩 Original Text")

def highlight(text, entities):
    if not entities:
        return text

    for e in entities:
        if not e.get("text"):
            continue

        pattern = re.escape(e["text"])

        def repl(m):
            return f"<mark style='background-color:yellow'>{m.group(0)}</mark>"

        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)

    return text


st.markdown(
    highlight(sample.get("text", ""), sample.get("entities", [])),
    unsafe_allow_html=True
)

# =========================
# 2. LLM EXTRACTION (OLLAMA)
# =========================

st.write("## 🟨 LLM Extraction (Ollama)")

with st.expander("NER Extraction"):
    entities = sample.get("entities", [])
    if entities:
        for e in entities:
            st.write(f"- {e.get('text')} → {e.get('label')}")
    else:
        st.write("No entities")

with st.expander("RE Extraction"):
    relations = sample.get("relations", [])
    if relations:
        for r in relations:
            st.write(f"- {r.get('head')} → {r.get('relation')} → {r.get('tail')}")
    else:
        st.write("No relations")

# =========================
# 3. LLM VALIDATION OUTPUT
# =========================

st.write("## 🟦 LLM Validation Output")

st.metric("Score", sample.get("Score", ""))

st.subheader("Correct Entities")
st.write(sample.get("Correct Entities", ""))

st.subheader("Wrong Entities")
st.write(sample.get("Wrong Entities", ""))

st.subheader("Missing Entities")
st.write(sample.get("Missing Entities", ""))

st.subheader("Correct Relations")
st.write(sample.get("Correct Relations", ""))

st.subheader("Wrong Relations")
st.write(sample.get("Wrong Relations", ""))

st.subheader("Missing Relations")
st.write(sample.get("Missing Relations", ""))

st.subheader("Comments")
st.write(sample.get("Comments", ""))

# =========================
# 4. DOMAIN EXPERT VIEW ONLY (NO EDIT)
# =========================

st.write("## 🧠 Domain Expert View")

st.info(
    "Check consistency between LLM extraction (Section 2) and LLM validation (Section 3)."
)

with st.expander("Raw JSON (debug)"):
    st.json(sample)