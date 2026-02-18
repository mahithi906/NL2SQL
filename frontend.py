import streamlit as st
from datetime import datetime
import random
import pandas as pd

# PAGE CONFIG
st.set_page_config(page_title="NL2SQL Chatbot", page_icon="💬", layout="wide")

# SESSION STATE INIT
if "sessions" not in st.session_state:
    # sessions = {
    #   session_id: {
    #       "name": str,
    #       "messages": [ {role, content, time} ],
    #       "suggestions": [str,str,str],
    #       "schema": str,
    #       "last_sql": str,
    #       "last_df": pd.DataFrame | None,
    #       "show_chart": bool
    #   }
    # }
    st.session_state.sessions = {}

if "current_session" not in st.session_state:
    st.session_state.current_session = None

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

DEFAULT_SCHEMA_TEXT = "No schema uploaded yet."



# HELPERS: CREATE/INIT & NORMALIZE SESSIONS
def create_new_session():
    session_id = str(len(st.session_state.sessions) + 1)
    st.session_state.sessions[session_id] = {
        "name": f"Chat {session_id}",
        "messages": [],
        "suggestions": [],
        "schema": DEFAULT_SCHEMA_TEXT,
        "last_sql": "",
        "last_df": None,
        "show_chart": True,
    }
    st.session_state.current_session = session_id
    generate_new_suggestions()
    return session_id


def normalize_sessions():
    for sid, data in st.session_state.sessions.items():
        data.setdefault("name", f"Chat {sid}")
        data.setdefault("messages", [])
        data.setdefault("suggestions", [])
        data.setdefault("schema", DEFAULT_SCHEMA_TEXT)
        data.setdefault("last_sql", "")
        data.setdefault("last_df", None)
        data.setdefault("show_chart", True)


normalize_sessions()

# RANDOM SUGGESTIONS ENGINE (3 new after each user msg)
SUGGESTIONS = [
    "Show me total sales by month.",
    "List top 10 customers by revenue.",
    "How many orders were placed last week?",
    "Show me sales by region.",
    "What is the refund rate?",
    "Which products have low stock?",
    "Show active users by region.",
    "List top performing sales agents.",
    "Show me orders pending delivery.",
    "List customer churn for Q3.",
    "Show me YOY revenue.",
    "List discounted orders.",
    "What is the average order value?",
    "Show best selling categories.",
    "Show signups by device.",
    "Which customers made repeat purchases?",
    "List transactions for 2025.",
    "How many new customers joined?",
    "Show failed transactions.",
    "Show slow moving items.",
    "Give me revenue by quarter.",
    "List the highest selling products.",
]


def generate_new_suggestions():
    if st.session_state.current_session:
        st.session_state.sessions[st.session_state.current_session]["suggestions"] = (
            random.sample(SUGGESTIONS, 3)
        )

# THEME (LIGHT/DARK)
def inject_theme(dark):
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
    max-width:100%;               /* allow full content width */
    width: fit-content;           /* bubble grows with content */
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

.chips-row {{
    display:flex; gap:10px; flex-wrap:wrap;
}}

.chip {{
    background:var(--chip-bg);
    border:1px solid var(--border);
    padding:8px 12px;
    border-radius:18px;
    font-size:13px;
    cursor:pointer;
}}
.chip:hover {{ background:var(--chip-hover); }}

/* Make the chat container use full width of main area */
.full-width-container {{
    max-width: 1400px;
    margin: 0 auto;
}}
</style>
""",
        unsafe_allow_html=True,
    )


inject_theme(st.session_state.dark_mode)


# MOCK PLACEHOLDERS (UI-ONLY) — Replace later with real NL→SQL & DB
def mock_generate_sql(nl: str) -> str:
    nl_low = nl.lower()
    table = "orders" if any(k in nl_low for k in ["order", "orders"]) else "customers"
    return f"SELECT * FROM {table} LIMIT 5;"


def mock_generate_results(sql: str) -> pd.DataFrame:
    random.seed(hash(sql) % (2**32))
    rows = 5
    return pd.DataFrame(
        {
            "id": list(range(1, rows + 1)),
            "category": random.sample(
                ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"], rows
            ),
            "value": [random.randint(10, 100) for _ in range(rows)],
        }
    )


# SIDEBAR — Multi-Session + Schema Upload + Outputs Viewer (ALWAYS VISIBLE)
with st.sidebar:
    st.title("💬 Chats")

    # Dark mode
    new_dark = st.toggle("🌗 Dark Mode", value=st.session_state.dark_mode)
    if new_dark != st.session_state.dark_mode:
        st.session_state.dark_mode = new_dark
        st.rerun()

    st.markdown("---")

    # New Chat
    if st.button("➕ New Chat"):
        create_new_session()
        st.rerun()

    st.markdown("### 🗂 All Chats")
    for session_id, data in st.session_state.sessions.items():
        col1, col2 = st.columns([0.75, 0.25])
        if col1.button(data["name"], key="sel_" + session_id):
            st.session_state.current_session = session_id
            st.rerun()
        if col2.button("🗑", key="del_" + session_id):
            del st.session_state.sessions[session_id]
            st.session_state.current_session = None
            st.rerun()

    st.markdown("---")

    # Ensure current session for settings
    if st.session_state.current_session is None:
        create_new_session()
    chat = st.session_state.sessions[st.session_state.current_session]

    st.markdown("### 📥 Upload SQL / JSON Schema")
    uploaded = st.file_uploader("Upload schema", type=["sql", "json", "txt"])
    if uploaded:
        chat["schema"] = uploaded.read().decode("utf-8")
        st.success("Schema uploaded!")

    st.markdown("### 📈 Display Options")
    chat["show_chart"] = st.toggle(
        "Show chart in responses", value=chat.get("show_chart", True)
    )

    st.markdown("---")
    st.markdown("### 📤 Outputs")

    # Compact view switcher for outputs (ALWAYS visible here)
    view = st.radio(
        "View",
        options=["SQL", "Results", "Chart", "Schema"],
        index=0,
        horizontal=True,
        label_visibility="collapsed",
    )

    # SQL
    if view == "SQL":
        last_sql = chat.get("last_sql", "")
        if last_sql.strip():
            st.caption("SQL used in the last response:")
            st.code(last_sql, language="sql")
        else:
            st.info("No SQL yet. Ask a question to see the SQL here.")

    # Results
    if view == "Results":
        last_df = chat.get("last_df", None)
        if isinstance(last_df, pd.DataFrame):
            st.caption("Results preview (mock). Replace with real DB results later.")
            st.dataframe(last_df, use_container_width=True, height=260)
        else:
            st.info("No results yet. Ask a question to see a results table here.")

    # Chart
    if view == "Chart":
        last_df = chat.get("last_df", None)
        if isinstance(last_df, pd.DataFrame) and chat.get("show_chart", True):
            st.caption("Simple bar chart (mock). Replace with your own visualization.")
            if "category" in last_df.columns and "value" in last_df.columns:
                st.bar_chart(
                    last_df.set_index("category")["value"], use_container_width=True
                )
            else:
                num_cols = last_df.select_dtypes(include="number").columns
                if len(num_cols):
                    st.bar_chart(last_df[num_cols[0]], use_container_width=True)
                else:
                    st.info("No numeric columns to chart.")
        else:
            st.info("Chart is hidden (toggle above) or no data yet.")

    # Schema
    if view == "Schema":
        st.caption("Uploaded schema (JSON / SQL / TXT shown as-is):")
        st.code(chat.get("schema", DEFAULT_SCHEMA_TEXT), language="sql")


# MAIN HEADER
st.markdown(
    f"<div class='full-width-container'><h2>💬 {chat['name']}</h2></div>",
    unsafe_allow_html=True,
)


# FULL-WIDTH CHAT 
st.markdown("<div class='full-width-container'>", unsafe_allow_html=True)
st.markdown("<div class='panel'>", unsafe_allow_html=True)

for msg in chat["messages"]:
    if msg["role"] == "user":
        st.markdown(
            f"""
            <div class="message-row row-user user">
                <div class="avatar user">U</div>
                <div>
                    <div class="bubble">{msg['content']}</div>
                    <div class="timestamp">{msg['time']}</div>
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
                    <div class="bubble">{msg['content']}</div>
                    <div class="timestamp">{msg['time']}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("</div>", unsafe_allow_html=True)

# Suggestions (full width)
st.markdown("### 🔎 Suggested Questions")
scols = st.columns(3)
suggs = chat.get("suggestions", [])
if len(suggs) < 3:
    generate_new_suggestions()
    suggs = chat["suggestions"]
for i, c in enumerate(scols):
    if c.button(suggs[i], key=f"sug_{i}"):
        st.session_state.prefill = suggs[i]
        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)  # end full-width container


# CHAT INPUT
user_input = st.chat_input("Ask a question...")

# Prefill from suggestion
if user_input is None and st.session_state.get("prefill"):
    user_input = st.session_state.prefill
    st.session_state.prefill = ""


# HANDLE INPUT (UI-only)
if user_input is not None:
    if user_input.strip() == "":
        st.warning("⚠️ Please enter a question.")
    else:
        # Save USER message (right bubble)
        chat["messages"].append(
            {
                "role": "user",
                "content": user_input,
                "time": datetime.now().strftime("%H:%M"),
            }
        )

        # --------- TODO: Plug your NL→SQL here (replace mock below) ----------
        import requests

        response = requests.post(
            "http://localhost:8000/nl2sql", json={"query": user_input}
        )
        result = response.json()

        chat["last_sql"] = result["sql"]
        chat["last_df"] = pd.DataFrame(result["rows"])

        # Assistant bubble: AI-generated text (only)
        ai_text = "Here are the results for your request. Use the sidebar outputs to view SQL, table, and chart."
        chat["messages"].append(
            {
                "role": "assistant",
                "content": ai_text,
                "time": datetime.now().strftime("%H:%M"),
            }
        )

        # New rotating suggestions
        generate_new_suggestions()

        st.rerun()
