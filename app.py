from flask import Flask, render_template, request, jsonify, session
from pathlib import Path
from financialAnalyzer import FinancialAnalyzer
from dotenv import load_dotenv
import os
import subprocess
import sys
import datetime
import uuid
import ollama
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "0"
from playwright.sync_api import sync_playwright

load_dotenv()

OLLAMA_HOST = os.getenv(
    "OLLAMA_HOST",
    "http://localhost:11434"
)

ollama_client = ollama.Client(host=OLLAMA_HOST)

from playwright.sync_api import sync_playwright


app = Flask(__name__)

# Required for Flask sessions
app.secret_key = os.environ.get("SECRET_KEY", "financial-analyzer-secret-key")


# ============================================================
# CONFIG
# ============================================================

URL = "https://www.money2management.com/"

DOWNLOAD_DIR = os.path.join("/tmp", "Data")
USERNAME = os.environ.get("M2M_USERNAME")
PASSWORD = os.environ.get("M2M_PASSWORD")
EMAIL = os.environ.get("M2M_EMAIL")
_playwright_checked = False



# ============================================================
# DOWNLOAD PORTFOLIO
# ============================================================

def run_server_download(client_name):


    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        context = browser.new_context(
            accept_downloads=True
        )

        context.set_default_timeout(120000)

        context.set_default_navigation_timeout(
            120000
        )

        page = context.new_page()

        # ----------------------------------------------------
        # Open website
        # ----------------------------------------------------

        page.goto(URL)

        page.wait_for_selector(
            "input[type='text']"
        )

        # ----------------------------------------------------
        # Login
        # ----------------------------------------------------

        page.get_by_role(
            "textbox",
            name="Email"
        ).fill(EMAIL)

        page.get_by_role(
            "textbox",
            name="Username"
        ).fill(USERNAME)

        page.get_by_role(
            "textbox",
            name="Password"
        ).fill(PASSWORD)

        page.get_by_role(
            "button",
            name="Login"
        ).click()

        # ----------------------------------------------------
        # Portfolio Management
        # ----------------------------------------------------

        page.goto(
            "https://www.money2management.com/MF_MutualFundPortFoilo.aspx"
        )

        page.wait_for_selector(
            "#ctl00_ContentPlaceHolder1_rbtn_clienttype_1"
        )

        page.check(
            "#ctl00_ContentPlaceHolder1_rbtn_clienttype_1"
        )

        # ----------------------------------------------------
        # Wait for client dropdown
        # ----------------------------------------------------

        page.wait_for_selector(
            "#ctl00_ContentPlaceHolder1_drp_ClientName option[value]",
            state="attached"
        )

        page.wait_for_timeout(3000)

        options = page.locator(
            "#ctl00_ContentPlaceHolder1_drp_ClientName option"
        ).element_handles()

        selected_value = None

        # ----------------------------------------------------
        # 1. Exact match
        # ----------------------------------------------------

        for opt in options:

            text = opt.text_content()

            if text:

                parts = [
                    p.strip()
                    for p in text.split(" - ")
                ]

                extracted_name = (
                    parts[1]
                    if len(parts) >= 2
                    else text
                )

                norm_extracted = " ".join(
                    extracted_name.lower().split()
                )

                norm_client = " ".join(
                    client_name.lower().split()
                )

                if norm_extracted == norm_client:

                    selected_value = (
                        opt.get_attribute("value")
                    )

                    break

        # ----------------------------------------------------
        # 2. Full text exact
        # ----------------------------------------------------

        if not selected_value:

            for opt in options:

                text = opt.text_content()

                if text:

                    norm_text = " ".join(
                        text.lower().split()
                    )

                    norm_client = " ".join(
                        client_name.lower().split()
                    )

                    if norm_text == norm_client:

                        selected_value = (
                            opt.get_attribute("value")
                        )

                        break

        # ----------------------------------------------------
        # 3. Partial fallback
        # ----------------------------------------------------

        if not selected_value:

            for opt in options:

                text = opt.text_content()

                if text:

                    norm_text = " ".join(
                        text.lower().split()
                    )

                    norm_client = " ".join(
                        client_name.lower().split()
                    )

                    if norm_client in norm_text:

                        selected_value = (
                            opt.get_attribute("value")
                        )

                        break

        # ----------------------------------------------------
        # Client not found
        # ----------------------------------------------------

        if not selected_value:

            browser.close()

            raise Exception(
                f"Could not find client matching '{client_name}'"
            )

        # ----------------------------------------------------
        # Select client
        # ----------------------------------------------------

        page.evaluate(
            f"""
            const el = document.getElementById(
                'ctl00_ContentPlaceHolder1_drp_ClientName'
            );

            el.value = '{selected_value}';

            el.dispatchEvent(
                new Event('change')
            );
            """
        )

        page.wait_for_selector(
            "#ctl00_ContentPlaceHolder1_btn_export_excel"
        )

        # ----------------------------------------------------
        # Download Excel
        # ----------------------------------------------------

        with page.expect_download(
            timeout=120000
        ) as download_info:

            page.locator(
                "#ctl00_ContentPlaceHolder1_btn_export_excel"
            ).click()

        download = download_info.value

        os.makedirs(
            DOWNLOAD_DIR,
            exist_ok=True
        )

        today_str = datetime.datetime.now().strftime(
            "%Y-%m-%d"
        )

        safe_name = "".join(
            c if c.isalnum() else "_"
            for c in client_name
        )

        file_path = os.path.join(
            DOWNLOAD_DIR,
            f"Portfolio_{safe_name}_{today_str}.xls"
        )

        download.save_as(file_path)

        browser.close()

        return file_path


# ============================================================
# LOAD ANALYZER
# ============================================================

def load_analyzer(file_path):

    try:

        analyzer = FinancialAnalyzer(
            Path(file_path)
        )

        return analyzer

    except Exception as e:

        print(
            "Error loading portfolio:",
            e
        )

        return None


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():

    return render_template(
        "index.html",
        portfolio=None,
        holders=[],
        client_name=None
    )


# ============================================================
# FETCH CLIENT PORTFOLIO
# ============================================================

@app.route(
    "/fetch-portfolio",
    methods=["POST"]
)
def fetch_portfolio():

    client_name = request.form.get(
        "client_name",
        ""
    ).strip()

    if not client_name:

        return jsonify({
            "success": False,
            "error": "Please enter client name."
        })

    try:

        # ----------------------------------------------------
        # Download Excel
        # ----------------------------------------------------

        file_path = run_server_download(
            client_name
        )

        # ----------------------------------------------------
        # Load FinancialAnalyzer
        # ----------------------------------------------------

        analyzer = load_analyzer(
            file_path
        )

        if analyzer is None:

            return jsonify({
                "success": False,
                "error": "Could not parse portfolio data."
            })

        # ----------------------------------------------------
        # Generate session ID
        # ----------------------------------------------------

        portfolio_id = str(
            uuid.uuid4()
        )

        session["portfolio_id"] = portfolio_id

        session["file_path"] = file_path

        session["client_name"] = client_name

        session["chat_history"] = []

        return jsonify({
            "success": True,
            "client_name": client_name,
            "message": "Portfolio loaded successfully."
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        })


# ============================================================
# GET PORTFOLIO DATA
# ============================================================

@app.route(
    "/portfolio",
    methods=["GET"]
)
def portfolio():

    file_path = session.get(
        "file_path"
    )

    client_name = session.get(
        "client_name"
    )

    if not file_path:

        return jsonify({
            "success": False,
            "error": "No portfolio loaded."
        })

    analyzer = load_analyzer(
        file_path
    )

    if analyzer is None:

        return jsonify({
            "success": False,
            "error": "Could not load portfolio."
        })

    portfolio_data = analyzer.portfolio_data

    holders_list = []

    if "holders" in portfolio_data:

        holders_list = [
            h["Holder Name"]
            for h in portfolio_data["holders"]
            if h.get("Holder Name")
        ]

    # --------------------------------------------------------
    # KPI calculations
    # --------------------------------------------------------

    total_sip = sum(
        float(h.get("SIP") or 0)
        for h in portfolio_data.get(
            "holders",
            []
        )
    )

    total_cost = sum(
        float(h.get("Cost of Investment") or 0)
        for h in portfolio_data.get(
            "holders",
            []
        )
    )

    total_current = sum(
        float(h.get("Current Value") or 0)
        for h in portfolio_data.get(
            "holders",
            []
        )
    )

    weighted_xirr_sum = sum(
        float(h.get("XIRR") or 0)
        *
        float(h.get("Current Value") or 0)
        for h in portfolio_data.get(
            "holders",
            []
        )
    )

    avg_xirr = (
        weighted_xirr_sum / total_current
        if total_current > 0
        else 0
    )

    net_gain = (
        total_current - total_cost
    )

    gain_percentage = (
        net_gain / total_cost * 100
        if total_cost > 0
        else 0
    )

    return jsonify({

        "success": True,

        "client_name": client_name,

        "holders": holders_list,

        "metrics": {

            "total_sip": total_sip,

            "total_cost": total_cost,

            "total_current": total_current,

            "avg_xirr": avg_xirr,

            "net_gain": net_gain,

            "gain_percentage": gain_percentage

        }

    })


# ============================================================
# CHATBOT
# ============================================================

@app.route(
    "/chat",
    methods=["POST"]
)
def chat():

    data = request.get_json()

    actual_query = data.get(
        "message",
        ""
    ).strip()

    selected_name = data.get(
        "chat_name",
        ""
    ).strip()

    if not actual_query:

        return jsonify({
            "success": False,
            "error": "Please enter a question."
        })

    # --------------------------------------------------------
    # Load analyzer
    # --------------------------------------------------------

    file_path = session.get(
        "file_path"
    )

    if not file_path:

        return jsonify({
            "success": False,
            "error": "Please load a portfolio first."
        })

    analyzer = load_analyzer(
        file_path
    )

    if analyzer is None:

        return jsonify({
            "success": False,
            "error": "Could not load portfolio."
        })

    portfolio = analyzer.portfolio_data

    # --------------------------------------------------------
    # Extract holders
    # --------------------------------------------------------

    holders_list = []

    if "holders" in portfolio:

        holders_list = [
            h["Holder Name"]
            for h in portfolio["holders"]
            if h.get("Holder Name")
        ]

    # --------------------------------------------------------
    # Name Detection
    # Priority:
    # 1. Selected name
    # 2. Query text
    # --------------------------------------------------------

    detected_name = None

    if selected_name:

        detected_name = selected_name

    else:

        query_lower = actual_query.lower()

        for holder in holders_list:

            for part in holder.split():

                if (
                    len(part) > 2
                    and part.lower()
                    in query_lower
                ):

                    detected_name = holder

                    break

            if detected_name:

                break

    # --------------------------------------------------------
    # Build context-aware system prompt
    # --------------------------------------------------------

    if detected_name:

        compact_data = (
            analyzer
            ._generate_compact_summary_for_holder(
                detected_name
            )
        )

        system_prompt = (

            f"You are a Mutual Fund Advisor "
            f"exclusively assisting {detected_name}.\n"

            f"IMPORTANT: Only answer based on "
            f"{detected_name}'s data below. "

            f"Do NOT include or mention any other "
            f"family member's data.\n\n"

            f"{compact_data}\n\n"

            "Rules:\n"

            "- Use ONLY exact figures from the data above.\n"

            "- Address the client by their first name.\n"

            "- Be concise and professional.\n"

            f"- If the query is about someone else entirely, "
            f"politely clarify that you only have "
            f"{detected_name}'s data loaded."

        )

        rich_query = (
            f"[Client: {detected_name}] "
            f"{actual_query}"
        )

    else:

        compact_data = (
            analyzer
            ._generate_compact_summary()
        )

        system_prompt = (

            "You are a Mutual Fund Advisor "
            "for the entire family portfolio.\n"

            f"{compact_data}\n\n"

            "Rules: Use exact figures from above data. "
            "Be concise. Address clients by name."

        )

        rich_query = (
            "[Context: All Family Members] "
            f"{actual_query}"
        )

    # --------------------------------------------------------
    # Ollama
    # --------------------------------------------------------

    try:


        response = ollama_client.chat(

            model="llama3",

            messages=[

                {
                    "role": "system",
                    "content": system_prompt
                },

                {
                    "role": "user",
                    "content": rich_query
                }

            ],

            stream=False,

            options={
                "num_predict": 512
            }

        )

        full_response = (
            response["message"]["content"]
        )

    except Exception as e:

        full_response = (
            f"Error contacting Ollama: {e}. "
            "Please make sure Ollama is running."
        )

    # --------------------------------------------------------
    # Save history
    # --------------------------------------------------------

    if "chat_history" not in session:

        session["chat_history"] = []

    session["chat_history"].append({

        "role": "user",

        "text": actual_query

    })

    session["chat_history"].append({

        "role": "bot",

        "text": full_response

    })

    session.modified = True

    return jsonify({

        "success": True,

        "question": actual_query,

        "answer": full_response,

        "detected_name": detected_name

    })


# ============================================================
# RESET CLIENT
# ============================================================

@app.route(
    "/reset",
    methods=["POST"]
)
def reset():

    session.clear()

    return jsonify({
        "success": True
    })


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    # NOTE: use_reloader=False is required because Playwright's
    # sync_playwright is incompatible with Werkzeug's auto-reloader
    # on Windows — the reloader forks a child process that breaks
    # the Chromium browser launch, causing "Failed to fetch".
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        use_reloader=False
    )