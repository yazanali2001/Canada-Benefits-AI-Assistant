"""
Streamlit login/signup + survey/chat interface for the
Canada Benefits AI agent — professional design + suggested
follow-up questions to guide the user's next step.
"""

import streamlit as st
import requests

API_BASE = "http://127.0.0.1:8000"
REQUEST_TIMEOUT_SECONDS = 30
LONG_OPTIONS_THRESHOLD = 6

st.set_page_config(page_title="Canada Benefits AI", page_icon="🍁", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&display=swap');

:root {
    --spruce: #1F5D4C;
    --spruce-dark: #163F34;
    --maple: #C8262A;
    --maple-dark: #A31E21;
    --wheat: #D9A441;
    --parchment: #F3F1EB;
    --ink: #202A24;
    --ink-soft: #5B6660;
    --surface: #FFFFFF;
    --track: #E4E0D3;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    color: var(--ink);
}

.stApp { background-color: var(--parchment); }

h1, h2, h3 { font-family: 'Fraunces', serif; }

.brand-header {
    background: var(--spruce);
    padding: 1.5rem 2rem;
    border-radius: 16px;
    margin-bottom: 1.4rem;
    display: flex;
    align-items: center;
    gap: 1rem;
}
.brand-header svg { flex-shrink: 0; }
.brand-header .brand-text h1 {
    color: #FBF8F2;
    margin: 0;
    font-size: 1.5rem;
    font-weight: 600;
    letter-spacing: -0.01em;
}
.brand-header .brand-text p {
    color: #D7E5DF;
    margin: 0.25rem 0 0 0;
    font-size: 0.9rem;
    font-family: 'Inter', sans-serif;
}

div.stButton > button[kind="primary"],
div.stFormSubmitButton > button[kind="primary"] {
    background-color: var(--maple) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 999px;
    padding: 0.5rem 1.4rem;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    transition: background-color 0.15s ease, transform 0.15s ease;
}
div.stButton > button[kind="primary"]:hover,
div.stFormSubmitButton > button[kind="primary"]:hover {
    background-color: var(--maple-dark) !important;
    transform: translateY(-1px);
}

div.stButton > button[kind="secondary"],
div.stFormSubmitButton > button[kind="secondary"] {
    background-color: var(--surface) !important;
    color: var(--spruce) !important;
    border: 1.5px solid var(--spruce) !important;
    border-radius: 999px;
    padding: 0.5rem 1.4rem;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    transition: background-color 0.15s ease, transform 0.15s ease;
}
div.stButton > button[kind="secondary"]:hover,
div.stFormSubmitButton > button[kind="secondary"]:hover {
    background-color: #EAF2EF !important;
    transform: translateY(-1px);
}

.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background-color: #E7E3D8;
    padding: 5px;
    border-radius: 12px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 9px;
    padding: 8px 20px;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    color: var(--ink-soft);
}
.stTabs [aria-selected="true"] {
    background-color: var(--surface) !important;
    color: var(--spruce) !important;
}

/* ---------- Progress bar: label is a separate element from the
   bar itself, so styling one never overlaps or clips the other ---------- */
.progress-label {
    font-size: 0.85rem;
    color: var(--ink-soft);
    font-weight: 500;
    margin: 1.4rem 0 0.4rem 0;
}
div[data-testid="stProgress"] {
    margin-bottom: 1rem;
}
div[data-testid="stProgress"] > div {
    background-color: var(--track) !important;
    border-radius: 999px;
    height: 10px;
}
div[data-testid="stProgress"] div[style*="width"] {
    background-color: var(--wheat) !important;
    border-radius: 999px;
}

/* ---------- Chat area ---------- */
div[data-testid="stChatMessage"] {
    background-color: var(--surface);
    border-radius: 14px;
    padding: 0.5rem 0.3rem;
    margin-bottom: 0.4rem;
    border: 1px solid var(--track);
}

/* ---------- Inputs ---------- */
.stTextInput input, .stSelectbox div[data-baseweb="select"] {
    border-radius: 10px !important;
}

/* ---------- Expander (history items) ---------- */
details {
    background-color: var(--surface);
    border-radius: 12px;
    border: 1px solid var(--track);
    padding: 0.2rem 0.6rem;
    margin-bottom: 0.5rem;
}

.suggestion-label {
    font-size: 0.85rem;
    color: var(--ink-soft);
    font-weight: 600;
    margin: 0.6rem 0 0.3rem 0;
}
</style>
""", unsafe_allow_html=True)


MAPLE_LEAF_SVG = """<svg width="40" height="40" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M50 6 L58 30 L78 18 L72 40 L92 42 L74 54 L84 74 L62 66 L60 88 L50 70 L40 88 L38 66 L16 74 L26 54 L8 42 L28 40 L22 18 L42 30 Z"
fill="#D9A441" stroke="#FBF8F2" stroke-width="2" stroke-linejoin="round"/>
</svg>"""


def render_header(subtitle: str) -> None:
    html = (
        '<div class="brand-header">'
        + MAPLE_LEAF_SVG
        + '<div class="brand-text">'
        + f'<h1>Canada Benefits AI</h1><p>{subtitle}</p>'
        + '</div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)


if "token" not in st.session_state:
    st.session_state.token = None
if "history" not in st.session_state:
    st.session_state.history = []
if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "suggestions" not in st.session_state:
    st.session_state.suggestions = []


def auth_headers() -> dict:
    return {"Authorization": f"Bearer {st.session_state.token}"}


def call_agent(message: str = None, selected_option: str = None) -> dict:
    try:
        response = requests.post(
            f"{API_BASE}/chat",
            headers=auth_headers(),
            json={"message": message, "selected_option": selected_option},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if response.status_code == 401:
            st.session_state.token = None
            st.session_state.history = []
            st.rerun()
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"type": "answer", "text": "Can't reach the backend right now.", "options": None, "suggestions": []}
    except requests.exceptions.Timeout:
        return {"type": "answer", "text": "The request timed out. Please try again.", "options": None, "suggestions": []}
    except Exception as e:
        return {"type": "answer", "text": f"Unexpected error: {e}", "options": None, "suggestions": []}


def render_choice_widget(label: str, options: list[str], key: str) -> str:
    if len(options) > LONG_OPTIONS_THRESHOLD:
        return st.selectbox(label, options, key=key)
    return st.radio(label, options, key=key)


def send_followup(text: str) -> None:
    st.session_state.history.append({"role": "user", "content": text})
    with st.spinner("Thinking..."):
        result = call_agent(message=text)
    st.session_state.history.append({"role": "assistant", "content": result["text"]})
    st.session_state.suggestions = result.get("suggestions") or []
    st.rerun()


# ============================================================
# SCREEN 1: Login / Signup
# ============================================================
if not st.session_state.token:
    render_header("Sign in or create an account to get started.")

    tab_login, tab_signup = st.tabs(["Log In", "Sign Up"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Log In", type="primary")

        if submitted:
            try:
                resp = requests.post(
                    f"{API_BASE}/auth/login",
                    json={"username": username, "password": password},
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )
                if resp.status_code == 200:
                    st.session_state.token = resp.json()["access_token"]
                    st.rerun()
                else:
                    st.error(resp.json().get("detail", "Login failed."))
            except requests.exceptions.ConnectionError:
                st.error("Can't reach the backend. Make sure it's running.")

    with tab_signup:
        with st.form("signup_form"):
            new_username = st.text_input("Choose a username", key="signup_username")
            new_password = st.text_input(
                "Choose a password (min 8 characters)", type="password", key="signup_password"
            )
            submitted_signup = st.form_submit_button("Sign Up", type="primary")

        if submitted_signup:
            try:
                resp = requests.post(
                    f"{API_BASE}/auth/signup",
                    json={"username": new_username, "password": new_password},
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )
                if resp.status_code == 201:
                    st.session_state.token = resp.json()["access_token"]
                    st.rerun()
                else:
                    st.error(resp.json().get("detail", "Signup failed."))
            except requests.exceptions.ConnectionError:
                st.error("Can't reach the backend. Make sure it's running.")

# ============================================================
# SCREEN 2: Main app (Chat / History / Edit Profile)
# ============================================================
else:
    col1, col2 = st.columns([5, 1])
    with col1:
        render_header("Answer a few questions to discover which federal benefits you may qualify for.")
    with col2:
        st.write("")
        st.write("")
        if st.button("Log Out", type="secondary"):
            st.session_state.token = None
            st.session_state.history = []
            st.session_state.current_question = None
            st.session_state.suggestions = []
            st.rerun()

    tab_chat, tab_history, tab_profile = st.tabs(["Chat", "History", "Edit Profile"])

    # --- TAB 1: Chat ---
    with tab_chat:
        if st.session_state.current_question or not st.session_state.history:
            try:
                profile_resp = requests.get(
                    f"{API_BASE}/profile", headers=auth_headers(), timeout=REQUEST_TIMEOUT_SECONDS
                )
                if profile_resp.status_code == 200:
                    fields = profile_resp.json()["fields"]
                    answered = sum(1 for f in fields if f["current_value"] is not None)
                    total = len(fields)
                    if answered < total:
                        st.markdown(
                            f'<p class="progress-label">{answered} of {total} questions answered</p>',
                            unsafe_allow_html=True,
                        )
                        st.progress(answered / total)
            except requests.exceptions.ConnectionError:
                pass

        for turn in st.session_state.history:
            with st.chat_message(turn["role"]):
                st.markdown(turn["content"])

        if not st.session_state.history:
            result = call_agent(message="start")
            st.session_state.current_question = result if result["type"] == "question" else None
            st.session_state.history.append({"role": "assistant", "content": result["text"]})
            st.session_state.suggestions = result.get("suggestions") or []
            st.rerun()

        if st.session_state.current_question:
            q = st.session_state.current_question

            choice = render_choice_widget(
                q["text"], q["options"], key=f"radio_{len(st.session_state.history)}"
            )

            other_text = ""
            if choice == "Other":
                other_text = st.text_input(
                    "Please describe your situation:",
                    key=f"other_{len(st.session_state.history)}",
                )

            if st.button("Submit", key=f"submit_{len(st.session_state.history)}", type="primary"):
                if choice == "Other" and not other_text.strip():
                    st.warning("Please describe your situation before submitting.")
                else:
                    shown_answer = other_text if choice == "Other" else choice
                    st.session_state.history.append({"role": "user", "content": shown_answer})

                    result = call_agent(
                        selected_option=choice,
                        message=other_text if choice == "Other" else None,
                    )
                    st.session_state.current_question = (
                        result if result["type"] == "question" else None
                    )
                    st.session_state.history.append({"role": "assistant", "content": result["text"]})
                    st.session_state.suggestions = result.get("suggestions") or []
                    st.rerun()
        else:
            if st.session_state.suggestions:
                st.markdown('<p class="suggestion-label">You might also ask:</p>', unsafe_allow_html=True)
                cols = st.columns(len(st.session_state.suggestions))
                for i, suggestion in enumerate(st.session_state.suggestions):
                    with cols[i]:
                        if st.button(suggestion, key=f"suggestion_{len(st.session_state.history)}_{i}", type="secondary"):
                            send_followup(suggestion)

            if st.button("Download Summary as PDF", type="secondary"):
                try:
                    pdf_resp = requests.get(
                        f"{API_BASE}/export/pdf", headers=auth_headers(), timeout=REQUEST_TIMEOUT_SECONDS
                    )
                    if pdf_resp.status_code == 200:
                        st.download_button(
                            "Click to save PDF",
                            data=pdf_resp.content,
                            file_name="benefits_summary.pdf",
                            mime="application/pdf",
                        )
                    else:
                        st.error("Could not generate PDF yet.")
                except requests.exceptions.ConnectionError:
                    st.error("Can't reach the backend.")

            user_input = st.chat_input("Ask a follow-up question...")
            if user_input:
                send_followup(user_input)

    # --- TAB 2: History ---
    with tab_history:
        st.subheader("Your Past Conversations")
        try:
            hist_resp = requests.get(
                f"{API_BASE}/history", headers=auth_headers(), timeout=REQUEST_TIMEOUT_SECONDS
            )
            if hist_resp.status_code == 200:
                items = hist_resp.json()
                if not items:
                    st.info("No conversation history yet.")
                else:
                    for item in items:
                        with st.expander(f"{item['created_at']} — {item['user_message'][:50]}"):
                            st.markdown(f"**You:** {item['user_message']}")
                            st.markdown(f"**Assistant:** {item['assistant_response']}")
            else:
                st.error("Could not load history.")
        except requests.exceptions.ConnectionError:
            st.error("Can't reach the backend.")

    # --- TAB 3: Edit Profile ---
    with tab_profile:
        st.subheader("Update Your Answers")
        try:
            profile_resp = requests.get(
                f"{API_BASE}/profile", headers=auth_headers(), timeout=REQUEST_TIMEOUT_SECONDS
            )
            if profile_resp.status_code == 200:
                fields = profile_resp.json()["fields"]
                for f in fields:
                    st.markdown(f"**{f['question']}**")
                    current_display = str(f["current_value"]) if f["current_value"] is not None else "Not answered yet"
                    st.caption(f"Current answer: {current_display}")

                    new_choice = render_choice_widget(
                        "Change to:", f["options"], key=f"edit_{f['field']}"
                    )
                    new_free_text = ""
                    if new_choice == "Other":
                        new_free_text = st.text_input("Describe:", key=f"edit_other_{f['field']}")

                    if st.button("Update", key=f"update_btn_{f['field']}", type="primary"):
                        resp = requests.post(
                            f"{API_BASE}/profile/update",
                            headers=auth_headers(),
                            json={
                                "field": f["field"],
                                "new_option": new_choice,
                                "free_text": new_free_text or None,
                            },
                            timeout=REQUEST_TIMEOUT_SECONDS,
                        )
                        if resp.status_code == 200:
                            st.success("Updated! Ask a new question in Chat to see the effect.")
                        else:
                            st.error(resp.json().get("detail", "Update failed."))
                    st.divider()
            else:
                st.error("Could not load profile.")
        except requests.exceptions.ConnectionError:
            st.error("Can't reach the backend.")