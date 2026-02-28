"""
UFDRINSIGHT — Single-file Streamlit App
Run: python -m streamlit run app.py
Login: admin / admin123
"""
import streamlit as st
import time, base64, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

from database import init_db, login_user, register_user, save_analysis, get_history, get_pdf, delete_analysis

st.set_page_config(page_title="UFDRINSIGHT", page_icon="🔍", layout="wide",
                   initial_sidebar_state="collapsed")
init_db()

# ══════════════════════════════════════════════════════
# SHARED CSS
# ══════════════════════════════════════════════════════
st.markdown("""<style>
.stApp{background:#0a0e27;color:#fff}
.block-container{padding-top:0 !important;max-width:100% !important}
#MainMenu,footer,header{visibility:hidden}
section[data-testid="stSidebar"]{display:none !important}
.stSpinner>div{border-top-color:#00d9ff !important}
/* inputs */
div[data-testid="stTextInput"] input,div[data-testid="stTextArea"] textarea{
  background:#0a0e27 !important;border:1px solid #1a2550 !important;
  color:#fff !important;border-radius:8px !important}
div[data-testid="stTextInput"] input:focus,div[data-testid="stTextArea"] textarea:focus{
  border-color:#00d9ff !important}
label{color:#8892b0 !important;font-size:.82rem !important}
/* buttons */
.stButton>button{background:transparent;border:1px solid #1a2550;color:#ccd6f6;
  border-radius:7px;font-size:.85rem}
.stButton>button:hover{border-color:#00d9ff;color:#00d9ff}
.stDownloadButton>button{background:transparent;border:1px solid #00d9ff;
  color:#00d9ff;border-radius:7px;font-weight:600}
.stDownloadButton>button:hover{background:#00d9ff;color:#0a0e27}
/* file uploader */
[data-testid="stFileUploader"]{background:#0a0e27;border:2px dashed #1a2550;border-radius:10px}
/* tabs */
.stTabs [data-baseweb="tab"]{background:transparent;color:#8892b0;font-weight:600}
.stTabs [aria-selected="true"]{color:#00d9ff !important}
.stTabs [data-baseweb="tab-list"]{background:transparent}
</style>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# SESSION STATE DEFAULTS
# ══════════════════════════════════════════════════════
if "page"       not in st.session_state: st.session_state.page      = "login"
if "logged_in"  not in st.session_state: st.session_state.logged_in = False
if "username"   not in st.session_state: st.session_state.username  = ""
if "result"     not in st.session_state: st.session_state.result    = None

def goto(page):
    st.session_state.page = page
    st.rerun()

# ══════════════════════════════════════════════════════
# NAVBAR (shown on dashboard + history)
# ══════════════════════════════════════════════════════
def navbar():
    l, _, r = st.columns([3, 4, 3])
    with l:
        st.markdown("""<div style='padding:10px 0 2px 0'>
          <span style='font-size:1.4rem;font-weight:900;color:#fff'>🔍 UFDR<span style='color:#00d9ff'>INSIGHT</span></span><br>
          <span style='font-size:.7rem;color:#8892b0;text-transform:uppercase;letter-spacing:.08em'>
            Forensic Intelligence Platform</span></div>""", unsafe_allow_html=True)
    with r:
        c1,c2,c3 = st.columns(3)
        with c1:
            if st.button("🏠 Home", use_container_width=True):
                st.session_state.result = None
                goto("dashboard")
        with c2:
            if st.button("🗄️ History", use_container_width=True):
                goto("history")
        with c3:
            if st.button("↩️ Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.username  = ""
                st.session_state.result    = None
                goto("login")
    st.markdown(f"<div style='text-align:right;font-size:.75rem;color:#4a5580;margin-top:-6px;margin-bottom:12px'>"
                f"Logged in as <strong style='color:#00d9ff'>{st.session_state.username}</strong></div>",
                unsafe_allow_html=True)
    st.markdown("<hr style='border-color:#1a2550;margin:0 0 20px 0'>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# PAGE: LOGIN
# ══════════════════════════════════════════════════════
def page_login():
    if st.session_state.logged_in:
        goto("dashboard")

    _, center, _ = st.columns([1,1,1])
    with center:
        st.markdown("<div style='height:50px'></div>", unsafe_allow_html=True)
        st.markdown("""<div style='text-align:center;margin-bottom:28px'>
          <div style='font-size:2.2rem;font-weight:900;color:#fff'>
            🔍 UFDR<span style='color:#00d9ff'>INSIGHT</span></div>
          <div style='font-size:.8rem;color:#8892b0;margin-top:4px;
            text-transform:uppercase;letter-spacing:.08em'>
            Forensic Intelligence Platform</div></div>""", unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["🔐  Login", "📝  Register"])

        with tab1:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            uname = st.text_input("Username", key="l_user", placeholder="Enter username")
            passw = st.text_input("Password", key="l_pass", placeholder="Enter password", type="password")
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            if st.button("Login →", key="btn_login", use_container_width=True):
                if not uname or not passw:
                    st.error("Please enter username and password.")
                elif login_user(uname, passw):
                    st.session_state.logged_in = True
                    st.session_state.username  = uname
                    goto("dashboard")
                else:
                    st.error("❌ Wrong username or password.")
            st.markdown("""<div style='text-align:center;margin-top:14px;
              color:#4a5580;font-size:.78rem'>
              Demo: <span style='color:#00d9ff'>admin</span> /
              <span style='color:#00d9ff'>admin123</span></div>""", unsafe_allow_html=True)

        with tab2:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            nu = st.text_input("Username", key="r_user", placeholder="Choose a username")
            np = st.text_input("Password", key="r_pass", placeholder="Min 4 characters", type="password")
            np2 = st.text_input("Confirm", key="r_pass2", placeholder="Repeat password", type="password")
            if st.button("Create Account →", key="btn_reg", use_container_width=True):
                if not nu or not np:
                    st.error("Fill in all fields.")
                elif np != np2:
                    st.error("Passwords don't match.")
                else:
                    ok, msg = register_user(nu, np)
                    if ok: st.success(f"✅ {msg} Now login.")
                    else:  st.error(f"❌ {msg}")

        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center;color:#2a3060;font-size:.7rem'>"
                    "UFDRINSIGHT · For Authorized Use Only</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ══════════════════════════════════════════════════════
def page_dashboard():
    if not st.session_state.logged_in:
        goto("login")

    navbar()

    # Page title
    st.markdown("""<div style='text-align:center;padding:0 0 24px 0'>
      <div style='font-size:1.7rem;font-weight:800;color:#fff'>Upload & Analyze UFDR File</div>
      <div style='font-size:.9rem;color:#8892b0;margin-top:6px'>
        Upload a forensic export to generate instant AI-powered intelligence</div></div>""",
      unsafe_allow_html=True)

    # ── 3 Upload Boxes ─────────────────────────────────
    def box(icon, title, desc):
        st.markdown(f"""<div style='background:#111936;border:1px solid #1a2550;border-radius:12px;
          padding:18px 16px;border-top:3px solid #00d9ff;margin-bottom:6px'>
          <div style='font-size:1.6rem'>{icon}</div>
          <div style='font-size:.82rem;font-weight:700;color:#00d9ff;
            text-transform:uppercase;letter-spacing:.06em;margin:6px 0 3px 0'>{title}</div>
          <div style='font-size:.75rem;color:#4a5580'>{desc}</div></div>""",
          unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3, gap="large")
    with col1:
        box("📋","File Name","Give this analysis a name")
        file_name = st.text_input("fn", label_visibility="collapsed",
                    placeholder="e.g. Case 2024-001 — Suspect Phone", key="inp_fn")
    with col2:
        box("📝","Description","Add context about this case")
        description = st.text_area("desc", label_visibility="collapsed",
                      placeholder="e.g. iPhone extracted from suspect on Jan 15. Fraud case.",
                      key="inp_desc", height=80)
    with col3:
        box("📁","Upload UFDR File","Drag & drop or click (.zip)")
        uploaded = st.file_uploader("uploader", label_visibility="collapsed",
                   type=["zip"], key="uploader")

    st.markdown("<br>", unsafe_allow_html=True)
    _, bcol, _ = st.columns([1,2,1])
    with bcol:
        go = st.button("🔍  Analyze UFDR File", use_container_width=True, key="btn_analyze")

    if go:
        if not uploaded:
            st.error("Please upload a .zip UFDR file.")
            return
        if not file_name.strip():
            st.warning("Please enter a file name.")
            return

        # ── Run pipeline ────────────────────────────────
        prog = st.progress(0)
        stat = st.empty()

        def step(msg, val):
            stat.markdown(f"<div style='color:#8892b0;font-size:.85rem'>{msg}</div>",
                          unsafe_allow_html=True)
            prog.progress(val)
            time.sleep(0.2)

        step("📦 Extracting archive...", 0.1)
        from parser import parse_ufdr
        parsed = parse_ufdr(uploaded.read())

        if parsed["messages"].empty:
            prog.empty(); stat.empty()
            st.error("❌ No messages found in this file.")
            with st.expander("🔍 Technical details"):
                for e in parsed["errors"]: st.code(e)
                st.info("Try: python generate_ufdr.py — then upload sample_ufdr.zip")
            return

        step("📊 Aggregating metrics...", 0.35)
        from aggregator import aggregate
        metrics = aggregate(parsed["messages"], parsed["calls"], parsed["metadata"])

        step("🤖 Generating AI summary...", 0.55)
        from ai_summary import generate_summary
        summary = generate_summary(metrics)

        step("⚠️  Detecting risk signals...", 0.72)
        from risk_detector import detect_risks
        risks = detect_risks(metrics)

        step("🕸️  Building network graph...", 0.85)
        from network_graph import generate_network_graph
        graph = generate_network_graph(metrics)

        step("📄  Generating PDF...", 0.95)
        from pdf_generator import generate_pdf
        pdf = generate_pdf(metrics, summary, risks, graph)

        save_analysis(st.session_state.username, file_name.strip(),
                      description.strip(), metrics, summary, risks, pdf)

        prog.progress(1.0)
        stat.markdown("<div style='color:#2ed573;font-size:.85rem'>✅ Done!</div>",
                      unsafe_allow_html=True)
        time.sleep(0.4)
        prog.empty(); stat.empty()

        st.session_state.result = {
            "metrics": metrics, "summary": summary, "risks": risks,
            "graph": graph, "pdf": pdf, "file_name": file_name.strip()
        }
        st.rerun()

    # ── Show Results ──────────────────────────────────
    res = st.session_state.result
    if not res:
        st.markdown("""<div style='text-align:center;padding:50px 0;color:#2a3060'>
          <div style='font-size:3.5rem'>🔍</div>
          <div style='margin-top:10px;font-size:.9rem'>
            Fill in the details above and upload a UFDR file<br>
            <span style='color:#1a2550;font-size:.8rem'>
              No file? Run <code style='color:#00d9ff'>python generate_ufdr.py</code>
            </span></div></div>""", unsafe_allow_html=True)
        return

    m      = res["metrics"]
    graph  = res["graph"]
    pdf    = res["pdf"]

    st.markdown(f"<div style='text-align:right;font-size:.78rem;color:#2ed573;margin-bottom:14px'>"
                f"✅ Analysis: <span style='color:#8892b0'>{res['file_name']}</span></div>",
                unsafe_allow_html=True)

    # KPI cards
    kpis = [
        ("Total Messages",   m.get("total_messages",0),            ""),
        ("Total Calls",      m.get("total_calls",0),               ""),
        ("Unique Contacts",  m.get("unique_contacts",0),           ""),
        ("Days Active",      m.get("days_active",0),               ""),
        ("Night Activity",   f"{m.get('night_activity_pct',0)}%",  ""),
        ("Daily Average",    m.get("avg_daily_messages",0),        "msgs"),
    ]
    for col, (lbl, val, unit) in zip(st.columns(6), kpis):
        with col:
            st.markdown(f"""<div style='background:#111936;border:1px solid #1a2550;
              border-radius:8px;padding:14px 10px;text-align:center;border-top:3px solid #00d9ff'>
              <div style='font-size:1.8rem;font-weight:700;color:#00d9ff;line-height:1'>
                {val}<span style='font-size:.75rem;color:#8892b0'> {unit}</span></div>
              <div style='font-size:.68rem;color:#8892b0;margin-top:4px;
                text-transform:uppercase;letter-spacing:.05em'>{lbl}</div></div>""",
              unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    left, right = st.columns([3,2])

    with left:
        # Executive Summary
        st.markdown("<div style='font-size:.9rem;font-weight:700;color:#00d9ff;"
                    "text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px;"
                    "padding-bottom:6px;border-bottom:1px solid #1a2550'>"
                    "🤖 AI Executive Summary</div>", unsafe_allow_html=True)
        for para in res["summary"].split("\n\n"):
            if para.strip():
                st.markdown(f"<div style='background:#111936;border-left:3px solid #00d9ff;"
                            f"border-radius:0 8px 8px 0;padding:14px 16px;margin-bottom:10px;"
                            f"font-size:.88rem;color:#ccd6f6;line-height:1.7'>{para.strip()}</div>",
                            unsafe_allow_html=True)

        # Timeline chart
        st.markdown("<div style='font-size:.9rem;font-weight:700;color:#00d9ff;"
                    "text-transform:uppercase;letter-spacing:.08em;margin:16px 0 10px 0;"
                    "padding-bottom:6px;border-bottom:1px solid #1a2550'>"
                    "📈 Message Volume Timeline</div>", unsafe_allow_html=True)
        daily_raw = m.get("daily_volume",{})
        if daily_raw:
            df = pd.DataFrame([{"date":pd.to_datetime(k),"count":v}
                                for k,v in daily_raw.items()]).sort_values("date")
            fig, ax = plt.subplots(figsize=(9,3))
            fig.patch.set_facecolor("#111936"); ax.set_facecolor("#111936")
            avg = m.get("avg_daily_messages",0)
            ax.axhline(avg, color="#8892b0", linestyle="--", linewidth=0.8, alpha=0.6)
            ax.fill_between(df["date"], df["count"], alpha=0.15, color="#00d9ff")
            ax.plot(df["date"], df["count"], color="#00d9ff", linewidth=2)
            spike_date = m.get("spike_date")
            if spike_date:
                sd  = pd.to_datetime(spike_date)
                sv  = df[df["date"].dt.date == pd.to_datetime(spike_date).date()]["count"]
                if not sv.empty:
                    ax.scatter([sd],[sv.values[0]],color="#ff4757",s=80,zorder=5)
                    ax.annotate(f"SPIKE +{m.get('spike_increase_pct',0)}%",
                        xy=(sd,sv.values[0]),xytext=(0,10),textcoords="offset points",
                        color="#ff4757",fontsize=7,ha="center",
                        arrowprops=dict(arrowstyle="->",color="#ff4757",lw=0.8))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
            plt.xticks(rotation=30,color="#8892b0",fontsize=7)
            plt.yticks(color="#8892b0",fontsize=7)
            for sp in ax.spines.values(): sp.set_edgecolor("#1a2550")
            ax.set_ylabel("Messages",color="#8892b0",fontsize=7)
            plt.tight_layout(pad=0.5)
            st.pyplot(fig, use_container_width=True); plt.close()

        # Hourly chart
        st.markdown("<div style='font-size:.9rem;font-weight:700;color:#00d9ff;"
                    "text-transform:uppercase;letter-spacing:.08em;margin:16px 0 10px 0;"
                    "padding-bottom:6px;border-bottom:1px solid #1a2550'>"
                    "🕐 Hourly Activity</div>", unsafe_allow_html=True)
        hourly = m.get("hourly_distribution",{})
        if hourly:
            hrs = list(range(24))
            cts = [hourly.get(h,0) for h in hrs]
            cb  = ["#ff475780" if h<=4 else "#00d9ff60" for h in hrs]
            ce  = ["#ff4757"   if h<=4 else "#00d9ff"   for h in hrs]
            fig2,ax2 = plt.subplots(figsize=(9,2.5))
            fig2.patch.set_facecolor("#111936"); ax2.set_facecolor("#111936")
            ax2.bar(hrs,cts,color=cb,edgecolor=ce,linewidth=0.5,width=0.7)
            ax2.axvspan(-0.5,4.5,alpha=0.08,color="#ff4757")
            ax2.set_xticks(hrs)
            ax2.set_xticklabels([f"{h:02d}h" for h in hrs],rotation=45,fontsize=6,color="#8892b0")
            plt.yticks(color="#8892b0",fontsize=7)
            for sp in ax2.spines.values(): sp.set_edgecolor("#1a2550")
            ax2.set_ylabel("Messages",color="#8892b0",fontsize=7)
            plt.tight_layout(pad=0.5)
            st.pyplot(fig2, use_container_width=True); plt.close()

    with right:
        # Risk signals
        st.markdown("<div style='font-size:.9rem;font-weight:700;color:#00d9ff;"
                    "text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px;"
                    "padding-bottom:6px;border-bottom:1px solid #1a2550'>"
                    "⚠️ Risk Signals</div>", unsafe_allow_html=True)
        sc = {"HIGH":"#ff4757","MEDIUM":"#ffa502","INFO":"#00d9ff"}
        for risk in res["risks"]:
            col = sc.get(risk["severity"],"#00d9ff")
            st.markdown(f"""<div style='border-left:4px solid {col};background:#111936;
              border-radius:0 8px 8px 0;padding:12px 14px;margin-bottom:10px'>
              <div style='font-size:.84rem;font-weight:700;color:{col};margin-bottom:5px'>
                {risk['icon']} {risk['flag']}
                <span style='background:{col}22;border:1px solid {col};
                  border-radius:20px;padding:2px 8px;font-size:.65rem;margin-left:6px'>
                  {risk['severity']}</span></div>
              <div style='font-size:.77rem;color:#8892b0;line-height:1.5'>
                {risk['detail']}</div></div>""", unsafe_allow_html=True)

        # Key individuals
        st.markdown("<div style='font-size:.9rem;font-weight:700;color:#00d9ff;"
                    "text-transform:uppercase;letter-spacing:.08em;margin:16px 0 10px 0;"
                    "padding-bottom:6px;border-bottom:1px solid #1a2550'>"
                    "👤 Key Individuals</div>", unsafe_allow_html=True)
        contacts = m.get("top_contacts",[])
        pc = {"HIGH":"#ff4757","MEDIUM":"#ffa502","STANDARD":"#2ed573"}
        rows_html = "".join(f"""<tr>
          <td style='color:#00d9ff;font-weight:700'>#{c['rank']}</td>
          <td>{c['contact_name']}</td>
          <td>{c['messages']}</td>
          <td>{c['calls']}</td>
          <td>{c['msg_pct']}%</td>
          <td style='color:{pc.get(c["priority"],"#2ed573")};font-weight:700'>{c['priority']}</td>
        </tr>""" for c in contacts[:8])
        st.markdown(f"""<table style='width:100%;border-collapse:collapse;font-size:.8rem'>
          <thead><tr style='background:#00d9ff;color:#0a0e27'>
            <th style='padding:7px 8px;text-align:left'>#</th>
            <th style='padding:7px 8px;text-align:left'>Contact</th>
            <th style='padding:7px 8px'>Msgs</th>
            <th style='padding:7px 8px'>Calls</th>
            <th style='padding:7px 8px'>Share</th>
            <th style='padding:7px 8px'>Priority</th></tr></thead>
          <tbody>{rows_html}</tbody></table>""", unsafe_allow_html=True)

    # Network graph
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:.9rem;font-weight:700;color:#00d9ff;"
                "text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px;"
                "padding-bottom:6px;border-bottom:1px solid #1a2550'>"
                "🕸️ Communication Network</div>", unsafe_allow_html=True)
    if graph:
        _, gc, _ = st.columns([1,3,1])
        with gc:
            st.image(base64.b64decode(graph), use_container_width=True,
                     caption="Node size = interaction volume · Edge = frequency")

    # Download PDF
    st.markdown("<br>", unsafe_allow_html=True)
    _, dlc, _ = st.columns([1,2,1])
    with dlc:
        if pdf:
            fname = f"UFDRINSIGHT_{res['file_name'].replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
            st.download_button("⬇️  Download Forensic Intelligence Report (PDF)",
                               data=pdf, file_name=fname,
                               mime="application/pdf", use_container_width=True)
        else:
            st.warning("PDF generation failed — check reportlab is installed.")

    st.markdown("<div style='text-align:center;padding:24px 0 10px;color:#1a2550;font-size:.7rem'>"
                "UFDRINSIGHT · Forensic Intelligence Platform · For Authorized Use Only</div>",
                unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# PAGE: HISTORY
# ══════════════════════════════════════════════════════
def page_history():
    if not st.session_state.logged_in:
        goto("login")

    navbar()

    st.markdown("""<div style='text-align:center;padding:0 0 24px 0'>
      <div style='font-size:1.7rem;font-weight:800;color:#fff'>🗄️ Analysis History</div>
      <div style='font-size:.9rem;color:#8892b0;margin-top:6px'>
        View, download and delete your past forensic analyses</div></div>""",
      unsafe_allow_html=True)

    history = get_history(st.session_state.username)

    if not history:
        st.markdown("""<div style='text-align:center;padding:60px 0;color:#2a3060'>
          <div style='font-size:3.5rem'>🗄️</div>
          <div style='margin-top:10px;font-size:.9rem;color:#4a5580'>No analyses yet.</div>
          <div style='font-size:.8rem;color:#2a3060;margin-top:6px'>
            Go to Home, upload a file to get started.</div></div>""", unsafe_allow_html=True)
        _, bc, _ = st.columns([1,2,1])
        with bc:
            if st.button("→ Go to Dashboard", use_container_width=True):
                goto("dashboard")
        return

    st.markdown(f"<div style='margin-bottom:16px;font-size:.8rem;color:#4a5580'>"
                f"<span style='color:#00d9ff;font-weight:600'>{len(history)}</span> analyses · "
                f"Latest: <span style='color:#8892b0'>{history[0]['analyzed_at']}</span></div>",
                unsafe_allow_html=True)

    for item in history:
        m   = item.get("metrics",{})
        rid = item["id"]

        st.markdown(f"""<div style='background:#111936;border:1px solid #1a2550;
          border-radius:12px;padding:18px 22px;margin-bottom:4px'>
          <div style='font-size:1rem;font-weight:700;color:#fff'>📁 {item['file_name']}</div>
          <div style='font-size:.82rem;color:#8892b0;margin-top:3px'>
            {item.get('description') or '<em>No description</em>'}</div>
          <div style='font-size:.75rem;color:#4a5580;margin-top:8px'>
            🕐 {item['analyzed_at']} &nbsp;·&nbsp;
            💬 <span style='color:#00d9ff'>{m.get('total_messages','—')}</span> messages &nbsp;·&nbsp;
            📞 <span style='color:#00d9ff'>{m.get('total_calls','—')}</span> calls &nbsp;·&nbsp;
            👤 <span style='color:#00d9ff'>{m.get('unique_contacts','—')}</span> contacts
          </div></div>""", unsafe_allow_html=True)

        with st.expander("📄 View Summary & Risks"):
            summ = item.get("summary","")
            if summ:
                for para in summ.split("\n\n"):
                    if para.strip():
                        st.markdown(f"<div style='background:#0a0e27;border-left:3px solid #00d9ff;"
                                    f"padding:10px 14px;margin-bottom:8px;font-size:.85rem;"
                                    f"color:#ccd6f6;line-height:1.7;border-radius:0 6px 6px 0'>"
                                    f"{para.strip()}</div>", unsafe_allow_html=True)
            sc = {"HIGH":"#ff4757","MEDIUM":"#ffa502","INFO":"#00d9ff"}
            for r in item.get("risks",[]):
                col = sc.get(r.get("severity","INFO"),"#00d9ff")
                st.markdown(f"<div style='border-left:3px solid {col};padding:6px 12px;"
                            f"margin:5px 0;background:#0a0e27;border-radius:0 6px 6px 0;"
                            f"font-size:.8rem'><strong style='color:{col}'>"
                            f"{r.get('icon','')} {r['flag']} [{r.get('severity','')}]</strong>"
                            f"<br><span style='color:#8892b0'>{r['detail']}</span></div>",
                            unsafe_allow_html=True)

        a1, a2 = st.columns([2,1])
        with a1:
            pdf_data = get_pdf(rid)
            if pdf_data:
                st.download_button("⬇️ Download PDF",
                    data=pdf_data,
                    file_name=f"UFDRINSIGHT_{item['file_name'].replace(' ','_')}.pdf",
                    mime="application/pdf",
                    key=f"dl_{rid}", use_container_width=True)
        with a2:
            if st.button("🗑️ Delete", key=f"del_{rid}", use_container_width=True):
                delete_analysis(rid)
                st.success("Deleted.")
                time.sleep(0.5)
                st.rerun()

        st.markdown("<hr style='border-color:#1a2550;margin:6px 0 14px 0'>",
                    unsafe_allow_html=True)

    st.markdown("<div style='text-align:center;padding:20px 0 8px;color:#1a2550;font-size:.7rem'>"
                "UFDRINSIGHT · Forensic Intelligence Platform · For Authorized Use Only</div>",
                unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════
page = st.session_state.page
if page == "login":     page_login()
elif page == "dashboard": page_dashboard()
elif page == "history":   page_history()
else:                     page_login()
