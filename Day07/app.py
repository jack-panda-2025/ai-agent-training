from dotenv import load_dotenv

load_dotenv()

import uuid
import streamlit as st
from langgraph.types import Command
from rag_graph import graph

st.title("RAG Agent with Human-in-the-Loop")

# --- Initialize session state ---
if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = None
if "is_waiting" not in st.session_state:
    st.session_state["is_waiting"] = False
if "interrupt_payload" not in st.session_state:
    st.session_state["interrupt_payload"] = None
if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if not st.session_state["is_waiting"]:
    query = st.chat_input("Ask a question...")

    if query:
        st.session_state["thread_id"] = str(uuid.uuid4())
        config = {"configurable": {"thread_id": st.session_state["thread_id"]}}

        st.session_state["messages"].append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.write(query)

        with st.chat_message("assistant"):
            status_box = st.status("Agent thinking...", expanded=True)
            interrupted = False
            answer_placeholder = st.empty()
            streamed_answer = ""

            for event_type, event_data in graph.stream(
                {
                    "query": query,
                    "documents": [],
                    "confidence": 0.0,
                    "human_decision": "",
                    "answer": "",
                },
                config=config,
                stream_mode=["updates", "messages"],
            ):
                if event_type == "updates":
                    if "__interrupt__" in event_data:
                        interrupted = True
                        payload = event_data["__interrupt__"][0].value
                        st.session_state["interrupt_payload"] = payload
                        st.session_state["is_waiting"] = True
                        status_box.update(
                            label="Low confidence - human review needed", state="error"
                        )
                        break
                    for node_name in event_data:
                        status_box.write(f"✓ {node_name} completed")

                elif event_type == "messages":
                    chunk, metadata = event_data
                    if hasattr(chunk, "content") and chunk.content:
                        streamed_answer += chunk.content
                        answer_placeholder.write(streamed_answer)

            if not interrupted:
                status_box.update(label="Done", state="complete")
                st.session_state["messages"].append(
                    {"role": "assistant", "content": streamed_answer}
                )

# --- Review mode: human decision ---
if st.session_state["is_waiting"]:
    payload = st.session_state["interrupt_payload"]

    st.warning(f"⚠️ Low confidence: {payload['confidence']:.3f}")
    st.write("**Query:**", payload["query"])
    st.write("**Retrieved documents:**")
    for doc in payload["documents"]:
        st.write(f"- {doc}")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Approve", use_container_width=True):
            config = {"configurable": {"thread_id": st.session_state["thread_id"]}}
            for event in graph.stream(
                Command(resume="approve"), config=config, stream_mode="updates"
            ):
                if "generate" in event:
                    answer = event["generate"]["answer"]
                    st.session_state["messages"].append(
                        {"role": "assistant", "content": answer}
                    )
            st.session_state["is_waiting"] = False
            st.rerun()

    with col2:
        if st.button("❌ Reject", use_container_width=True):
            config = {"configurable": {"thread_id": st.session_state["thread_id"]}}
            for event in graph.stream(
                Command(resume="reject"), config=config, stream_mode="updates"
            ):
                if "generate" in event:
                    answer = event["generate"]["answer"]
                    st.session_state["messages"].append(
                        {"role": "assistant", "content": answer}
                    )
            st.session_state["is_waiting"] = False
            st.rerun()
