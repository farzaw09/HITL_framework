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

    try:
        df = pd.read_excel(DATASET_FILE)

    except Exception as e:
        st.error(f"Error loading Excel file: {e}")
        st.stop()

    # CLEAN COLUMN NAMES
    df.columns = df.columns.str.strip()

    # OPTIONAL DEBUG
    st.write("Detected Columns:")
    st.write(df.columns.tolist())

    # RENAME COLUMN
    if "Score (1–5)" in df.columns:
        df = df.rename(columns={
            "Score (1–5)": "Score"
        })

    # SELECT ONLY 10 ARTICLES
    selected_articles = [
        "001", "010", "018", "050", "077",
        "098", "119", "146", "200", "244"
    ]

    # FORMAT ARTICLE IDs
    df["Article ID"] = df["Article ID"].astype(str).str.zfill(3)

    # FILTER ARTICLES
    df = df[df["Article ID"].isin(selected_articles)]

    # CHECK EMPTY
    if df.empty:
        st.error("No matching articles found.")
        st.stop()

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
st.write(sample.get("Score", ""))

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
# DOWNLOAD RESULTS
# =========================

st.write("## Download Results")

final_df = pd.DataFrame(st.session_state.data)

# JSON DOWNLOAD
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

# CSV DOWNLOAD
csv_data = final_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download CSV Results",
    data=csv_data,
    file_name="domain_expert_review.csv",
    mime="text/csv"
)