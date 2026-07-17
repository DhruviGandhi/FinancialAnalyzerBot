import streamlit as st
import pandas as pd
from pathlib import Path
from financialAnalyzer import FinancialAnalyzer

# ----------------------------------------------------
# 1. PAGE SETUP & PREMIUM CSS THEME
# ----------------------------------------------------
st.set_page_config(
    page_title="FamilyFolio - Wealth Advisor",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling (Glassmorphism, Google Fonts, harmony colors)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Premium background & layout styling */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        color: #f1f5f9;
    }
    
    /* Glassmorphism KPI card styling */
    .kpi-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        transition: transform 0.3s ease;
        margin-bottom: 20px;
    }
    .kpi-card:hover {
        transform: translateY(-5px);
        border-color: rgba(255, 255, 255, 0.2);
    }
    .kpi-label {
        font-size: 0.9rem;
        text-transform: uppercase;
        color: #94a3b8;
        font-weight: 600;
        letter-spacing: 0.05em;
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: 800;
        color: #f8fafc;
        margin-top: 8px;
    }
    .kpi-delta {
        font-size: 0.85rem;
        font-weight: 600;
        margin-top: 4px;
    }
    .delta-up { color: #10b981; }
    .delta-down { color: #f43f5e; }
    
    /* Chat bubbles */
    .chat-bubble {
        padding: 16px 20px;
        border-radius: 16px;
        margin-bottom: 12px;
        max-width: 85%;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .chat-user {
        background: rgba(99, 102, 241, 0.15);
        border: 1px solid rgba(99, 102, 241, 0.3);
        align-self: flex-end;
        margin-left: auto;
    }
    .chat-bot {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        align-self: flex-start;
    }
    
    /* ── Generic stButton baseline ── */
    div.stButton > button {
        background: rgba(255, 255, 255, 0.04) !important;
        color: #c7d2fe !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 999px !important;          /* pill shape */
        padding: 8px 18px !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.01em !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
        white-space: normal !important;     /* allow text to wrap */
        word-break: break-word !important;
        min-height: 48px !important;
        height: auto !important;
        line-height: 1.4 !important;
        text-align: center !important;
        width: 100% !important;
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, rgba(99,102,241,0.3) 0%, rgba(139,92,246,0.3) 100%) !important;
        color: #ffffff !important;
        border-color: rgba(139,92,246,0.6) !important;
        box-shadow: 0 0 18px rgba(139,92,246,0.35) !important;
        transform: translateY(-2px) scale(1.02) !important;
    }
    div.stButton > button:active {
        transform: translateY(1px) scale(0.98) !important;
        box-shadow: none !important;
    }

    /* ── FAQ Category header ── */
    .faq-category {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #a5b4fc;
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin: 14px 0 8px 0;
        padding-left: 2px;
    }
    .faq-category::after {
        content: '';
        flex: 1;
        height: 1px;
        background: linear-gradient(to right, rgba(165,180,252,0.35), transparent);
    }

    /* ── Glowing FAQ section wrapper ── */
    .faq-wrapper {
        background: rgba(255,255,255,0.025);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 18px;
        padding: 18px 20px 20px;
        margin-bottom: 22px;
        backdrop-filter: blur(8px);
    }

    /* ── Upload Landing Screen ── */
    .upload-hero {
        text-align: center;
        padding: 60px 40px 50px;
        margin: 40px auto;
        max-width: 680px;
        background: rgba(255,255,255,0.03);
        border: 1.5px dashed rgba(139,92,246,0.45);
        border-radius: 28px;
        backdrop-filter: blur(10px);
        animation: pulse-border 3s ease-in-out infinite;
    }
    @keyframes pulse-border {
        0%, 100% { border-color: rgba(139,92,246,0.35); box-shadow: 0 0 0px rgba(139,92,246,0); }
        50%       { border-color: rgba(139,92,246,0.75); box-shadow: 0 0 30px rgba(139,92,246,0.18); }
    }
    .upload-icon {
        font-size: 4rem;
        margin-bottom: 18px;
        display: block;
        animation: float 3.5s ease-in-out infinite;
    }
    @keyframes float {
        0%, 100% { transform: translateY(0); }
        50%       { transform: translateY(-10px); }
    }
    .upload-title {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(to right, #a5b4fc, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 12px;
    }
    .upload-sub {
        color: #64748b;
        font-size: 1rem;
        margin-bottom: 32px;
        line-height: 1.6;
    }
    .feature-badges {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 10px;
        margin-top: 28px;
    }
    .badge {
        background: rgba(99,102,241,0.12);
        border: 1px solid rgba(99,102,241,0.25);
        color: #a5b4fc;
        border-radius: 999px;
        padding: 6px 16px;
        font-size: 0.8rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 2. DATA LOADING & STATE CACHING
# ----------------------------------------------------

@st.cache_resource
def load_analyzer(path_str: str):
    """Load FinancialAnalyzer; cached by file path string."""
    try:
        return FinancialAnalyzer(Path(path_str))
    except Exception as e:
        st.error(f"Error loading portfolio data: {e}")
        return None

def load_analyzer_from_bytes(file_bytes: bytes, filename: str):
    """Save uploaded bytes to a temp file and load analyzer (not cached by resource — keyed by filename)."""
    temp_path = Path(f"./uploaded_{filename}")
    temp_path.write_bytes(file_bytes)
    return load_analyzer(str(temp_path))

# ── Session-state: persist uploaded file across reruns ─────────────────────────
if 'uploaded_file_bytes' not in st.session_state:
    st.session_state.uploaded_file_bytes = None
if 'uploaded_file_name' not in st.session_state:
    st.session_state.uploaded_file_name = None
if 'uploader_key' not in st.session_state:
    # Incrementing this forces the file_uploader widget to reset to empty
    st.session_state.uploader_key = 0

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.markdown("<h2 style='color:#a5b4fc; font-weight:800;'>💼 Portfolio Data</h2>", unsafe_allow_html=True)

uploaded_file = st.sidebar.file_uploader(
    "📂 Upload FamilyFolio Excel Sheet",
    type=["xlsx"],
    key=f"file_uploader_{st.session_state.uploader_key}",
    help="Upload a FamilyFolio-format .xlsx file. All analysis and chat will be based on this data."
)

# When a new file is uploaded, save its bytes to session state
if uploaded_file is not None:
    st.session_state.uploaded_file_bytes = uploaded_file.getvalue()
    st.session_state.uploaded_file_name = uploaded_file.name

# ── Load analyzer only if a file is available ──────────────────────────────────
if st.session_state.uploaded_file_bytes is None:
    # ── Premium landing screen ─────────────────────────────────────────────────
    st.markdown("""
    <h1 style='font-weight:800; background:linear-gradient(to right, #a5b4fc, #818cf8);
        -webkit-background-clip:text; -webkit-text-fill-color:transparent;'>
        FamilyFolio Advisor AI
    </h1>
    <p style='color:#94a3b8; font-size:1.1rem; margin-top:-8px;'>Premium Wealth & Portfolio Advisory Intelligence</p>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="upload-hero">
        <span class="upload-icon">📊</span>
        <div class="upload-title">Upload Your Portfolio File</div>
        <div class="upload-sub">
            Upload your <b>FamilyFolio Excel sheet</b> using the sidebar on the left.<br>
            Your data stays local — no cloud upload ever happens.
        </div>
        <div style="color:#475569; font-size:0.88rem;">Supports <code>.xlsx</code> format · Family member auto-detection · AI-powered Q&amp;A</div>
        <div class="feature-badges">
            <span class="badge">📈 Portfolio Analytics</span>
            <span class="badge">💬 AI Chat Advisor</span>
            <span class="badge">👨‍👩‍👧 Family Member Filter</span>
            <span class="badge">🔒 Fully Local</span>
            <span class="badge">⚡ Instant Answers</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# File is available — load the analyzer
analyzer = load_analyzer_from_bytes(
    st.session_state.uploaded_file_bytes,
    st.session_state.uploaded_file_name
)

if not analyzer:
    st.sidebar.error("Could not parse the uploaded file. Please check the format.")
    st.stop()

portfolio = analyzer.portfolio_data

# Show a sidebar success banner with file name
st.sidebar.success(f"✅ Loaded: {st.session_state.uploaded_file_name}")
if st.sidebar.button("🗑️ Remove File & Reset", key="clear_file"):
    # Increment key → forces the file_uploader widget to render as empty on rerun
    st.session_state.uploader_key += 1
    st.session_state.uploaded_file_bytes = None
    st.session_state.uploaded_file_name = None
    st.session_state.chat_history = []
    st.session_state.chat_name = ""
    st.rerun()

# ----------------------------------------------------
# 3. DYNAMIC METRICS (always whole-family aggregate)
# ----------------------------------------------------
# Extract holders directly from the uploaded file's parsed data
holders_list = []
if 'holders' in portfolio:
    holders_list = [h['Holder Name'] for h in portfolio['holders']]

# Main Title Header
st.markdown("<h1 style='font-weight:800; background:linear-gradient(to right, #a5b4fc, #818cf8); -webkit-background-clip:text; -webkit-text-fill-color:transparent;'>FamilyFolio Advisor AI</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#94a3b8; font-size:1.15rem; margin-top:-10px;'>Premium Wealth & Portfolio Advisory Intelligence</p>", unsafe_allow_html=True)

# KPIs — aggregate across all holders
total_sip = sum(float(h.get('SIP') or 0) for h in portfolio.get('holders', []))
total_cost = sum(float(h.get('Cost of Investment') or 0) for h in portfolio.get('holders', []))
total_current = sum(float(h.get('Current Value') or 0) for h in portfolio.get('holders', []))
weighted_xirr_sum = sum(float(h.get('XIRR') or 0) * float(h.get('Current Value') or 0) for h in portfolio.get('holders', []))
avg_xirr = (weighted_xirr_sum / total_current) if total_current > 0 else 0

net_gain = total_current - total_cost
gain_percentage = (net_gain / total_cost * 100) if total_cost > 0 else 0

# Render KPI cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Active monthly SIP</div>
        <div class="kpi-value">₹{total_sip:,.2f}</div>
        <div class="kpi-delta delta-up">Recurring Wealth Growth</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Cost of Investment</div>
        <div class="kpi-value">₹{total_cost:,.2f}</div>
        <div class="kpi-delta">Principal Amount</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Current Value</div>
        <div class="kpi-value">₹{total_current:,.2f}</div>
        <div class="kpi-delta {"delta-up" if net_gain >= 0 else "delta-down"}">
            {"▲" if net_gain >= 0 else "▼"} ₹{abs(net_gain):,.2f} ({gain_percentage:.2f}%)
        </div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Portfolio XIRR</div>
        <div class="kpi-value">{avg_xirr:.2f}%</div>
        <div class="kpi-delta delta-up">Annualised Return Rate</div>
    </div>
    """, unsafe_allow_html=True)


# ----------------------------------------------------
# 5. CHATBOT INTERFACE
# ----------------------------------------------------
st.markdown("<h3 style='color:#c7d2fe; font-weight:600; margin-top:20px;'>🤖 Wealth Advisor Chat</h3>", unsafe_allow_html=True)

# Initialise chat logs & active chat name
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'chat_name' not in st.session_state:
    st.session_state.chat_name = ""

# ── Name Entry Row ────────────────────────────────────────────────────────────
name_col, greet_col = st.columns([2, 3])

with name_col:
    name_options = [""] + holders_list
    default_idx = 0

    chat_name_input = st.selectbox(
        "👤 Who are you asking for?",
        options=name_options,
        index=default_idx,
        format_func=lambda x: "— Select a person —" if x == "" else x,
        key="chat_name_select",
        help="Choose a family member to get answers specific to their portfolio."
    )
    st.session_state.chat_name = chat_name_input

with greet_col:
    if st.session_state.chat_name:
        first_name = st.session_state.chat_name.split()[0].title()
        st.markdown(
            f"""<div style='
                background: linear-gradient(135deg, rgba(99,102,241,0.2), rgba(139,92,246,0.2));
                border: 1px solid rgba(139,92,246,0.4);
                border-radius: 12px;
                padding: 14px 20px;
                margin-top: 28px;
                color: #c7d2fe;
                font-size: 0.95rem;
            '>
            ✅ <b>Focused on {first_name}</b> — all answers will be based on {st.session_state.chat_name}'s portfolio only.
            </div>""",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """<div style='
                background: rgba(255,255,255,0.03);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 12px;
                padding: 14px 20px;
                margin-top: 28px;
                color: #64748b;
                font-size: 0.95rem;
            '>
            ℹ️ No person selected — answers will cover the <b>entire family portfolio</b>.
            </div>""",
            unsafe_allow_html=True
        )

st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)

# ── Predefined Question Panel ─────────────────────────────────────────────────
client_label = st.session_state.chat_name.split()[0].title() if st.session_state.chat_name else "my"

# Categorised FAQ bank  (use {name} as placeholder → replaced at runtime)
FAQ_CATEGORIES = [
    {
        "icon": "📊",
        "label": "Portfolio Overview",
        "questions": [
            "What is {name} total portfolio value?",
            "What is {name} overall XIRR / annualised return?",
            "How much has {name} invested so far (cost of investment)?",
            "What is the total gain or loss in {name} portfolio?",
        ]
    },
    {
        "icon": "💳",
        "label": "SIP & Investments",
        "questions": [
            "Show all active SIPs for {name}",
            "What is the monthly SIP amount for {name}?",
            "Which SIPs are currently paused or stopped?",
        ]
    },
    {
        "icon": "🏆",
        "label": "Performance & Schemes",
        "questions": [
            "Which scheme is performing best for {name}?",
            "Which fund has the highest unrealised gain?",
            "List all equity funds in {name} portfolio",
            "Which funds are giving negative returns?",
        ]
    },
    {
        "icon": "💡",
        "label": "Advice & Recommendations",
        "questions": [
            "Suggest portfolio improvements for {name}",
            "Is {name} portfolio well diversified?",
            "Should {name} increase SIP amount based on current performance?",
            "What is the risk profile of {name} portfolio?",
        ]
    },
]

selected_query = None

st.markdown("""
<div class="faq-wrapper">
    <div style="color:#c7d2fe; font-weight:700; font-size:0.97rem; margin-bottom:4px;">💡 Quick Questions — click to get an instant answer</div>
    <div style="color:#64748b; font-size:0.82rem; margin-bottom:10px;">No typing needed — select a question below and the advisor will answer immediately.</div>
</div>
""", unsafe_allow_html=True)

COLS_PER_ROW = 2   # max pills per row — keeps text readable

for category in FAQ_CATEGORIES:
    # Category header
    st.markdown(
        f'<div class="faq-category">{category["icon"]} {category["label"]}</div>',
        unsafe_allow_html=True
    )
    questions = category["questions"]
    # Chunk into rows of COLS_PER_ROW
    for row_start in range(0, len(questions), COLS_PER_ROW):
        row_qs = questions[row_start : row_start + COLS_PER_ROW]
        cols = st.columns(COLS_PER_ROW)
        for col_idx, raw_q in enumerate(row_qs):
            display_q = raw_q.replace("{name}", f"{client_label}'s") if client_label != "my" else raw_q
            global_idx = row_start + col_idx
            if cols[col_idx].button(display_q, key=f"faq_{category['label']}_{global_idx}"):
                selected_query = display_q
        # Fill remaining column(s) in last row with empty space so layout stays clean
        for empty_col in range(len(row_qs), COLS_PER_ROW):
            cols[empty_col].empty()

st.markdown("<div style='margin-top:6px'></div>", unsafe_allow_html=True)

# Input text box
user_input = st.text_input(
    "✍️ Or type your own question about investments, schemes, nominees or recommendations",
    key="chat_input",
    placeholder="e.g. What is the exit load on my HDFC Flexi Cap fund?"
)

# Handle user question
if selected_query or user_input:
    actual_query = user_input if user_input else selected_query

    import ollama as _ollama

    # Name Detection: Priority 1=Selectbox, 2=Query text, 3=Sidebar
    detected_name = None

    if st.session_state.get('chat_name'):
        # P1: Selectbox explicitly chosen by user
        detected_name = st.session_state.chat_name
    else:
        # P2: Scan query text for a holder name
        query_lower = actual_query.lower()
        for holder in holders_list:
            for part in holder.split():
                if len(part) > 2 and part.lower() in query_lower:
                    detected_name = holder
                    break
            if detected_name:
                break

    # ── Build Context-Aware System Prompt ────────────────────────────────────
    if detected_name:
        # Focused: only this holder's data goes to the LLM
        compact_data = analyzer._generate_compact_summary_for_holder(detected_name)
        system_prompt = (
            f"You are a Mutual Fund Advisor exclusively assisting {detected_name}.\n"
            f"IMPORTANT: Only answer based on {detected_name}'s data below. "
            f"Do NOT include or mention any other family member's data.\n\n"
            f"{compact_data}\n\n"
            "Rules:\n"
            "- Use ONLY exact figures from the data above.\n"
            "- Address the client by their first name.\n"
            "- Be concise and professional.\n"
            f"- If the query is about someone else entirely, politely clarify that you only have {detected_name}'s data loaded."
        )
        rich_query = f"[Client: {detected_name}] {actual_query}"
    else:
        # Full family view
        compact_data = analyzer._generate_compact_summary()
        system_prompt = (
            "You are a Mutual Fund Advisor for the entire family portfolio.\n"
            f"{compact_data}\n\n"
            "Rules: Use exact figures from above data. Be concise. Address clients by name."
        )
        rich_query = f"[Context: All Family Members] {actual_query}"

    try:
        with st.spinner(f"Thinking about {'**' + detected_name + '**' if detected_name else 'family portfolio'}..."):
            response = _ollama.chat(
                model="llama3",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": rich_query}
                ],
                stream=False,
                options={"num_predict": 512}
            )
        full_response = response["message"]["content"]
    except Exception as e:
        full_response = f"Error contacting Ollama: {e}. Please make sure Ollama is running."

    # Save to history — display loop below renders them
    st.session_state.chat_history.append({"role": "user", "text": actual_query})
    st.session_state.chat_history.append({"role": "bot", "text": full_response})

# Display chat history (chronological order: user message then bot response)
if st.session_state.chat_history:
    for chat in st.session_state.chat_history:
        if chat["role"] == "user":
            st.markdown(f'<div class="chat-bubble chat-user"><b>You:</b><br>{chat["text"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-bubble chat-bot"><b>Wealth Advisor:</b><br>{chat["text"]}</div>', unsafe_allow_html=True)

# ----------------------------------------------------
# 6. PORTFOLIO SCHEMES DETAIL TABLE
# ----------------------------------------------------
selected_person = st.session_state.get('chat_name', '')
if selected_person and 'portfolio_schemes' in portfolio:
    st.markdown("<h3 style='color:#c7d2fe; font-weight:600; margin-top:30px;'>📋 Detailed Holdings</h3>", unsafe_allow_html=True)
    client_schemes = portfolio['portfolio_schemes'].get(selected_person, [])
    if client_schemes:
        st.dataframe(pd.DataFrame(client_schemes), use_container_width=True)
