import streamlit as st
import json
import re

st.title("HITL Annotation Tool (NER + RE)")


# LOAD DATA
with open("dataset_A.json", "r", encoding="utf-8") as f:
    data = json.load(f)

if "data" not in st.session_state:
    st.session_state.data = data

# MIGRATION 
for item in st.session_state.data:

    if "status" not in item:
        item["status"] = "not_started"

    for ent in item.get("entities", []):

        if "original_label" not in ent:
            ent["original_label"] = ent.get("label", "")

        if "corrected_label" not in ent:
            ent["corrected_label"] = ent.get("label", "")

        # REMOVE OLD SYSTEM CLEANLY
        if "label" in ent:
            del ent["label"]

    for rel in item.get("relations", []):

        if "original_relation" not in rel:
            rel["original_relation"] = rel.get("relation", "")

        if "corrected_relation" not in rel:
            rel["corrected_relation"] = rel.get("relation", "")

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

# LOAD STATE
if st.session_state.get("current_idx") != idx:

    st.session_state.entities = sample.get("entities", []).copy()
    st.session_state.relations = sample.get("relations", []).copy()
    st.session_state.current_idx = idx

    if sample.get("status") != "done":
        sample["status"] = "in_progress"

entities = st.session_state.entities
relations = st.session_state.relations

# PROGRESS CHECK
done = len([x for x in st.session_state.data if x["status"] == "done"])
total = len(st.session_state.data)

st.progress(done / total if total > 0 else 0)
st.write(f"Progress: {done}/{total} completed")

status = sample.get("status", "not_started")

if status == "done":
    st.success("🟢 COMPLETED")
elif status == "in_progress":
    st.warning("🟡 IN PROGRESS")


# FULL ARTICLE VIEW
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


# TEXT DISPLAY WITH HIGHLIGHT
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

# REVIEW ENTITY
st.write("## Entities")

for i, ent in enumerate(entities):

    c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 3])

    with c1:
        st.write(ent["text"])

    with c2:
        st.write(ent["original_label"])

    with c3:
        decision = st.selectbox(
            "Decision",
            ["accept", "reject"],
            index=0 if ent.get("status", "accept") == "accept" else 1,
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

    entities[i]["corrected_label"] = new_label
    entities[i]["status"] = decision
    entities[i]["justification"] = justification

# ADD ENTITY
st.write("### Add Entity")

new_text = st.text_input("Entity text")
new_label = st.text_input("Entity label")

if st.button("Add Entity"):

    if new_text and new_label:

        entities.append({
            "text": new_text,
            "original_label": new_label,
            "status": "accept",
            "corrected_label": new_label,
            "justification": ""
        })

        st.success("Entity added!")

        st.rerun()

# REVIEW RELATIONS 
st.write("## Relations")

for i, rel in enumerate(relations):

    c1, c2, c3 = st.columns([4, 2, 3])

    with c1:
        st.write(f"{rel.get('Subject')} → {rel.get('relation')} → {rel.get('Object')}")

    with c2:
        decision = st.selectbox(
            "Decision",
            ["accept", "reject"],
            index=0 if rel.get("status", "accept") == "accept" else 1,
            key=f"rel_dec_{idx}_{i}"
        )

    with c3:
        justification = st.text_input(
            "Justification",
            value=rel.get("justification", ""),
            key=f"rel_just_{idx}_{i}"
        )

    relations[i]["status"] = decision
    relations[i]["justification"] = justification

# ADD RELATION
st.write("### Add Relation")

new_s = st.text_input("Subject")
new_r = st.text_input("Relation")
new_o = st.text_input("Object")

if st.button("Add Relation"):

    if new_s and new_r and new_o:

        relations.append({
            "Subject": new_s,
            "relation": new_r,
            "Object": new_o,
            "original_relation": new_label,
            "status": "accept",
            "justification": ""
        })

        st.success("Relation added!")

        st.rerun()

# SAVE
if st.button("Save Sample"):

    sample["entities"] = entities
    sample["relations"] = relations
    sample["status"] = "done"

    st.session_state.data[idx] = sample

    with open("corrected_Dataset.json", "w", encoding="utf-8") as f:
        json.dump(st.session_state.data, f, indent=2, ensure_ascii=False)

    st.success("Saved!")

    st.rerun()

# DOWNLOAD FINAL OUTPUT
st.download_button(
    "Download FINAL Dataset",
    data=json.dumps(st.session_state.data, indent=2, ensure_ascii=False),
    file_name="FINAL_corrected_dataset.json",
    mime="application/json"
)