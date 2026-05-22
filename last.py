import streamlit as st
import pandas as pd
import json
import re

st.set_page_config(layout="wide")
st.title("HITL: Extraction vs Validation Review Tool")

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

    # -------- extraction --------
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    data = [
        d for d in data
        if str(d.get("article_id", "")).zfill(3) in selected_articles
    ]

    # -------- validation --------
    df = pd.read_excel(EXCEL_FILE)
    df.columns = df.columns.str.strip()

    if "Score (1–5)" in df.columns:
        df = df.rename(columns={"Score (1–5)": "Score"})

    df["Article ID"] = df["Article ID"].astype(str).str.zfill(3)
    df = df[df["Article ID"].isin(selected_articles)]

    val_dict = df.set_index("Article ID").to_dict(orient="index")

    # -------- merge --------
    for d in data:
        aid = str(d.get("article_id", "")).zfill(3)
        d["validation"] = val_dict.get(aid, {})

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

st.markdown(f"### Sample {display_idx}")
st.markdown(f"Article ID: `{sample.get('article_id')}`")

# =========================
# ARTICLE VIEW (KEEP ORIGINAL STYLE)
# =========================

article_ids = sorted(list(set([d.get("article_id") for d in st.session_state.data])))

if st.checkbox("Show full article"):

    selected_article = st.selectbox("Select Article", article_ids)

    article_chunks = [
        d for d in st.session_state.data
        if d.get("article_id") == selected_article
    ]

    st.write("### Full Article")

    with st.container(height=300):
        for c in article_chunks:

            text = c.get("text", "")

            # highlight entities (SAME AS YOUR ORIGINAL LOGIC)
            entities = c.get("entities", [])
            color = "yellow"

            for ent in entities:
                if ent.get("text"):
                    pattern = re.escape(ent["text"])
                    text = re.sub(
                        pattern,
                        lambda m: f"<mark style='background-color:{color}'>{m.group(0)}</mark>",
                        text,
                        flags=re.IGNORECASE
                    )

            if c["chunk_id"] == sample.get("chunk_id"):
                st.markdown(f"**[{c['chunk_id']}] {text}**", unsafe_allow_html=True)
            else:
                st.markdown(f"[{c['chunk_id']}] {text}", unsafe_allow_html=True)


# =========================
# LLM EXTRACTION (ONLY WHAT YOU SAID)
# =========================

st.write("## LLM Extraction (Ollama)")

st.write("### NER")
for e in sample.get("entities", []):
    st.write(f"- {e.get('text')} → {e.get('label')}")

st.write("### RE")
for r in sample.get("relations", []):
    st.write(f"- {r.get('head')} → {r.get('relation')} → {r.get('tail')}")


# =========================
# LLM VALIDATION OUTPUT
# =========================

st.write("## LLM Validation Output")

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