"""Streamlit chat UI acting as a custom MCP host.

Run with: uv run streamlit run career_matcher_agentic/mcp_host/app.py
"""

import tempfile
from pathlib import Path

import streamlit as st

from career_matcher_agentic.logging.pydantic_logger import setup_logging
from career_matcher_agentic.mcp_host.llm import run_turn
from career_matcher_agentic.mcp_host.mcp_bridge import McpBridge

setup_logging()

st.set_page_config(page_title="Career Matcher", page_icon="🧭")
st.title("Career Matcher")
st.caption(
    "A minimal MCP host: this chat is backed by career-matcher-mcp, job-crawler-mcp, "
    "and embedding-matcher-mcp."
)

uploaded_file = st.sidebar.file_uploader("Upload your CV", type=["pdf", "txt"])

if uploaded_file is not None:
    if "cv_dir" not in st.session_state:
        st.session_state.cv_dir = tempfile.mkdtemp(prefix="career_matcher_cv_")
    cv_path = Path(st.session_state.cv_dir) / uploaded_file.name
    cv_path.write_bytes(uploaded_file.getvalue())
    st.session_state.cv_path = str(cv_path)
    st.sidebar.success(f"CV ready: {uploaded_file.name}")
elif "cv_path" in st.session_state:
    del st.session_state["cv_path"]


@st.cache_resource
def get_bridge() -> McpBridge:
    return McpBridge()


bridge = get_bridge()

if "history" not in st.session_state:
    st.session_state.history = []
if "messages" not in st.session_state:
    st.session_state.messages = []


def _render_tool_calls(tool_calls: list[dict]) -> None:
    if not tool_calls:
        return
    with st.expander(f"{len(tool_calls)} tool call(s)"):
        for call in tool_calls:
            st.markdown(f"**{call['tool']}**")
            st.json(call["arguments"])
            st.json(call["result"])


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["text"])
        _render_tool_calls(message.get("tool_calls", []))

user_message = st.chat_input("Ask about jobs, your CV, or trigger a crawl...")
if user_message:
    st.session_state.messages.append({"role": "user", "text": user_message, "tool_calls": []})
    with st.chat_message("user"):
        st.write(user_message)

    effective_message = user_message
    if "cv_path" in st.session_state:
        effective_message = (
            f"[Uploaded CV file available at: {st.session_state.cv_path}. Use this exact path "
            "for file_path if the user is asking about matching their CV to jobs.]\n\n" + user_message
        )

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer, tool_calls = run_turn(st.session_state.history, effective_message, bridge)
        st.write(answer)
        _render_tool_calls(tool_calls)

    st.session_state.messages.append({"role": "assistant", "text": answer, "tool_calls": tool_calls})
