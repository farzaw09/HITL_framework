import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("HITL: LLM Evaluation Validation (NER + RE)")

# =========================
# LOAD DATA
# =========================

DATASET_FILE = "llm_validations.xlsx"

if "data" not in st.session_state:

    df = pd.read_excel(DATASET_FILE)
    df.columns = df.columns.str.strip()

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
# FULL ARTICLE VIEW (NO HIGHLIGHT)
# =========================

article_ids = sorted(list(set([d.get("Article ID") for d in st.session_state.data])))

if st.checkbox("Show full article context"):

    selected_article = st.selectbox("Select Article", article_ids)

    article_chunks = [
        d for d in st.session_state.data
        if d.get("Article ID") == selected_article
    ]

    st.write("### Full Article")

    with st.container(height=300):
        for c in article_chunks:
            st.markdown(f"[{c.get('chunk_id','')}] {c.get('text','')}")

# =========================
# TEXT (CURRENT CHUNK)
# =========================

st.write("## Text (Current Chunk)")
st.write(sample.get("text", ""))

# =========================
# LLM EXTRACTION
# =========================

st.markdown("## 🟨 LLM Extraction (Ollama)")

st.write("### NER")
st.write(sample.get("llm_ner", "Not available"))

st.write("### RE")
st.write(sample.get("llm_re", "Not available"))

# =========================
# LLM VALIDATION OUTPUT
# =========================

st.markdown("## 🟦 LLM Evaluation Output")

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

st.metric("Score", sample.get("Score (1–5)", ""))

# =========================
# DOMAIN EXPERT VALIDATION (META-EVALUATION)
# =========================

st.markdown("## 🧠 Domain Expert Validation (LLM Judgment Check)")

st.write("### Evaluate whether LLM evaluation is correct")

ner_check = st.radio("NER evaluation is correct?", ["Yes", "No"])
re_check = st.radio("RE evaluation is correct?", ["Yes", "No"])

confidence = st.slider("Confidence level", 1, 5)
expert_comment = st.text_area("Expert Comment")

sample["expert_ner_check"] = ner_check
sample["expert_re_check"] = re_check
sample["expert_confidence"] = confidence
sample["expert_comment"] = expert_comment

# =========================
# SAVE
# =========================

if st.button("Save Review"):

    st.session_state.data[idx] = sample
    st.success("Saved successfully!")