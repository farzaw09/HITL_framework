import streamlit as st
import pandas as pd
import json

st.set_page_config(layout="wide")

st.title("LLM Validation Review Tool")

st.warning("⚠️ Remember to download backup after review session.")

# =========================
# FILE
# =========================

DATASET_FILE = "llm_validations.xlsx"

# =========================
# LOAD DATA
# =========================

if "data" not in st.session_state:

    df = pd.read_excel(DATASET_FILE)

    # SELECT ONLY 10 ARTICLES
    selected_articles = [
        "001", "010", "018", "050", "077",
        "098", "119", "146", "200", "244"
    ]

    df["Article ID"] = df["Article ID"].astype(str).str.zfill(3)

    df = df[df["Article ID"].isin(selected_articles)]

    # ADD REVIEW COLUMNS
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

done = len([
    x for x in st.session_state.data
    if x["status"] == "done"
])

total = len(st.session_state.data)

st.progress(done / total if total > 0 else 0)

st.write(f"Progress: {done}/{total} completed")

# =========================
# SELECT SAMPLE
# =========================

display_idx = st.number_input(
    "Select Sample",
    min_value=1,
    max_value=total,
    value=1
)

idx = display_idx - 1

sample = st.session_state.data[idx]

# =========================
# STATUS
# =========================

if sample["status"] == "done":
    st.success("🟢 COMPLETED")
else:
    st.warning("🟡 IN PROGRESS")

# =========================
# ARTICLE INFO
# =========================

st.markdown(f"## Article {sample.get('Article ID')}")

# =========================
# VALIDATION OUTPUT
# =========================

st.write("## LLM Validation Output")

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

st.write("### Score")
st.write(sample.get("Score (1–5)", ""))

# =========================
# DOMAIN EXPERT REVIEW
# =========================

st.write("## Domain Expert Review")

decision = st.selectbox(
    "Decision",
    ["Accept", "Minor Correction", "Reject"],
    index=0
)

expert_comment = st.text_area(
    "Expert Comment",
    value=sample.get("expert_comment", "")
)

# SAVE TO SESSION
sample["expert_decision"] = decision
sample["expert_comment"] = expert_comment

# =========================
# SAVE BUTTON
# =========================

if st.button("Save Review"):

    sample["status"] = "done"

    st.session_state.data[idx] = sample

    st.success("Review saved!")

# =========================
# DOWNLOAD REVIEW RESULTS
# =========================

st.write("## Download Results")

final_df = pd.DataFrame(st.session_state.data)

json_data = final_df.to_json(
    orient="records",
    force_ascii=False,
    indent=2
)

st.download_button(
    label="Download JSON Backup",
    data=json_data,
    file_name="domain_expert_review.json",
    mime="application/json"
)

excel_buffer = final_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download CSV Results",
    data=excel_buffer,
    file_name="domain_expert_review.csv",
    mime="text/csv"
)