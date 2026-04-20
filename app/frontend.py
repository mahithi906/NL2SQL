import os
import requests
import streamlit as st
from datetime import datetime
import random
import pandas as pd
import uuid

# ------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------
st.set_page_config(page_title="NL2SQL Chatbot", page_icon="💬", layout="wide")

# ------------------------------------------------------
# SESSION STATE INIT
# ------------------------------------------------------
if "sessions" not in st.session_state:
    st.session_state.sessions = {}

if "current_session" not in st.session_state:
    st.session_state.current_session = None

# Dark Mode DEFAULT = True
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True  # DEFAULT DARK MODE

if "pending_user_input" not in st.session_state:
    st.session_state.pending_user_input = None

if "pending_user_time" not in st.session_state:
    st.session_state.pending_user_time = None

if "pending_message_appended" not in st.session_state:
    st.session_state.pending_message_appended = False

DEFAULT_SCHEMA_TEXT = ""  # Schema removed entirely


# ------------------------------------------------------
# CREATE SESSION WITH DYNAMIC NAME
# ------------------------------------------------------
def create_new_session(custom_name=None):
    session_id = str(len(st.session_state.sessions) + 1)
    backend_session_id = str(uuid.uuid4())

    st.session_state.sessions[session_id] = {
        "backend_session_id": backend_session_id,
        "name": custom_name if custom_name else f"Chat {session_id}",
        "messages": [],
        "suggestions": [],
        "schema": DEFAULT_SCHEMA_TEXT,
        "last_sql": "",
        "last_df": None,
        "show_chart": True,
        "tokens": 0,
    }

    st.session_state.current_session = session_id
    generate_new_suggestions()
    return session_id


def normalize_sessions():
    for sid, data in st.session_state.sessions.items():
        data.setdefault("backend_session_id", str(uuid.uuid4()))
        data.setdefault("messages", [])
        data.setdefault("suggestions", [])
        data.setdefault("schema", DEFAULT_SCHEMA_TEXT)
        data.setdefault("last_sql", "")
        data.setdefault("last_df", None)
        data.setdefault("show_chart", True)
        data.setdefault("tokens", 0)


normalize_sessions()


# ------------------------------------------------------
# RANDOM SUGGESTIONS
# ------------------------------------------------------
SUGGESTIONS = [
    "How much extra stock do we keep as a safety backup for product AR‑5381?",
    "What does it usually cost us to produce Product ID 319?",
    "What is the selling price of Product ID 317?",
    "What color is the product CN‑6137?",
    "What are the size and weight of the product CA‑5965?",
    "How many products take time to manufacture?",
    "What is the total amount of money actually spent on Product ID 783?",
    "How many times did Product ID 921 go through transactions?",
    "What is the total number of units moved for Product ID 715?",
    "How many units of Product ID 981 were sold in total?",
    "How many transactions happened for Product ID 873 on May 21, 2014?",
    "For work order 4, how many items were ordered and how many were wasted?",
    "How many work orders were created for Product ID 732 between June 1 and June 20, 2011?",
    "How many units of Product ID 738 were ordered on June 3, 2011?",
    "What were the production steps and where did they happen for work order 13?",
    "When did the work start and finish for work order 14 at location 20?",
    "How many units of Product ID 530 were received in purchase order detail 4?",
    "What is the total real cost of product AR‑5381 based on its transaction history?",
    "How many work orders exist for the product CA‑5965?",
    "What is the total production routing cost for work order 13?",
    "What is the name of Product ID 783, and how many units of it were sold?",
    "What was the average purchase price and the color of Product ID 318?",
]


def generate_new_suggestions():
    if st.session_state.current_session:
        st.session_state.sessions[st.session_state.current_session]["suggestions"] = (
            random.sample(SUGGESTIONS, 3)
        )


# ------------------------------------------------------
# THEME / CSS (Dark Mode Default)
# ------------------------------------------------------
def inject_theme(dark=True):
    if dark:
        bg = "#0b1020"
        panel = "#0f172a"
        bubble_user = "linear-gradient(90deg,#7c3aed,#4f46e5)"
        bubble_bot = "#0b1220"
        text = "#e5e7eb"
        border = "#1f2937"
        chip_bg = "#1f2937"
        chip_hover = "#374151"
    else:
        bg = "#f8f9fc"
        panel = "#ffffff"
        bubble_user = "linear-gradient(90deg,#4F46E5,#6D28D9)"
        bubble_bot = "#ffffff"
        text = "#0f172a"
        border = "#e5e7eb"
        chip_bg = "#eef2ff"
        chip_hover = "#e0e7ff"

    st.markdown(
        f"""
<style>
:root {{
    --bg:{bg}; --panel:{panel};
    --bubble-user:{bubble_user}; --bubble-bot:{bubble_bot};
    --text:{text}; --border:{border};
    --chip-bg:{chip_bg}; --chip-hover:{chip_hover};
}}

html, body, [data-testid="stAppViewContainer"] {{
    background: var(--bg);
    color: var(--text);
}}

.panel {{
    background: var(--panel);
    border: 1px solid var(--border);
    padding: 16px; border-radius: 12px;
}}

.message-row {{ display:flex; margin-bottom:12px; }}
.row-user {{ flex-direction: row-reverse; }}
.row-bot {{ flex-direction: row; }}

.avatar {{
    width:38px;height:38px;
    border-radius:50%;
    display:grid;
    place-items:center;
    font-weight:bold;
    color:white;
}}

.avatar.user {{ background:#8b5cf6; }}
.avatar.bot {{ background:#14b8a6; }}

.bubble {{
    max-width:100%;
    width: fit-content;
    padding:12px 16px;
    border-radius:14px;
    border:1px solid var(--border);
}}

.user .bubble {{
    background: var(--bubble-user);
    border:none;
    color:white;
}}

.bot .bubble {{
    background: var(--bubble-bot);
    color: var(--text);
}}

.timestamp {{
    font-size:11px;
    opacity:0.7;
    margin-top:4px;
}}

.chips-row {{ display:flex; gap:10px; flex-wrap:wrap; }}

.chip {{
    background:var(--chip-bg);
    border:1px solid var(--border);
    padding:8px 12px;
    border-radius:18px;
    font-size:13px;
    cursor:pointer;
}}
.chip:hover {{ background:var(--chip-hover); }}

.full-width-container {{
    max-width: 1400px;
    margin: 0 auto;
}}
</style>
""",
        unsafe_allow_html=True,
    )


inject_theme(st.session_state.dark_mode)

# ------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------
with st.sidebar:
    st.title("💬 Chats")

    # DARK MODE ALWAYS
    st.session_state.dark_mode = True
    inject_theme(True)

    st.markdown("---")

    # New Chat
    if st.button("➕ New Chat"):
        create_new_session()
        st.rerun()

    st.markdown("### 🗂 All Chats")
    for session_id, data in st.session_state.sessions.items():
        col1, col2, col3 = st.columns([0.6, 0.25, 0.15])

        if col1.button(data["name"], key=f"sel_{session_id}"):
            st.session_state.current_session = session_id
            st.rerun()

        if col3.button("🗑", key=f"del_{session_id}"):
            del st.session_state.sessions[session_id]
            st.session_state.current_session = None
            st.rerun()

    if st.session_state.current_session is None:
        create_new_session()

    chat = st.session_state.sessions[st.session_state.current_session]

    st.markdown("### 📤 Outputs")

    view = st.radio(
        "View",
        ["SQL", "Results", "Chart"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if view == "SQL":
        # Always show the latest validated_sql, even if empty
        validated_sql = chat.get("last_sql", "")
        # Replace escaped newlines with real newlines for proper formatting
        if validated_sql:
            formatted_sql = validated_sql.replace("\\n", "\n")
            st.markdown("**Validated SQL:**")
            st.code(formatted_sql, language="sql")
        else:
            st.info("No validated SQL yet.")

    if view == "Results":
        # Show DataFrame if available
        if isinstance(chat["last_df"], pd.DataFrame):
            st.dataframe(chat["last_df"], use_container_width=True, height=260)
        else:
            st.info("No results yet.")
        # Always show the raw rows as JSON if available in chat["_last_backend_response"]
        last_backend = chat.get("_last_backend_response", {})
        raw_rows = None
        if isinstance(last_backend, dict):
            raw_rows = last_backend.get("rows")
        if raw_rows is not None and raw_rows != []:
            st.markdown("**Raw Results:**")
            st.json(raw_rows)

    if view == "Chart":
        df = chat["last_df"]
        if isinstance(df, pd.DataFrame) and chat["show_chart"]:
            if "category" in df.columns and "value" in df.columns:
                st.bar_chart(df.set_index("category")["value"])
            else:
                nums = df.select_dtypes(include="number").columns
                if len(nums):
                    st.bar_chart(df[nums[0]])
                else:
                    st.info("No numeric data.")
        else:
            st.info("No data yet.")

    if view == "Debug":
        # Show the last backend response for troubleshooting
        st.markdown("**Backend raw response (debug):**")
        st.json(chat.get("_last_backend_response", {}))


# ------------------------------------------------------
# MAIN CHAT AREA
# ------------------------------------------------------
st.markdown(
    f"<div class='full-width-container'><h2>💬 {chat['name']}</h2></div>",
    unsafe_allow_html=True,
)

st.markdown(
    "<div class='full-width-container'><div class='panel'>", unsafe_allow_html=True
)

for msg in chat["messages"]:
    role = msg["role"]
    content = msg["content"]
    time = msg["time"]

    if role == "user":
        st.markdown(
            f"""
            <div class="message-row row-user user">
                <div class="avatar user">U</div>
                <div>
                    <div class="bubble">{content}</div>
                    <div class="timestamp">{time}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="message-row row-bot bot">
                <div class="avatar bot">AI</div>
                <div>
                    <div class="bubble">{content}</div>
                    <div class="timestamp">{time}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("</div></div>", unsafe_allow_html=True)


# ------------------------------------------------------
# SUGGESTIONS UNDER CHAT
# ------------------------------------------------------
st.markdown("### 🔎 Suggested Questions")
cols = st.columns(3)
suggs = chat.get("suggestions", [])

if len(suggs) < 3:
    generate_new_suggestions()
    suggs = chat["suggestions"]

for i, col in enumerate(cols):
    if col.button(suggs[i], key=f"sg_{i}"):
        st.session_state.prefill = suggs[i]
        st.rerun()


# ------------------------------------------------------
# BACKEND CALLER
# ------------------------------------------------------
BACKEND_BASE_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000/api")
BACKEND_NL2SQL_URL = f"{BACKEND_BASE_URL}/nl2sql"
BACKEND_SESSION_CREATE_URL = f"{BACKEND_BASE_URL}/session/create"
BACKEND_HEALTH_URL = f"{BACKEND_BASE_URL}/health"


def send_to_backend(question, session_id):
    """Send question to NL2SQL backend API."""
    try:
        resp = requests.post(
            BACKEND_NL2SQL_URL,
            json={
                "question": question,
                "session_id": session_id,
            },
            timeout=360,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {
            "answer": f"Backend error: {str(e)}",
            "sql": "",
            "rows": [],
            "row_count": 0,
            "execution_error": str(e),
            "flow": [],
        }


def create_backend_session(session_id, name):
    """Create a session in the backend."""
    try:
        resp = requests.post(
            BACKEND_SESSION_CREATE_URL,
            json={
                "session_id": session_id,
                "name": name,
            },
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.warning(f"Could not sync session to backend: {str(e)}")
        return None


def check_backend_health():
    """Check if backend is available."""
    try:
        resp = requests.get(BACKEND_HEALTH_URL, timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


# ------------------------------------------------------
# SINGLE CHAT INPUT
# ------------------------------------------------------
user_input = st.chat_input("Ask a question...")

# Prefill from suggestion
if user_input is None and st.session_state.get("prefill"):
    user_input = st.session_state.prefill
    del st.session_state["prefill"]

if user_input:
    st.session_state.pending_user_input = user_input
    st.session_state.pending_user_time = datetime.now().strftime("%H:%M")
    st.session_state.pending_message_appended = False
    st.rerun()

pending_input = st.session_state.get("pending_user_input")
if pending_input:
    # Append the user message first and rerun so it displays immediately.
    if not st.session_state.get("pending_message_appended"):
        if chat["messages"] == []:
            first_three = " ".join(pending_input.split()[:3])
            chat["name"] = first_three
            create_backend_session(st.session_state.current_session, chat["name"])

        chat["messages"].append(
            {
                "role": "user",
                "content": pending_input,
                "time": st.session_state.pending_user_time,
            }
        )
        st.session_state.pending_message_appended = True
        st.rerun()

    backend_session_id = st.session_state.current_session
    response = send_to_backend(pending_input, session_id=backend_session_id)

    # Save the raw backend response for debugging
    chat["_last_backend_response"] = response

    # Extract SQL (validated_sql takes precedence)
    validated_sql = response.get("validated_sql") or response.get("sql", "")
    chat["last_sql"] = validated_sql

    # Extract rows and row count
    rows = response.get("rows", [])
    row_count = response.get("row_count", 0)

    # Convert to DataFrame if we have rows
    if rows and isinstance(rows, list):
        try:
            chat["last_df"] = pd.DataFrame(rows)
        except Exception:
            chat["last_df"] = None
    else:
        chat["last_df"] = None

    # Get final answer
    answer = response.get("answer", "No response from backend")

    # Show execution error if present
    if response.get("execution_error"):
        answer = f"{answer}\n\n⚠️ Execution Error: {response.get('execution_error')}"

    # Assistant reply
    chat["messages"].append(
        {
            "role": "assistant",
            "content": answer,
            "time": datetime.now().strftime("%H:%M"),
        }
    )

    st.session_state.pending_user_input = None
    st.session_state.pending_user_time = None
    st.session_state.pending_message_appended = False

    generate_new_suggestions()
    st.rerun()
