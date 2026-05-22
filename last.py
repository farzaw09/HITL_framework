import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("LLM Validation Review Dashboard (HITL)")

st.warning("⚠️ Review only. No annotation/editing required.")

# =========================
# LOAD DATA
# =========================

DATASET_FILE = "llm_validations.xlsx"

if "data" not in st.session_state:

    df = pd.read_excel(DATASET_FILE)

    df.columns = df.columns.str.strip()

    # OPTIONAL: fix score column name
    if "Score (1–5)" in df.columns:
        df = df.rename(columns={"Score (1–5)": "Score"})

    # SELECT ONLY 10 ARTICLES
    selected_articles = [
        "001", "010", "018", "050", "077",
        "098", "119", "146", "200", "244"
    ]

    df["Article ID"] = df["Article ID"].astype(str).str.zfill(3)
    df = df[df["Article ID"].isin(selected_articles)]

    if df.empty:
        st.error("No matching articles found.")
        st.stop()

    # add review fields
    if "expert_decision" not in df.columns:
        df["expert_decision"] = ""

    if "expert_comment" not in df.columns:
        df["expert_comment"] = ""

    if "status" not in df.columns:
        df["status"] = "not_started"

    st.session_state.data = df.to_dict(orient="records")


# =========================
# PROGRESS
# =========================

done = len([x for x in st.session_state.data if x["status"] == "done"])
total = len(st.session_state.data)

st.progress(done / total if total > 0 else 0)
st.write(f"Progress: {done}/{total}")


# =========================
# SELECT ARTICLE
# =========================

idx = st.number_input("Select Sample", 1, total, 1) - 1
sample = st.session_state.data[idx]


# =========================
# HEADER
# =========================

st.markdown(f"## Article {sample.get('Article ID')}")

col1, col2 = st.columns(2)

with col1:
    st.metric("Score", sample.get("Score", ""))

with col2:
    st.write("Comments:")
    st.write(sample.get("Comments", ""))


# =========================
# ORIGINAL TEXT (optional if you have it)
# =========================

if "text" in sample:
    st.markdown("## Original Text")
    st.write(sample["text"])


# =========================
# VALIDATION OUTPUT
# =========================

st.markdown("## LLM Validation Output")

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


# =========================
# EXPANDER (OPTIONAL DETAIL)
# =========================

with st.expander("Show Full Raw Data (Debug)"):
    st.json(sample)


# =========================
# DOMAIN EXPERT REVIEW
# =========================

st.markdown("## Domain Expert Review")

decision = st.selectbox(
    "Decision",
    ["Accept", "Minor Correction", "Reject"],
    index=0
)

comment = st.text_area(
    "Expert Comment",
    value=sample.get("expert_comment", "")
)

sample["expert_decision"] = decision
sample["expert_comment"] = comment


# =========================
# SAVE
# =========================

if st.button("Save Review"):

    sample["status"] = "done"
    st.session_state.data[idx] = sample

    st.success("Saved successfully!")


# =========================
# DOWNLOAD
# =========================

st.markdown("## Export Results")

final_df = pd.DataFrame(st.session_state.data)

json_data = final_df.to_json(
    orient="records",
    force_ascii=False,
    indent=2
)

st.download_button(
    "Download JSON",
    json_data,
    file_name="llm_validation_review.json",
    mime="application/json"
)

csv_data = final_df.to_csv(index=False).encode("utf-8")

st.download_button(
    "Download CSV",
    csv_data,
    file_name="llm_validation_review.csv",
    mime="text/csv"
)