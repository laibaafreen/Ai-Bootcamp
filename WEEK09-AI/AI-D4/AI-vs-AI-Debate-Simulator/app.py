import os
import requests
import streamlit as st

try:
    from backend.debate import run_debate
    DIRECT_DEBATE_AVAILABLE = True
except Exception:
    DIRECT_DEBATE_AVAILABLE = False

# ==============================================================================
# Page Configuration & Styling
# ==============================================================================
st.set_page_config(
    page_title="AI vs AI Debate Simulator",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for polished, modern look
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    .main-header {
        text-align: center;
        padding: 1.5rem 1rem 1rem 1rem;
        margin-bottom: 1.5rem;
    }
    .main-title {
        font-size: 2.6rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, #6366F1 0%, #06B6D4 50%, #3B82F6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.4rem;
    }
    .main-subtitle {
        color: #64748B;
        font-size: 1.15rem;
        font-weight: 400;
        max-width: 650px;
        margin: 0 auto;
    }
    .topic-card {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(6, 182, 212, 0.08) 100%);
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-left: 5px solid #6366F1;
        padding: 1.2rem 1.5rem;
        border-radius: 12px;
        margin: 1rem 0 1.5rem 0;
    }
    .for-badge {
        background: linear-gradient(135deg, #10B981, #059669);
        color: white;
        padding: 3px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.85rem;
        letter-spacing: 0.03em;
        display: inline-block;
        margin-bottom: 0.4rem;
        box-shadow: 0 2px 6px rgba(16, 185, 129, 0.25);
    }
    .against-badge {
        background: linear-gradient(135deg, #EF4444, #DC2626);
        color: white;
        padding: 3px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.85rem;
        letter-spacing: 0.03em;
        display: inline-block;
        margin-bottom: 0.4rem;
        box-shadow: 0 2px 6px rgba(239, 68, 68, 0.25);
    }
    .judge-badge {
        background: linear-gradient(135deg, #8B5CF6, #6366F1);
        color: white;
        padding: 4px 12px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.9rem;
        letter-spacing: 0.03em;
        display: inline-block;
        margin-bottom: 0.6rem;
    }
    .round-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-top: 1.5rem;
        margin-bottom: 0.8rem;
        padding-bottom: 0.3rem;
        border-bottom: 2px solid rgba(148, 163, 184, 0.2);
    }
    .verdict-container {
        background: linear-gradient(145deg, rgba(245, 158, 11, 0.08) 0%, rgba(99, 102, 241, 0.08) 100%);
        border: 2px solid rgba(245, 158, 11, 0.35);
        border-radius: 16px;
        padding: 1.5rem 1.8rem;
        margin-top: 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.04);
    }
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.82rem;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
    }
    .status-online {
        background-color: rgba(16, 185, 129, 0.15);
        color: #059669;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .status-offline {
        background-color: rgba(239, 68, 68, 0.15);
        color: #DC2626;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    .stButton>button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Backend API Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")


# ==============================================================================
# Session State Initialization
# ==============================================================================
if "debate_result" not in st.session_state:
    st.session_state.debate_result = None

if "topic_input_val" not in st.session_state:
    st.session_state.topic_input_val = "Artificial Intelligence will create more jobs than it destroys."

if "last_rounds" not in st.session_state:
    st.session_state.last_rounds = 3


def set_example_topic(topic_str: str):
    """Set the topic input from example buttons."""
    st.session_state.topic_input_val = topic_str


def reset_debate():
    """Clear current debate session state."""
    st.session_state.debate_result = None


# Helper to check backend status
def is_backend_online(url: str) -> bool:
    try:
        r = requests.get(f"{url.rstrip('/')}/", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


# ==============================================================================
# Sidebar
# ==============================================================================
with st.sidebar:
    st.markdown("### ⚔️ Debate Arena")
    st.markdown(
        """
        Two autonomous AI agents debate opposing sides of any resolution across structured rounds.
        An impartial AI adjudicator evaluates both cases and determines the winner with reasoned analysis.
        """
    )

    st.markdown("---")
    st.markdown("#### 💡 Quick Topic Inspirations")
    example_topics = [
        "Artificial Intelligence will create more jobs than it destroys.",
        "Social media does more harm than good to society.",
        "Space exploration is worth the high financial cost.",
        "Remote work is superior to in-office work for productivity.",
        "Universal basic income should be implemented globally.",
    ]

    for ex in example_topics:
        if st.button(f"📌 {ex[:38]}...", help=ex, use_container_width=True, key=f"ex_{hash(ex)}"):
            st.session_state.topic_input_val = ex
            st.rerun()

    st.markdown("---")
    st.markdown("#### 📡 System Connection")
    backend_endpoint = st.text_input(
        "FastAPI Backend Endpoint",
        value=BACKEND_URL,
        help="URL of the running FastAPI backend server (e.g., http://127.0.0.1:8000)",
    )

    backend_healthy = is_backend_online(backend_endpoint)
    if backend_healthy:
        st.markdown(
            '<div class="status-pill status-online">🟢 Backend Connected & Healthy</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="status-pill status-offline">🔴 Backend Offline (Direct Mode fallback ready)</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.caption("AI vs AI Debate Simulator • Powered by Gemini 3.6 Flash & FastAPI")


# ==============================================================================
# Header & Instructions
# ==============================================================================
st.markdown(
    """
    <div class="main-header">
        <div class="main-title">⚔️ AI vs AI Debate Simulator</div>
        <div class="main-subtitle">Two AI debaters enter the arena. One impartial judge decides the victor.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ==============================================================================
# 1. User Inputs & Configuration
# ==============================================================================
with st.container():
    col_input, col_config = st.columns([3, 1])

    with col_input:
        user_topic = st.text_input(
            "🎯 Debate Topic / Resolution",
            value=st.session_state.topic_input_val,
            placeholder="e.g., Artificial general intelligence poses an existential risk to humanity.",
            help="Enter any proposition or debate resolution for the AI agents to argue.",
        )

    with col_config:
        # Strictly restricted to 2 or 3 rounds per SPEC
        num_rounds = st.radio(
            "🔁 Number of Rounds",
            options=[2, 3],
            index=1 if st.session_state.last_rounds == 3 else 0,
            horizontal=True,
            help="Select strictly 2 or 3 debate rounds (FOR and AGAINST exchange arguments each round).",
        )

    btn_col1, btn_col2, _ = st.columns([1.5, 1.2, 3])

    with btn_col1:
        start_button = st.button("🚀 Start Debate", type="primary", use_container_width=True)

    with btn_col2:
        reset_button = st.button("🔄 Clear", on_click=reset_debate, use_container_width=True)


# ==============================================================================
# 2. Execution & Loading State
# ==============================================================================
if start_button:
    cleaned_topic = user_topic.strip() if user_topic else ""

    if not cleaned_topic:
        st.warning("⚠️ Please enter a debate topic before starting the debate.")
    else:
        st.session_state.topic_input_val = cleaned_topic
        st.session_state.last_rounds = num_rounds

        progress_msg = st.empty()
        with st.spinner(f"🥊 Debaters FOR and AGAINST are arguing {num_rounds} rounds, and the Judge is deliberating..."):
            # Check backend connection first
            api_endpoint = f"{backend_endpoint.rstrip('/')}/debate"
            backend_alive = is_backend_online(backend_endpoint)
            payload = {"topic": cleaned_topic, "num_rounds": num_rounds}

            if backend_alive:
                try:
                    response = requests.post(api_endpoint, json=payload, timeout=120)
                    if response.status_code == 200:
                        st.session_state.debate_result = response.json()
                    else:
                        error_detail = response.text
                        try:
                            error_detail = response.json().get("detail", response.text)
                        except Exception:
                            pass
                        st.error(f"⚠️ Backend returned error ({response.status_code}): {error_detail}")
                except requests.exceptions.Timeout:
                    st.error("⏳ Request Timed Out: The debate took longer than 120 seconds. Please try again.")
                except Exception as exc:
                    st.error(f"❌ Backend request failed: {str(exc)}")
            else:
                # If backend is offline, execute directly in-process
                if DIRECT_DEBATE_AVAILABLE:
                    try:
                        res = run_debate(topic=cleaned_topic, num_rounds=num_rounds)
                        st.session_state.debate_result = res.model_dump() if hasattr(res, "model_dump") else res.dict()
                    except Exception as err:
                        st.error(f"❌ Debate execution failed: {str(err)}")
                else:
                    st.error(
                        f"❌ **Connection Error**: Unable to reach FastAPI backend server at `{backend_endpoint}`.\n\n"
                        "**To start the backend server:**\n"
                        "```bash\n"
                        "uvicorn main:app --reload --port 8000\n"
                        "```"
                    )


# ==============================================================================
# 3. Debate Results & Transcript Display
# ==============================================================================
if st.session_state.debate_result:
    result = st.session_state.debate_result
    topic = result.get("topic", user_topic)
    turns = result.get("turns", [])
    winner = result.get("winner", "UNDECIDED").upper()
    reasoning = result.get("reasoning", "No justification provided.")

    st.markdown("---")
    st.markdown(
        f"""
        <div class="topic-card">
            <div style="font-size: 0.85rem; font-weight: 700; color: #6366F1; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.3rem;">DEBATE RESOLUTION</div>
            <h3 style="margin: 0; color: #0F172A; font-weight: 700;">"{topic}"</h3>
            <div style="margin-top: 0.5rem; font-size: 0.9rem; color: #64748B;">
                <span>Total Rounds: <strong>{len(set(t.get('round') for t in turns))}</strong></span> • 
                <span>Total Exchanges: <strong>{len(turns)}</strong></span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 💬 Debate Transcript")

    # Group turns by round
    rounds_dict = {}
    for turn in turns:
        r_num = turn.get("round", 1)
        if r_num not in rounds_dict:
            rounds_dict[r_num] = []
        rounds_dict[r_num].append(turn)

    for r_num in sorted(rounds_dict.keys()):
        st.markdown(
            f"""
            <div class="round-header">
                <h4 style="margin: 0; color: #1E293B;">🥊 Round {r_num}</h4>
            </div>
            """,
            unsafe_allow_html=True,
        )

        for turn in rounds_dict[r_num]:
            speaker = turn.get("speaker", "UNKNOWN").upper()
            text = turn.get("text", "")

            if speaker == "FOR":
                with st.chat_message("user", avatar="🟢"):
                    st.markdown('<span class="for-badge">PROPOSITION — FOR</span>', unsafe_allow_html=True)
                    st.markdown(text)
            elif speaker == "AGAINST":
                with st.chat_message("assistant", avatar="🔴"):
                    st.markdown('<span class="against-badge">OPPOSITION — AGAINST</span>', unsafe_allow_html=True)
                    st.markdown(text)
            else:
                with st.chat_message("system", avatar="⚠️"):
                    st.markdown(f"**{speaker}:**")
                    st.markdown(text)

        st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # Official Judge's Verdict
    # --------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 🧑‍⚖️ Official Adjudication")

    if winner == "FOR":
        winner_badge = "🟢 PROPOSITION (FOR)"
        verdict_color = "#059669"
        border_color = "#10B981"
        bg_color = "rgba(16, 185, 129, 0.08)"
    elif winner == "AGAINST":
        winner_badge = "🔴 OPPOSITION (AGAINST)"
        verdict_color = "#DC2626"
        border_color = "#EF4444"
        bg_color = "rgba(239, 68, 68, 0.08)"
    else:
        winner_badge = f"⚖️ {winner}"
        verdict_color = "#6366F1"
        border_color = "#818CF8"
        bg_color = "rgba(99, 102, 241, 0.08)"

    st.markdown(
        f"""
        <div class="verdict-container" style="background: {bg_color}; border-color: {border_color};">
            <span class="judge-badge">DECISION</span>
            <h2 style="margin: 0.2rem 0 1rem 0; color: {verdict_color}; font-weight: 800;">
                🏆 Winner: {winner_badge}
            </h2>
            <div style="font-weight: 700; font-size: 1rem; color: #1E293B; margin-bottom: 0.4rem;">
                📝 Adjudicator's Reasoned Justification:
            </div>
            <div style="font-size: 1.05rem; line-height: 1.6; color: #334155;">
                {reasoning}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Transcript export text
    full_transcript_text = f"AI vs AI Debate Simulator\nResolution: {topic}\nWinner: {winner}\n\nReasoning:\n{reasoning}\n\n--- Transcript ---\n"
    for turn in turns:
        full_transcript_text += f"\nRound {turn.get('round', 1)} [{turn.get('speaker', '')}]:\n{turn.get('text', '')}\n"

    c1, c2, _ = st.columns([1.5, 1.5, 3])
    with c1:
        st.button("🔄 Start New Debate", on_click=reset_debate, type="secondary", use_container_width=True)
    with c2:
        st.download_button(
            label="📥 Download Transcript",
            data=full_transcript_text,
            file_name="debate_transcript.txt",
            mime="text/plain",
            use_container_width=True,
        )
