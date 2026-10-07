import os
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="DocTalk", page_icon="📄")

# Session-scoped knowledge base: every new session starts empty and only
# sees PDFs uploaded in that session (enforced server-side via a metadata
# filter on retrieval — other sessions' documents are never searched).
if "session_docs" not in st.session_state:
    st.session_state.session_docs = []
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------- sidebar ----------
with st.sidebar:
    st.title("📄 DocTalk")
    st.caption("Chat with your documents. Answers are grounded in the source PDFs, with page-level citations.")

    st.header("Your documents")
    if st.session_state.session_docs:
        for s in st.session_state.session_docs:
            st.markdown(f"- {s}")
    else:
        st.caption("Empty — add a PDF to get started.")

    uploaded = st.file_uploader("Add a PDF", type="pdf", label_visibility="collapsed")
    if uploaded is not None and st.button("Add document", use_container_width=True):
        with st.spinner("Processing document..."):
            try:
                resp = requests.post(
                    f"{API_URL}/upload",
                    files={"file": (uploaded.name, uploaded.getvalue(), "application/pdf")},
                    timeout=180,
                )
                resp.raise_for_status()
                data = resp.json()
                if data["filename"] not in st.session_state.session_docs:
                    st.session_state.session_docs.append(data["filename"])
                st.success(f"Added {data['filename']} ({data['chunks_added']} chunks)")
                st.rerun()
            except requests.RequestException as e:
                st.error(f"Upload failed: {e}")

    if st.session_state.session_docs:
        st.header("Settings")
        scope = st.selectbox("Answer from", ["All my documents"] + st.session_state.session_docs)
        use_rerank = st.toggle(
            "Reranking",
            value=True,
            help="Two-stage retrieval: fetch 10 candidate passages, score each for relevance with an LLM, keep the best 3. More accurate, slightly slower.",
        )
        if st.button("Clear chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    else:
        scope, use_rerank = "All my documents", True

# the filter sent to the API: one file, or all of this session's files
if scope == "All my documents":
    source_filter = st.session_state.session_docs
else:
    source_filter = scope

# ---------- chat ----------
if not st.session_state.messages:
    st.markdown("### Ask anything about your documents")
    if st.session_state.session_docs:
        st.caption('e.g. "What are the key findings?" · "Summarize section 3" · "Who are the authors?"')
    else:
        st.info("Add a PDF in the sidebar first — then ask away.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg.get("sources"):
            with st.expander(f"Sources ({len(msg['sources'])})"):
                for i, chunk in enumerate(msg["sources"], 1):
                    st.markdown(f"**{i}. {chunk['source']} — page {chunk['page']}**")
                    st.text(chunk["text"][:400])

question = st.chat_input(
    "Add a PDF first..." if not st.session_state.session_docs else "Ask about your documents...",
    disabled=not st.session_state.session_docs,
)

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching documents..."):
            try:
                resp = requests.post(
                    f"{API_URL}/query",
                    json={"question": question, "use_rerank": use_rerank, "source": source_filter},
                    timeout=120,
                )
                resp.raise_for_status()
                result = resp.json()
                st.write(result["answer"])
                with st.expander(f"Sources ({len(result['sources'])})"):
                    for i, chunk in enumerate(result["sources"], 1):
                        st.markdown(f"**{i}. {chunk['source']} — page {chunk['page']}**")
                        st.text(chunk["text"][:400])
                st.session_state.messages.append(
                    {"role": "assistant", "content": result["answer"], "sources": result["sources"]}
                )
            except requests.RequestException as e:
                st.error(f"Query failed: {e}")
