import streamlit as st
import json
import os
import copy
import re

st.set_page_config(layout="wide")
st.title("HITL Annotation Tool (NER + RE)")

st.warning("⚠️ Streamlit Cloud may reset storage after long inactivity. Use backup download daily.")

# FILES
DATASET_FILE = "Final_dataset.json"
SAVE_FILE = "progress.json"

# LOAD DATA
if "data" not in st.session_state:

    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        if not os.path.exists(DATASET_FILE):
            st.error("Missing dataset file")
            st.stop()

        with open(DATASET_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

    st.session_state.data = copy.deepcopy(data)
    st.session_state.current_idx = None


# RESTORE BACKUP (UPLOAD)
st.sidebar.header("Backup Restore")

uploaded = st.sidebar.file_uploader("Upload backup JSON", type=["json"])

if uploaded:
    restored = json.load(uploaded)

    st.session_state.data = restored

    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(restored, f, indent=2, ensure_ascii=False)

    st.sidebar.success("Backup restored!")


# MIGRATION
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

# SELECT SAMPLE
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

# LOAD WORKING STATE
if st.session_state.current_idx != idx:
    st.session_state.entities = copy.deepcopy(sample.get("entities", []))
    st.session_state.relations = copy.deepcopy(sample.get("relations", []))
    st.session_state.current_idx = idx

    if sample["status"] != "done":
        sample["status"] = "in_progress"

entities = st.session_state.entities
relations = st.session_state.relations

# AUTO SAVE 
def autosave():

    sample["entities"] = entities
    sample["relations"] = relations

    st.session_state.data[idx] = sample

    tmp = SAVE_FILE + ".tmp"

    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st.session_state.data, f, indent=2, ensure_ascii=False)

    os.replace(tmp, SAVE_FILE)

# PROGRESS
done = len([x for x in st.session_state.data if x["status"] == "done"])
total = len(st.session_state.data)

st.progress(done / total if total > 0 else 0)
st.write(f"Progress: {done}/{total} completed")

status = sample.get("status", "not_started")

if status == "done":
    st.success("🟢 COMPLETED")
elif status == "in_progress":
    st.warning("🟡 IN PROGRESS")

# ARTICLE VIEW
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
            if c["chunk_id"] == sample["chunk_id"]:
                st.markdown(f"**[{c['chunk_id']}] {c['text']}**")
            else:
                st.markdown(f"[{c['chunk_id']}] {c['text']}")

# TEXT DISPLAY
st.write("## Text")

def highlight_text(text, entities, sample_status):

    if not entities:
        return text

    color = "lightgreen" if sample_status == "done" else "yellow"

    for ent in entities:

        if not ent.get("text"):
            continue

        pattern = re.escape(ent["text"])

        def repl(m):
            return f"<mark style='background-color:{color}'>{m.group(0)}</mark>"

        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)

    return text


st.markdown(
    highlight_text(sample["text"], entities, sample.get("status")),
    unsafe_allow_html=True
)

# REVIEW ENTITIES
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
    if 0 <= delete_entity_idx < len(entities):
        entities.pop(delete_entity_idx)
        autosave()
        st.rerun()

# ADD ENTITY
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

# REVIEW RELATIONS
st.write("## Relations")

delete_relation_idx = None

for i, rel in enumerate(relations):

    c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 3, 1])

    with c1:
        st.write(f"{rel.get('head')} → {rel.get('original_relation')} → {rel.get('tail')}")

    with c2:
        decision = st.selectbox(
            "Decision",
            ["accept", "reject"],
            index=["accept", "reject"].index(rel.get("status", "accept")),
            key=f"rel_dec_{idx}_{i}"
        )

    with c3:
        corrected_relation = st.text_input(
            "Corrected Relation",
            value=rel.get("corrected_relation", rel.get("original_relation", "")),
            key=f"rel_corr_{idx}_{i}"
        )

    with c4:
        justification = st.text_input(
            "Justification",
            value=rel.get("justification", ""),
            key=f"rel_just_{idx}_{i}"
        )

    with c5:
        if st.button("🗑", key=f"del_rel_{idx}_{i}"):
            delete_relation_idx = i

    relations[i]["status"] = decision
    relations[i]["corrected_relation"] = corrected_relation
    relations[i]["justification"] = justification


if delete_relation_idx is not None:
    if 0 <= delete_relation_idx < len(relations):
        relations.pop(delete_relation_idx)
        autosave()
        st.rerun()


# ADD RELATION
st.write("### Add Relation")

new_s = st.text_input("Subject")
new_r = st.text_input("Relation")
new_o = st.text_input("Object")

if st.button("Add Relation"):
    if new_s and new_r and new_o:

        relations.append({
            "head": new_s,
            "original_relation": new_r,
            "corrected_relation": new_r,
            "tail": new_o,
            "status": "accept",
            "justification": ""
        })

        autosave()
        st.rerun()

if st.button("Save Current Progress"):
    autosave()
    st.success("Progress saved!")

# SAVE SAMPLE
if st.button("Save Sample as DONE"):

    sample["status"] = "done"
    autosave()

    st.success("Saved!")
    st.rerun()


# BACKUP DOWNLOAD
st.sidebar.subheader("Download Backup")

backup = json.dumps(st.session_state.data, indent=2, ensure_ascii=False)

st.sidebar.download_button(
    "Download Progress Backup",
    backup,
    file_name="backup.json",
    mime="application/json"
)

# FINAL DOWNLOAD
st.download_button(
    "Download FINAL DATASET",
    json.dumps(st.session_state.data, indent=2, ensure_ascii=False),
    file_name="final.json",
    mime="application/json"
)