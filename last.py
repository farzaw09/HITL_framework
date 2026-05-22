import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("HITL: LLM Extraction vs LLM Validation Review")

# =========================
# LOAD DATA
# =========================

DATASET_FILE = "llm_validations.xlsx"

if "data" not in st.session_state:

    df = pd.read_excel(DATASET_FILE)
    df.columns = df.columns.str.strip()

    if "Score (1–5)" in df.columns:
        df = df.rename(columns={"Score (1–5)": "Score"})

    selected_articles = [
        "001", "010", "018", "050", "077",
        "098", "119", "146", "200", "244"
    ]

    df["Article ID"] = df["Article ID"].astype(str).str.zfill(3)
    df = df[df["Article ID"].isin(selected_articles)]

    st.session_state.data = df.to_dict(orient="records")


# =========================
# SELECT SAMPLE
# =========================

idx = st.number_input("Select Sample", 1, len(st.session_state.data), 1) - 1
sample = st.session_state.data[idx]

st.markdown(f"## Article {sample.get('Article ID')}")

# =========================
# LAYER 1: TEXT
# =========================

st.markdown("## 🟩 Original Text")
st.write(sample.get("text", "No text available"))


# =========================
# LAYER 2: LLM EXTRACTION (OLLAMA)
# =========================

st.markdown("## 🟨 LLM Extraction (Ollama)")

with st.expander("NER Extraction"):
    st.write(sample.get("llm_ner", "Not available"))

with st.expander("RE Extraction"):
    st.write(sample.get("llm_re", "Not available"))


# =========================
# LAYER 3: LLM VALIDATION OUTPUT
# =========================

st.markdown("## 🟦 LLM Validation Output")

st.metric("Score", sample.get("Score", ""))

st.write("### Correct Entities")
st.write(sample.get("Correct Entities", ""))

st.write("### Wrong Entities")
st.write(sample.get("Wrong Entities", ""))

st.write("### Missing Entities")
st.write(sample.get("Missing Entities", ""))

st.write("### Correct Relations")
st.write(sample.get("Correct Relations", ""))

st.write("### Wrong Relations")
st.write(sample.get("Wrong Relations", ""))

st.write("### Missing Relations")
st.write(sample.get("Missing Relations", ""))

st.write("### Comments")
st.write(sample.get("Comments", ""))


# =========================
# DOMAIN EXPERT REVIEW
# =========================

st.markdown("## Domain Expert Decision")

decision = st.selectbox(
    "Decision",
    ["Accept Validation", "Partially Correct", "Reject Validation"]
)

comment = st.text_area("Expert Comment")

sample["expert_decision"] = decision
sample["expert_comment"] = comment


# =========================
# SAVE
# =========================

if st.button("Save"):

    st.session_state.data[idx] = sample
    st.success("Saved!")