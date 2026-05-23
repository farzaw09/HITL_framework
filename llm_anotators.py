import streamlit as st
import pandas as pd
import json
import os
import re

st.set_page_config(layout="wide")
st.title("HITL: Extraction vs LLM Validation Review Tool")

st.warning("⚠️ Download backup regularly after review session.")

# FILES
JSON_FILE = "Final_dataset.json"
EXCEL_FILE = "LLM_10samples.xlsx"
SAVE_FILE = "expert_progress.json"

# SELECTED ARTICLES
selected_articles = [
    "001", "002", "014", "025", "034",
    "068", "182", "193", "238", "244"
]

# LOAD DATA
if "data" not in st.session_state:

    # LOAD EXTRACTION
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    data = [
        d for d in data
        if str(d.get("article_id", "")).zfill(3)
        in selected_articles
    ]

    # LOAD VALIDATION
    df = pd.read_excel(EXCEL_FILE)
    df.columns = df.columns.str.strip()

    if "Score (1–5)" in df.columns:
        df = df.rename(columns={"Score (1–5)": "Score"})

    df["Article ID"] = (
        df["Article ID"]
        .astype(str)
        .str.zfill(3)
    )

    df["Chunk ID"] = (
        df["Chunk ID"]
        .astype(str)
    )

    df = df[df["Article ID"].isin(selected_articles)]

    # BUILD VALIDATION DICTIONARY
    validation_dict = {}

    for _, row in df.iterrows():

        aid = str(row["Article ID"]).zfill(3)
        cid = str(row["Chunk ID"])

        if aid not in validation_dict:
            validation_dict[aid] = {}

        validation_dict[aid][cid] = row.to_dict()

    # MERGE VALIDATION INTO DATA
    for d in data:

        aid = str(
            d.get("article_id", "")
        ).zfill(3)

        cid = str(
            d.get("chunk_id", "")
        )

        d["validation"] = (
            validation_dict
            .get(aid, {})
            .get(cid, {})
        )

        if "status" not in d:
            d["status"] = "not_started"

    # RESTORE SAVE FILE
    if os.path.exists(SAVE_FILE):

        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            st.session_state.data = json.load(f)

    else:
        st.session_state.data = data


# AUTOSAVE
def autosave():

    tmp = SAVE_FILE + ".tmp"

    with open(tmp, "w", encoding="utf-8") as f:

        json.dump(
            st.session_state.data,
            f,
            indent=2,
            ensure_ascii=False
        )

    os.replace(tmp, SAVE_FILE)


# SELECT SAMPLE
display_idx = st.number_input(
    "Select Sample",
    min_value=1,
    max_value=len(st.session_state.data),
    value=1
)

idx = display_idx - 1

sample = st.session_state.data[idx]

val = sample.get("validation", {})

# STATUS
if sample["status"] != "done":
    sample["status"] = "in_progress"

done = len([
    x for x in st.session_state.data
    if x.get("status") == "done"
])

total = len(st.session_state.data)

st.progress(done / total if total > 0 else 0)

st.write(f"Progress: {done}/{total} completed")

status = sample.get("status", "not_started")

if status == "done":
    st.success("🟢 COMPLETED")

elif status == "in_progress":
    st.warning("🟡 IN PROGRESS")

# ARTICLE INFO
st.markdown(f"## Article {sample.get('article_id')}")
st.markdown(f"Chunk {sample.get('chunk_id')}")

# FULL ARTICLE VIEW
article_ids = sorted(list(set([
    d.get("article_id")
    for d in st.session_state.data
])))

if st.checkbox("Show full article context"):

    selected_article = st.selectbox(
        "Select Article",
        article_ids
    )

    article_chunks = [
        d for d in st.session_state.data
        if d.get("article_id") == selected_article
    ]

    st.write("### Full Article")

    with st.container(height=300):

        for c in article_chunks:

            st.markdown(
                f"[{c.get('chunk_id')}] "
                f"{c.get('text','')}"
            )

# CURRENT CHUNK TEXT
st.write("## Current Chunk Text")

def highlight_text(text, entities, status):

    if not entities:
        return text

    color = (
        "lightgreen"
        if status == "done"
        else "yellow"
    )

    for ent in entities:

        if not ent.get("text"):
            continue

        pattern = re.escape(ent["text"])

        text = re.sub(
            pattern,
            lambda m:
            f"<mark style='background-color:{color}'>"
            f"{m.group(0)}</mark>",
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

# LLM EXTRACTION
st.write("## LLM Extraction (Ollama)")

with st.expander("NER Extraction", expanded=False):

    entities = sample.get("entities", [])

    if entities:

        ner_df = pd.DataFrame([
            {
                "Entity": e.get("text"),
                "Label": e.get("label")
            }
            for e in entities
        ])

        st.table(ner_df)

    else:
        st.write("No entities")

with st.expander("RE Extraction", expanded=False):

    relations = sample.get("relations", [])

    if relations:

        re_df = pd.DataFrame([
            {
                "Head": r.get("head"),
                "Relation": r.get("relation"),
                "Tail": r.get("tail")
            }
            for r in relations
        ])

        st.table(re_df)

    else:
        st.write("No relations")

# LLM VALIDATION OUTPUT
st.write("## LLM Notebook Evaluation Output")

st.metric("Score", val.get("Score", ""))

validation_table = pd.DataFrame([

    [
        "Correct Entities",
        val.get("Correct Entities", "")
    ],

    [
        "Wrong Entities",
        val.get("Wrong Entities", "")
    ],

    [
        "Missing Entities",
        val.get("Missing Entities", "")
    ],

    [
        "Correct Relations",
        val.get("Correct Relations", "")
    ],

    [
        "Wrong Relations",
        val.get("Wrong Relations", "")
    ],

    [
        "Missing Relations",
        val.get("Missing Relations", "")
    ],

    [
        "Comments",
        val.get("Comments", "")
    ]

], columns=["Category", "LLM Evaluation"])

st.table(validation_table)

# DOMAIN EXPERT VALIDATION
st.write("## Domain Expert Validation")

categories = [
    "Correct Entities",
    "Wrong Entities",
    "Missing Entities",
    "Correct Relations",
    "Wrong Relations",
    "Missing Relations",
    "Overall Evaluation"
]

# LOAD EXISTING SAVED RESULTS
saved_results = {}

if "expert_validation" in sample:

    for item in sample["expert_validation"]:

        saved_results[item["Category"]] = {
            "Decision": item.get("Decision", "Agree"),
            "Notes": item.get("Notes", "")
        }

expert_results = []

for cat in categories:

    safe_cat = cat.replace(" ", "_")

    st.write(f"### {cat}")

    # DEFAULT VALUES
    default_decision = saved_results.get(cat, {}).get(
        "Decision",
        "Agree"
    )

    default_note = saved_results.get(cat, {}).get(
        "Notes",
        ""
    )

    col1, col2 = st.columns([1, 3])

    with col1:

        decision = st.selectbox(
            "Decision",
            ["Agree", "Partial", "Reject"],
            index=["Agree", "Partial", "Reject"].index(default_decision),
            key=f"{safe_cat}_decision_{idx}"
        )

    with col2:

        note = st.text_input(
            "Notes",
            value=default_note,
            key=f"{safe_cat}_note_{idx}"
        )

    expert_results.append({
        "Category": cat,
        "Decision": decision,
        "Notes": note
    })

# OVERALL SCORE
saved_score = sample.get("overall_score", 4)

overall_score = st.slider(
    "Overall Expert Score",
    1,
    5,
    saved_score,
    key=f"overall_score_{idx}"
)

sample["expert_validation"] = expert_results
sample["overall_score"] = overall_score

# SAVE BUTTON
if st.button("Save Current Progress"):

    st.session_state.data[idx] = sample

    autosave()

    st.success("Progress saved!")

# DONE BUTTON
if st.button("Save Sample as DONE"):

    sample["status"] = "done"

    st.session_state.data[idx] = sample

    autosave()

    st.success("Saved as DONE!")

# BACKUP RESTORE
st.sidebar.header("Backup Restore")

uploaded = st.sidebar.file_uploader(
    "Upload backup JSON",
    type=["json"]
)

if uploaded:

    restored_data = json.load(uploaded)

    st.session_state.data = restored_data

    autosave()

    st.sidebar.success("Backup restored!")

    st.rerun()

# DOWNLOAD BACKUP
st.sidebar.header("Download Backup")

backup_json = json.dumps(
    st.session_state.data,
    indent=2,
    ensure_ascii=False
)

st.sidebar.download_button(
    "Download Progress Backup",
    data=backup_json,
    file_name="domain_expert_progress.json",
    mime="application/json"
)

# FINAL DOWNLOAD
st.download_button(
    "Download FINAL RESULTS",
    json.dumps(
        st.session_state.data,
        indent=2,
        ensure_ascii=False
    ),
    file_name="final_domain_expert_results.json",
    mime="application/json"
)