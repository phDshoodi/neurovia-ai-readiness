import re
from datetime import datetime, timezone

import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
import numpy as np
import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="NeuroVia | Neural Monitoring Simulator",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

BG = "#060913"
PANEL = "#0f172a"
CYAN = "#00e5ff"
PURPLE = "#8b5cf6"

st.markdown(
    """
    <style>
    .stApp { background: #060913; color: #e2e8f0; }
    [data-testid="stSidebar"] { background: #0a1020; border-right: 1px solid #1e293b; }
    .hero { text-align:center; padding: 8px 0 24px; }
    .hero-icon { font-size: 58px; filter: drop-shadow(0 0 16px #00e5ff); }
    .hero-title { font-size: clamp(30px, 4vw, 48px); font-weight: 850; letter-spacing: -1px;
      background: linear-gradient(110deg, #00e5ff, #3b82f6 55%, #8b5cf6);
      -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin:0; }
    .hero-subtitle { color:#94a3b8; font-size:16px; margin-top:8px; }
    .profile-card { padding:20px; border-radius:16px; text-align:center; margin-bottom:18px;
      background:linear-gradient(145deg,#111b31,#0b1222); border:1px solid #26334b; border-top:4px solid #8b5cf6; }
    .metric-card { background:rgba(30,41,59,.55); border:1px solid #334155; border-radius:13px;
      padding:17px 18px; min-height:94px; }
    .metric-label { color:#94a3b8; font-size:12px; text-transform:uppercase; letter-spacing:.08em; }
    .metric-value { color:#e2e8f0; font-size:23px; font-weight:750; margin-top:7px; }
    .notice { background:rgba(8,145,178,.10); border:1px solid rgba(34,211,238,.35); border-radius:12px;
      padding:14px 16px; color:#bae6fd; margin:8px 0 18px; }
    .stTabs [data-baseweb="tab-list"] { gap:8px; background:#0f172a; padding:8px; border-radius:13px; border:1px solid #1e293b; }
    .stTabs [data-baseweb="tab"] { border-radius:9px; font-weight:650; }
    .small-note { color:#94a3b8; font-size:12px; }
    </style>
    """,
    unsafe_allow_html=True,
)


def brain_map(state: str, seed: int, intensity: float):
    """Render a synthetic cortical activity map; this is not clinical EEG data."""
    rng = np.random.default_rng(seed)
    fig, ax = plt.subplots(figsize=(7, 5.2), facecolor=BG)
    ax.set_facecolor(BG)

    # Stylized head and hemispheres.
    head = Ellipse((0, 0), 5.1, 6.3, facecolor="#0b1427", edgecolor="#334155", linewidth=2)
    left = Ellipse((-1.0, 0.1), 2.45, 4.65, angle=7, fill=False, edgecolor="#2563eb", linewidth=1.5, alpha=.9)
    right = Ellipse((1.0, 0.1), 2.45, 4.65, angle=-7, fill=False, edgecolor="#7c3aed", linewidth=1.5, alpha=.9)
    ax.add_patch(head)
    ax.add_patch(left)
    ax.add_patch(right)
    ax.plot([0, 0], [-2.35, 2.35], color="#334155", linewidth=1, linestyle="--", alpha=.8)

    # Rejection sampling keeps generated electrodes inside the stylized head outline.
    points = []
    while len(points) < 44:
        x, y = rng.uniform(-2.2, 2.2), rng.uniform(-2.7, 2.7)
        if (x / 2.42) ** 2 + (y / 3.02) ** 2 < .83:
            points.append((x, y))
    xy = np.asarray(points)
    values = rng.uniform(.25, .75, len(xy)) * intensity
    palette = {
        "Stable baseline (simulated)": "#34d399",
        "Elevated activity (simulated)": "#fbbf24",
        "Suppression concept (simulated)": CYAN,
    }
    color = palette[state]
    if state == "Elevated activity (simulated)":
        focus = np.sum((xy - np.array([-0.8, 1.0])) ** 2, axis=1) < .75
        values[focus] = np.minimum(1, values[focus] + .55)
        ax.scatter(xy[focus, 0], xy[focus, 1], s=145, c="#ef4444", alpha=.9,
                   edgecolors="#fee2e2", linewidths=.6, zorder=4, label="Synthetic focus")
    if state == "Suppression concept (simulated)":
        for i in range(0, len(xy), 3):
            ax.plot([0, xy[i, 0]], [-2.55, xy[i, 1]], color=CYAN, alpha=.12, linewidth=.8, zorder=1)

    ax.scatter(xy[:, 0], xy[:, 1], c=values, cmap="plasma" if state != "Stable baseline (simulated)" else None,
               color=color if state == "Stable baseline (simulated)" else None,
               s=45 + values * 36, alpha=.9, edgecolors="#e2e8f0", linewidths=.45, zorder=3)
    ax.set_xlim(-3.1, 3.1)
    ax.set_ylim(-3.5, 3.5)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("SYNTHETIC CORTICAL ACTIVITY MAP", color="#e2e8f0", fontsize=12, weight="bold", pad=15)
    fig.tight_layout(pad=1.2)
    return fig


# Small bilingual reference set for local, transparent retrieval. No external model or patient records.
KNOWLEDGE = [
    {
        "en": "NeuroVia in this demo is a prototype interface for exploring simulated neural telemetry. It does not interpret EEG, diagnose seizures, or provide treatment advice.",
        "ar": "NeuroVia في هذا العرض هي واجهة أولية لاستكشاف بيانات عصبية محاكاة. لا تفسر تخطيط الدماغ ولا تشخّص النوبات ولا تقدم نصائح علاجية.",
        "tags": "neurovia prototype demo simulation telemetry purpose",
    },
    {
        "en": "The brain map uses randomly generated points for visualization only. It is not connected to a headband, sensor, patient, or live EEG stream.",
        "ar": "تستخدم خريطة الدماغ نقاطاً مولدة عشوائياً لأغراض العرض فقط. وهي غير متصلة بعصابة رأس أو مستشعر أو مريض أو بث مباشر لتخطيط الدماغ.",
        "tags": "brain map eeg data sensor headband live connection random",
    },
    {
        "en": "The activity states are illustrative scenarios, not validated predictions. Do not rely on them for medical or safety decisions.",
        "ar": "حالات النشاط المعروضة سيناريوهات توضيحية وليست تنبؤات معتمدة. لا تعتمد عليها لاتخاذ قرارات طبية أو متعلقة بالسلامة.",
        "tags": "state elevated activity prediction warning safety medical",
    },
    {
        "en": "The suppression state is a visual concept only. This application does not send signals, control devices, or perform neuromodulation.",
        "ar": "حالة التثبيط مفهوم بصري فقط. لا يرسل هذا التطبيق إشارات ولا يتحكم بالأجهزة ولا ينفذ التعديل العصبي.",
        "tags": "suppression treatment device signal neuromodulation control",
    },
    {
        "en": "Historical logs are stored only in the current Streamlit session and are cleared when the session resets. No emergency service or external endpoint is contacted.",
        "ar": "تُحفظ السجلات التاريخية في جلسة Streamlit الحالية فقط وتُحذف عند إعادة ضبط الجلسة. لا يتم الاتصال بخدمات الطوارئ أو بأي جهة خارجية.",
        "tags": "history logs privacy session storage emergency external",
    },
]


def retrieve_answer(question: str, language: str) -> str:
    words = set(re.findall(r"[\w\u0600-\u06FF]+", question.casefold()))
    ranked = []
    for item in KNOWLEDGE:
        tags = set(re.findall(r"[\w\u0600-\u06FF]+", (item["tags"] + " " + item["en"] + " " + item["ar"]).casefold()))
        ranked.append((len(words & tags), item))
    score, best = max(ranked, key=lambda pair: pair[0])
    if score == 0:
        return (
            "I can answer questions about this demo's simulated map, activity states, local logs, and privacy boundaries. "
            "I don't provide medical interpretation or advice."
            if language == "English"
            else "يمكنني الإجابة عن أسئلة خريطة المحاكاة وحالات النشاط والسجلات المحلية وحدود الخصوصية. لا أقدم تفسيراً أو نصيحة طبية."
        )
    return best["en"] if language == "English" else best["ar"]


if "history" not in st.session_state:
    st.session_state.history = []
if "chat" not in st.session_state:
    st.session_state.chat = []
if "frame_seed" not in st.session_state:
    st.session_state.frame_seed = 17

with st.sidebar:
    st.markdown(
        '<div class="profile-card"><div style="font-size:44px">🧠</div>'
        '<div style="font-size:22px;font-weight:800;color:#f8fafc">Dr. Shahd</div>'
        '<div style="font-size:12px;color:#67e8f9;letter-spacing:1px">NEUROVIA PROJECT</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown("### Simulation controls")
    patient_id = st.text_input("Demo profile label", "Demo-Profile-001", help="A local display label only; do not enter identifiable health information.")
    state = st.selectbox(
        "Synthetic scenario",
        ["Stable baseline (simulated)", "Elevated activity (simulated)", "Suppression concept (simulated)"],
    )
    intensity = st.slider("Visualization intensity", 0.2, 1.0, 0.65, 0.05)
    if st.button("↻ Generate new simulation frame", use_container_width=True):
        st.session_state.frame_seed += 1
    st.divider()
    st.caption("Demo only · No sensors connected · No clinical use")
    st.caption("Session data is temporary and is not sent to an external service.")

st.markdown(
    '<div class="hero"><div class="hero-icon">🧠</div>'
    '<h1 class="hero-title">NeuroVia Core</h1>'
    '<div class="hero-subtitle">Neural telemetry interface concept · Dr. Shahd’s project</div></div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="notice"><strong>Simulation notice:</strong> This prototype uses synthetic data only. '
    'It is not a medical device, seizure predictor, diagnostic tool, or emergency-response system.</div>',
    unsafe_allow_html=True,
)

tab_live, tab_logs, tab_chat, tab_about = st.tabs(
    ["🧠 Live simulation", "📜 Historical logs", "💬 Local RAG assistant", "ⓘ About & safety"]
)

with tab_live:
    c1, c2, c3 = st.columns(3)
    for col, label, value in [
        (c1, "Profile label", patient_id or "Not set"),
        (c2, "Scenario", state.replace(" (simulated)", "")),
        (c3, "Data source", "Synthetic only"),
    ]:
        with col:
            st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>', unsafe_allow_html=True)
    left, right = st.columns([1.05, .95], gap="large")
    with left:
        st.markdown("### Neural activity map")
        st.pyplot(brain_map(state, st.session_state.frame_seed, intensity), use_container_width=True)
        st.caption("Illustrative visualization generated with NumPy and Matplotlib; not real EEG or a physiological map.")
    with right:
        st.markdown("### Scenario summary")
        descriptions = {
            "Stable baseline (simulated)": "A calm synthetic visualization state for demonstrating the interface.",
            "Elevated activity (simulated)": "A visual anomaly scenario with a highlighted synthetic region; it is not a seizure warning.",
            "Suppression concept (simulated)": "A conceptual visualization only; no treatment or device control is performed.",
        }
        st.info(descriptions[state])
        st.markdown("**Interface status:** Demo active · Sensor link: not connected · External actions: disabled")
        if st.button("Add scenario to session log", type="primary"):
            st.session_state.history.insert(0, {
                "Timestamp (UTC)": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                "Profile label": patient_id or "Not set",
                "Scenario": state,
                "Intensity": round(float(intensity), 2),
                "Data source": "Synthetic",
            })
            st.success("Simulation entry added to this session's local history.")

with tab_logs:
    st.markdown("### Historical simulation logs")
    st.caption("Entries exist only in this browser session; this is not a clinical record.")
    if st.session_state.history:
        logs = pd.DataFrame(st.session_state.history)
        st.dataframe(logs, use_container_width=True, hide_index=True)
        st.download_button("Download session log as CSV", logs.to_csv(index=False).encode("utf-8"), "neurovia_simulation_logs.csv", "text/csv")
        if st.button("Clear session logs"):
            st.session_state.history.clear()
            st.rerun()
    else:
        st.info("No simulation entries yet. Add one from the Live simulation tab.")

with tab_chat:
    st.markdown("### NeuroVia reference assistant")
    st.caption("A lightweight local keyword-retrieval demo over the reference notes below. No external AI service is called.")
    language = st.radio("Response language", ["English", "العربية"], horizontal=True)
    response_language = "English" if language == "English" else "العربية"
    for message in st.session_state.chat:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    question = st.chat_input("Ask about the simulation, logs, or data boundaries…")
    if question:
        st.session_state.chat.append({"role": "user", "content": question})
        answer = retrieve_answer(question, response_language)
        st.session_state.chat.append({"role": "assistant", "content": answer})
        st.rerun()
    with st.expander("What the assistant can reference"):
        for item in KNOWLEDGE:
            st.markdown(f"- {item['en']}")

with tab_about:
    st.markdown("### Project scope")
    st.write("NeuroVia Core is a front-end demonstration for a healthcare-AI project concept. The map and scenario controls are illustrative and do not process biomedical measurements.")
    st.markdown("### Safety and privacy")
    st.markdown(
        "- No clinical data, patient identifiers, sensors, Bluetooth, or live telemetry are used.\n"
        "- No diagnosis, prediction, treatment recommendation, stimulation, or emergency message is produced.\n"
        "- Log entries and chat messages are held in Streamlit session state and may disappear when the session resets.\n"
        "- Do not enter personal or health information. For urgent concerns, contact local emergency services or a qualified clinician."
    )
    st.markdown("### Retrieval assistant")
    st.write("The assistant compares question terms with a small bilingual, in-app reference set and returns the closest matching note. It is not a general-purpose medical chatbot or a clinical RAG system.")
