import streamlit as st
import json
import re
import os

st.title("HITL Annotation Tool (NER + RE)")

# =========================
# ANNOTATOR SELECTION
# =========================
annotator = st.selectbox("Select Annotator", ["admin", "A", "B"])

# =========================
# DATASET MAPPING (IMPORTANT FIX)
# =========================
DATASET_MAP = {
    "A": "dataset_tA.json",
    "B": "dataset_tB.json"
}

# =========================
# AUTO SAVE PATH
# =========================
SAVE_PATH = f"progress_{annotator}.json"

def autosave():
    with open(SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(st.session_state.data, f, indent=2, ensure_ascii=False)

# =========================
# LOAD DATA
# =========================
if annotator == "admin":

    st.info("Admin mode: viewing progress only")

    view_file = st.selectbox(
        "Select file to view",
        ["progress_A.json", "progress_B.json"]
    )

    if os.path.exists(view_file):
        with open(view_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

else:

    base_file = DATASET_MAP[annotator]

    if os.path.exists(SAVE_PATH):
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        with open(base_file, "r", encoding="utf-8") as f:
            data = json.load(f)

# =========================
# SESSION INIT
# =========================
if "data" not in st.session_state:
    st.session_state.data = data

# =========================
# MIGRATION
# =========================
for item in st.session_state.data:

    if "status" not in item:
        item["status"] = "not_started"

    for ent in item.get("entities", []):

        if "original_label" not in ent:
            ent["original_label"] = ent.get("label", "")

        if "corrected_label" not in ent:
            ent["corrected_label"] = ent.get("label", "")

        if "status" not in ent:
            ent["status"] = "accept"

        if "justification" not in ent:
            ent["justification"] = ""

        if "label" in ent:
            del ent["label"]

    for rel in item.get("relations", []):

        if "original_relation" not in rel:
            rel["original_relation"] = rel.get("relation", "")

        if "corrected_relation" not in rel:
            rel["corrected_relation"] = rel.get("relation", "")

        if "status" not in rel:
            rel["status"] = "accept"

        if "justification" not in rel:
            rel["justification"] = ""

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

st.markdown(f"### Sample {display_idx}")
st.markdown(
    f"Chunk ID: `{sample.get('chunk_id','N/A')}` | "
    f"Article: `{sample.get('article_id','N/A')}`"
)

# =========================
# LOAD STATE
# =========================
if st.session_state.get("current_idx") != idx:

    st.session_state.entities = sample.get("entities", []).copy()
    st.session_state.relations = sample.get("relations", []).copy()
    st.session_state.current_idx = idx

    if sample.get("status") != "done":
        sample["status"] = "in_progress"

entities = st.session_state.entities
relations = st.session_state.relations

# =========================
# PROGRESS
# =========================
done = len([x for x in st.session_state.data if x["status"] == "done"])
total = len(st.session_state.data)

st.progress(done / total if total > 0 else 0)
st.write(f"Progress: {done}/{total} completed")

status = sample.get("status", "not_started")

if status == "done":
    st.success("🟢 COMPLETED")
elif status == "in_progress":
    st.warning("🟡 IN PROGRESS")

# =========================
# TEXT DISPLAY
# =========================
st.write("## Text")

def highlight_text(text, entities, sample_status):

    if not entities:
        return text

    color = "lightgreen" if sample_status == "done" else "yellow"

    for ent in entities:
        pattern = re.escape(ent["text"])

        def repl(m):
            return f"<mark style='background-color:{color}'>{m.group(0)}</mark>"

        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)

    return text


st.markdown(
    highlight_text(sample["text"], entities, sample.get("status")),
    unsafe_allow_html=True
)

# =========================
# REVIEW ENTITY
# =========================
st.write("## Entities")

delete_entity_idx = None

for i, ent in enumerate(entities):

    c1, c2, c3, c4, c5, c6 = st.columns([3, 2, 2, 2, 3, 1])

    with c1:
        st.write(ent["text"])

    with c2:
        st.write(ent["original_label"])

    with c3:
        decision = st.selectbox(
            "Decision",
            ["accept", "reject"],
            index=["accept", "reject"].index(ent.get("status", "accept")),
            key=f"ent_dec_{idx}_{i}"
        )

    with c4:
        new_label = st.text_input(
            "Corrected Label",
            value=ent["corrected_label"],
            key=f"ent_label_{idx}_{i}"
        )

    with c5:
        justification = st.text_input(
            "Justification",
            value=ent.get("justification", ""),
            key=f"ent_just_{idx}_{i}"
        )

    with c6:
        if st.button("🗑", key=f"del_ent_{idx}_{i}"):
            delete_entity_idx = i

    entities[i]["corrected_label"] = new_label
    entities[i]["status"] = decision
    entities[i]["justification"] = justification


if delete_entity_idx is not None:
    entities.pop(delete_entity_idx)
    autosave()
    st.rerun()

# =========================
# ADD ENTITY
# =========================
st.write("### Add Entity")

new_text = st.text_input("Entity text")
new_label = st.text_input("Entity label")

if st.button("Add Entity"):
    if new_text and new_label:

        entities.append({
            "text": new_text,
            "original_label": new_label,
            "corrected_label": new_label,
            "status": "accept",
            "justification": ""
        })

        autosave()
        st.rerun()

# =========================
# REVIEW RELATIONS
# =========================
st.write("## Relations")

delete_relation_idx = None

for i, rel in enumerate(relations):

    c1, c2, c3, c4 = st.columns([4, 2, 3, 1])

    with c1:
        st.write(f"{rel.get('head')} → {rel.get('relation')} → {rel.get('tail')}")

    with c2:
        decision = st.selectbox(
            "Decision",
            ["accept", "reject"],
            index=["accept", "reject"].index(rel.get("status", "accept")),
            key=f"rel_dec_{idx}_{i}"
        )

    with c3:
        justification = st.text_input(
            "Justification",
            value=rel.get("justification", ""),
            key=f"rel_just_{idx}_{i}"
        )

    with c4:
        if st.button("🗑", key=f"del_rel_{idx}_{i}"):
            delete_relation_idx = i

    relations[i]["status"] = decision
    relations[i]["justification"] = justification


if delete_relation_idx is not None:
    relations.pop(delete_relation_idx)
    autosave()
    st.rerun()

# =========================
# ADD RELATION
# =========================
st.write("### Add Relation")

new_s = st.text_input("Subject")
new_r = st.text_input("Relation")
new_o = st.text_input("Object")

if st.button("Add Relation"):
    if new_s and new_r and new_o:
        relations.append({
            "head": new_s,
            "relation": new_r,
            "tail": new_o,
            "status": "accept",
            "justification": ""
        })

        autosave()
        st.rerun()

# =========================
# SAVE SAMPLE
# =========================
if st.button("Save Sample"):

    sample["entities"] = entities
    sample["relations"] = relations
    sample["status"] = "done"

    st.session_state.data[idx] = sample

    autosave()

    st.success("Saved!")
    st.rerun()

# =========================
# DOWNLOAD FINAL
# =========================
st.download_button(
    "Download FINAL Dataset",
    data=json.dumps(st.session_state.data, indent=2, ensure_ascii=False),
    file_name=f"FINAL_{annotator}.json",
    mime="application/json"
)