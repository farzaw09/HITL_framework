import streamlit as st
import json
import os
import re

st.title("HITL Annotation Tool (NER + RE)")

# LOAD DATA
with open("dataset_A.json", "r", encoding="utf-8") as f:
    data = json.load(f)

if "data" not in st.session_state:
    st.session_state.data = data

# SELECT SAMPLE
idx = st.number_input("Select Sample", 0, len(st.session_state.data) - 1, 0)
sample = st.session_state.data[idx]

st.markdown(f"### Sample {idx}")
st.markdown(
    f"Chunk ID: `{sample.get('chunk_id','N/A')}` | Article: `{sample.get('article_id','N/A')}`"
)


# RESET STATE WHEN SAMPLE CHANGES 
if st.session_state.get("current_idx") != idx:
    st.session_state.entities = sample.get("entities", []).copy()
    st.session_state.relations = sample.get("relations", []).copy()
    st.session_state.current_idx = idx

entities = st.session_state.entities
relations = st.session_state.relations

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
                st.markdown(f"🟨 **[{c['chunk_id']}] {c['text']}**")
            else:
                st.markdown(f"[{c['chunk_id']}] {c['text']}")

# HIGHLIGHT FUNCTION
def highlight_text(text, entities):
    if not entities:
        return text

    sorted_ents = sorted(entities, key=lambda x: len(x["text"]), reverse=True)

    for ent in sorted_ents:
        pattern = re.escape(ent["text"])

        def repl(m):
            return f"<mark style='background-color: yellow;'>{m.group(0)}</mark>"

        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)

    return text

st.write("## Text")

text_display = highlight_text(sample["text"], entities)
st.markdown(text_display, unsafe_allow_html=True)


# ENTITY TABLE HEADER
h1, h2, h3, h4, h5 = st.columns([3, 2, 2, 2, 3])

with h1:
    st.markdown("**Entity Text**")
with h2:
    st.markdown("**Label**")
with h3:
    st.markdown("**Decision**")
with h4:
    st.markdown("**Edit Label**")
with h5:
    st.markdown("**Justification**")

# ENTITY EDITING
for i, ent in enumerate(entities):

    c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 3])

    with c1:
        st.write(ent["text"])

    with c2:
        st.write(f"**{ent['label']}**")

    with c3:
        decision = st.selectbox(
            "Decision",
            ["accept", "reject"],
            index=0 if ent.get("status") == "accept" else 1 if ent.get("status") == "reject" else 0,
            key=f"ent_dec_{idx}_{i}"
        )

    with c4:
        new_label = st.text_input(
            "Edit label",
            value=ent["label"],
            key=f"ent_edit_{idx}_{i}"
        )

    with c5:
        justification = st.text_input(
            "Justification",
            value=ent.get("justification", ""),
            key=f"ent_just_{idx}_{i}"
        )

    entities[i]["label"] = new_label
    entities[i]["status"] = decision
    entities[i]["justification"] = justification

st.session_state.entities = entities
sample["entities"] = entities

# ADD ENTITY
st.write("### Add Missing Entity")

new_text = st.text_input("Entity text", key="new_ent_text")
new_label = st.text_input("Entity label", key="new_ent_label")

if st.button("Add Entity"):
    if new_text and new_label:
        entities.append({
            "text": new_text,
            "label": new_label,
            "status": "added",
            "justification": ""
        })

        st.session_state.entities = entities
        sample["entities"] = entities

        st.rerun()

# RELATION HEADER
r1, r2, r3 = st.columns([4, 2, 3])

with r1:
    st.markdown("**Relation**")
with r2:
    st.markdown("**Decision**")
with r3:
    st.markdown("**Justification**")

# RELATION EDITING
for i, rel in enumerate(relations):

    c1, c2, c3 = st.columns([4, 2, 3])

    with c1:
        st.write(f"{rel['head']} → {rel['relation']} → {rel['tail']}")

    with c2:
        decision = st.selectbox(
            "Decision",
            ["accept", "reject"],
            index=0 if rel.get("status") == "accept" else 1 if rel.get("status") == "reject" else 0,
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

st.session_state.relations = relations
sample["relations"] = relations

# ADD RELATION
st.write("### Add Missing Relation")

new_subject = st.text_input("Subject", key="new_subject")
new_rel = st.text_input("Relation", key="new_rel")
new_object = st.text_input("Object", key="new_object")

if st.button("Add Relation"):
    if new_subject and new_rel and new_object:
        relations.append({
            "subject": new_subject,
            "relation": new_rel,
            "object": new_object,
            "status": "added",
            "justification": ""
        })

        st.session_state.relations = relations
        sample["relations"] = relations

        st.rerun()

# SAVE OUTPUT
if st.button("Save Annotation"):

    output_file = "corrected_test.json"

    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            try:
                saved = json.load(f)
            except:
                saved = []
    else:
        saved = []

    saved = [s for s in saved if s.get("chunk_id") != sample["chunk_id"]]
    saved.append(sample)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(saved, f, indent=2, ensure_ascii=False)

    st.success("Saved successfully!")