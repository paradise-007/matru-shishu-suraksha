import streamlit as st
import streamlit.components.v1 as components
import json
import os
import math
import re
from difflib import get_close_matches

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Matru-Shishu Suraksha",
    page_icon="🤱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
    .stApp { background: linear-gradient(135deg, #fff0f6 0%, #fce4ec 50%, #f3e5f5 100%); }

    .header-card {
        background: linear-gradient(135deg, #e91e8c, #9c27b0);
        color: white; padding: 2rem 2.5rem; border-radius: 20px;
        text-align: center; margin-bottom: 1.8rem;
        box-shadow: 0 8px 32px rgba(233,30,140,0.30);
    }
    .header-card h1 { margin:0; font-size:2.1rem; font-weight:700; }
    .header-card p  { margin:0.5rem 0 0; opacity:0.88; font-size:0.95rem; }

    .chat-user {
        background: linear-gradient(135deg,#e91e8c,#9c27b0); color:white;
        padding:0.75rem 1.1rem; border-radius:18px 18px 4px 18px;
        margin:0.5rem 0 0.5rem auto; max-width:78%; text-align:right;
        box-shadow:0 2px 10px rgba(233,30,140,0.25); line-height:1.5;
    }
    .chat-bot {
        background:white; color:#333; padding:0.75rem 1.1rem;
        border-radius:18px 18px 18px 4px; margin:0.5rem auto 0.5rem 0;
        max-width:78%; border-left:4px solid #e91e8c;
        box-shadow:0 2px 12px rgba(0,0,0,0.07); line-height:1.6;
    }
    .chat-label-bot  { font-size:0.72rem; color:#e91e8c; font-weight:700; margin-bottom:0.25rem; }
    .chat-label-user { font-size:0.72rem; color:rgba(255,255,255,0.75); margin-bottom:0.25rem; }

    .info-card {
        background:white; border-radius:14px; padding:1.2rem 1.3rem;
        margin:0.6rem 0; box-shadow:0 2px 14px rgba(0,0,0,0.07);
        border-left:4px solid #e91e8c;
    }
    .info-card h4 { margin:0 0 0.4rem; color:#e91e8c; font-size:1rem; }
    .info-card p  { margin:0; color:#555; font-size:0.88rem; line-height:1.6; }

    .stat-card {
        background:linear-gradient(135deg,#fff0f6,#fce4ec); border-radius:14px;
        padding:1rem; text-align:center; border:1px solid rgba(233,30,140,0.15);
    }
    .stat-card .num { font-size:2rem; font-weight:700; color:#e91e8c; }
    .stat-card .lbl { font-size:0.8rem; color:#9c27b0; font-weight:600; }

    .emer-box {
        background:linear-gradient(135deg,#ff1744,#d50000); color:white;
        border-radius:12px; padding:0.85rem 1.2rem;
        font-size:0.88rem; font-weight:600; letter-spacing:0.02em;
    }
    .tip-box {
        background:#fff8e1; border:1px solid #ffe082; border-radius:12px;
        padding:0.85rem 1.1rem; font-size:0.87rem; color:#5d4037; line-height:1.7;
    }

    div[data-testid="stTextInput"] > div > div > input {
        border-radius:25px !important; border:2px solid #e91e8c !important;
        padding:0.55rem 1.2rem !important;
    }
    .stButton > button {
        background:linear-gradient(135deg,#e91e8c,#9c27b0) !important;
        color:white !important; border:none !important; border-radius:25px !important;
        padding:0.5rem 1.4rem !important; font-weight:600 !important;
    }
    .stButton > button:hover { opacity:0.88 !important; transform:translateY(-1px) !important; }
    section[data-testid="stSidebar"] { background:white !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
for k, v in {"chat_history": [], "logged_in": False, "user_email": "",
              "user_location": None}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────
# LOAD CHATBOT JSON FILES
# ─────────────────────────────────────────────
@st.cache_data
def load_chatbot_data():
    combined = {}
    for fname in ["chatbot_qa_dataset.json", "chatbot_dialogue_dataset.json", "combined_conversations.json"]:
        if os.path.exists(fname):
            try:
                with open(fname, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        q = (item.get("question") or item.get("input") or item.get("prompt") or "").strip()
                        a = (item.get("answer")   or item.get("output") or item.get("response") or "").strip()
                        if q and a:
                            combined[q.lower()] = a
                elif isinstance(data, dict):
                    for k2, v2 in data.items():
                        combined[k2.lower().strip()] = v2 if isinstance(v2, str) else str(v2)
            except Exception:
                pass
    return combined

chatbot_db = load_chatbot_data()

# ─────────────────────────────────────────────
# BUILT-IN FALLBACK KNOWLEDGE BASE
# ─────────────────────────────────────────────
FALLBACK_KB = {
    "hello": "👋 Hello! I'm **MamaBot** 🤱 — your maternal & child health assistant. Ask me anything about pregnancy, nutrition, baby care, or health facilities!",
    "hi": "👋 Hi there! I'm MamaBot. How can I support you today?",
    "thank you": "😊 You're very welcome! Take good care of yourself and your little one. 💕",
    "thanks": "😊 Happy to help! Stay strong and healthy. 💪",

    "what should i eat in first trimester": "🥗 **First Trimester Nutrition:**\n\n• **Folic acid** (400–800 mcg/day) — spinach, lentils, fortified cereals\n• **Protein** — eggs, chicken, legumes\n• **Calcium** — milk, yogurt, cheese\n• **Iron** — red meat, beans, tofu\n• At least **8–10 glasses of water** per day\n\nTake prenatal vitamins daily. Avoid raw fish, unpasteurized dairy, and alcohol.",
    "what should i eat in second trimester": "🍎 **Second Trimester Nutrition:**\n\n• Increase **iron** (spinach, red meat, beans)\n• More **calcium** (3 servings dairy/day)\n• **Omega-3s** — salmon, walnuts, flaxseed\n• Eat small, frequent meals for heartburn\n• **Vitamin D** — sunlight + fortified milk",
    "what should i eat in third trimester": "🌾 **Third Trimester Nutrition:**\n\n• **Fibre** — whole grains, fruits, vegetables\n• Continue **iron + calcium** supplements\n• **Vitamin C** boosts iron absorption\n• Eat 5–6 small meals instead of 3 large ones\n• Stay well-hydrated; reduce salt to manage swelling",
    "foods to avoid during pregnancy": "⚠️ **Foods to Avoid:**\n\n• Raw or undercooked meat, fish, eggs\n• Unpasteurized dairy products\n• High-mercury fish (shark, swordfish)\n• **Alcohol** — none is safe at any stage\n• Excess caffeine (keep under 200 mg/day)\n• Unwashed raw fruits and vegetables\n• Highly processed, high-sodium foods",

    "when should i see a doctor": "🏥 **Antenatal Visit Schedule (India):**\n\n• **First visit** — as early as possible on confirmation\n• **Monthly** until 28 weeks\n• **Every 2 weeks** from 28–36 weeks\n• **Weekly** from 36 weeks to delivery\n\nDon't miss your anomaly scan at 18–20 weeks and glucose tolerance test at 24–28 weeks.",
    "warning signs during pregnancy": "🚨 **Go to hospital IMMEDIATELY for:**\n\n• Heavy vaginal bleeding\n• Severe headache + blurred vision\n• Sudden swelling of face, hands, feet\n• Reduced or no fetal movement\n• High fever (>38°C)\n• Difficulty breathing\n• Severe abdominal or chest pain\n\nThese may indicate preeclampsia, placenta previa, or other serious emergencies.",

    "how to handle morning sickness": "🌿 **Managing Morning Sickness:**\n\n• Eat small meals every 2 hours\n• Try ginger tea, ginger biscuits, or dry crackers before getting up\n• Avoid spicy, fatty, or strong-smelling foods\n• Sip cold water or lemon water throughout the day\n• Rest and change positions slowly\n• If vomiting is severe, see your doctor (may need IV fluids)",

    "signs of labour": "⚠️ **Signs of Labour:**\n\n• Regular contractions every 5 minutes, lasting ~60 seconds\n• Water breaking (clear/pink fluid)\n• Bloody mucus 'show' (pink/brown discharge)\n• Lower back pain radiating to the abdomen\n• Feeling of pelvic pressure\n\n🏥 Go to hospital when contractions are **5 min apart for 1 hour** (first baby).",

    "what vaccines are needed during pregnancy": "💉 **Vaccines During Pregnancy:**\n\n✅ **Recommended:**\n• **Tdap** (whooping cough protection for baby) — 27–36 weeks\n• **Flu vaccine** — any trimester\n\n❌ **Avoid (live vaccines):**\n• MMR, Chickenpox, Yellow Fever\n\nAlways consult your OB-GYN before any vaccine.",

    "baby kick count": "👶 **Fetal Kick Count:**\n\n• Start daily counting from **28 weeks**\n• Baby should kick **10 times in 2 hours**\n• Count after meals or in the evening (most active)\n• Lie on your left side for best results\n\n⚠️ Fewer than 10 kicks in 2 hours? Drink juice/cold water, count again. Still low? Call your doctor immediately.",

    "breastfeeding tips": "🤱 **Breastfeeding Tips:**\n\n• Feed every **2–3 hours** (8–12 times/day for newborns)\n• Ensure baby has a **deep latch** (covers areola)\n• First milk (colostrum) is golden — packed with immunity\n• Drink extra fluids + eat 500 more calories/day\n• Avoid alcohol and smoking\n• Skin-to-skin contact helps establish milk supply\n• Seek a lactation consultant if feeding is painful",
    "low breast milk supply": "🍼 **Boosting Milk Supply:**\n\n• Feed or pump **more frequently** — supply follows demand\n• Ensure a deep, correct latch\n• Stay well-hydrated (3+ litres/day)\n• Eat lactogenic foods: oats, fenugreek, garlic, nuts\n• Get enough rest and reduce stress\n• Consult a lactation consultant",

    "newborn care": "🍼 **Newborn Care Essentials:**\n\n• **Feeding:** Breastfeed on demand or formula if needed\n• **Cord:** Keep dry and clean; falls off in 1–3 weeks\n• **Bathing:** Sponge bath 2–3x/week until cord falls\n• **Sleeping:** Back sleeping ONLY — reduces SIDS risk\n• **First visit:** See pediatrician within 3–5 days of birth",
    "jaundice in newborn": "🟡 **Newborn Jaundice:**\n\nVery common (60% of babies). Appears day 2–3, clears in 1–2 weeks.\n\n**Help it resolve:**\n• Breastfeed 8–12 times/day\n• Brief morning indirect sunlight exposure\n\n⚠️ **See doctor immediately if:**\n• Appears in first 24 hours\n• Baby is lethargic or not feeding\n• Spreads to belly, arms, legs",

    "postpartum depression": "💙 **Postpartum Depression:**\n\nAffects 1 in 7 mothers — you are NOT alone and it IS treatable.\n\n**Symptoms:** Persistent sadness, difficulty bonding, extreme fatigue, feeling hopeless or overwhelmed.\n\n**Help:** Talk to your doctor. Treatment includes therapy, medication, and peer support.\n📞 iCall (India): **9152987821**",
    "c section recovery": "🏥 **C-Section Recovery:**\n\n• Avoid heavy lifting for **6–8 weeks**\n• Take prescribed pain relief — don't suffer needlessly\n• Keep incision clean and dry\n• Start gentle walking on day 1 (promotes healing)\n• Watch for: fever, redness, discharge, pain worsening\n• Driving: wait 4–6 weeks\n• Full recovery: 6–8 weeks",

    "high blood pressure pregnancy": "🩺 **Preeclampsia (High BP in Pregnancy):**\n\n🚨 **ER immediately if you have:**\n• Severe headache that won't go away\n• Blurred vision or seeing spots\n• Sudden severe face/hand/foot swelling\n• Upper right abdominal pain\n\n**Management:** Regular BP checks, low-salt diet, prescribed medication, frequent OB visits.",
    "gestational diabetes": "🍬 **Gestational Diabetes:**\n\n• Monitor blood sugar as prescribed\n• Low-sugar, high-fibre diet with frequent small meals\n• 30-min walks after meals lower blood sugar\n• Take insulin/medication if prescribed\n• Usually resolves after delivery\n\n⚠️ Untreated GDM risks: large baby, difficult delivery, increased future diabetes risk.",
    "anaemia in pregnancy": "🩸 **Anaemia in Pregnancy:**\n\n**Iron-rich foods:** Spinach, red meat, lentils, dates, fortified cereals\n\n**Boost absorption:**\n• Pair iron foods with **Vitamin C** (orange juice, tomatoes)\n• Avoid tea/coffee with iron-rich meals\n• Take iron supplements as prescribed\n\n**Severe symptoms:** Extreme fatigue, pale skin, dizziness, rapid heartbeat — see doctor.",

    "immunization schedule baby": "💉 **India National Immunization Schedule:**\n\n🔴 **Birth:** BCG, OPV-0, Hepatitis B\n🟠 **6 weeks:** OPV-1, DPT-1, Hib-1, Hep B-2, PCV-1, Rota-1\n🟡 **10 weeks:** OPV-2, DPT-2, Hib-2, PCV-2, Rota-2\n🟢 **14 weeks:** OPV-3, DPT-3, Hib-3, PCV-3, Rota-3\n🔵 **9 months:** Measles-1, OPV Booster\n🟣 **16–24 months:** DPT Booster, MMR, Typhoid\n\nAlways follow your pediatrician's schedule!",
}


def get_bot_response(user_msg: str) -> str:
    query = re.sub(r'[?!.,]', '', user_msg.lower().strip()).strip()

    if query in chatbot_db:
        return chatbot_db[query]
    if chatbot_db:
        close = get_close_matches(query, list(chatbot_db.keys()), n=1, cutoff=0.55)
        if close:
            return chatbot_db[close[0]]
    if query in FALLBACK_KB:
        return FALLBACK_KB[query]
    close_fb = get_close_matches(query, list(FALLBACK_KB.keys()), n=1, cutoff=0.42)
    if close_fb:
        return FALLBACK_KB[close_fb[0]]
    words = [w for w in re.split(r'\W+', query) if len(w) > 3]
    for key, val in {**chatbot_db, **FALLBACK_KB}.items():
        if any(w in key for w in words):
            return val

    return ("🤔 I'm not sure about that specific question. Please consult your doctor "
            "for personalised advice.\n\n💡 **I can help with:** Pregnancy nutrition, "
            "warning signs, labour, baby care, vaccines, breastfeeding, and postpartum health.")


# ─────────────────────────────────────────────
# FACILITIES DATA
# ─────────────────────────────────────────────
@st.cache_data
def load_facilities():
    for fname in ["data/facilities.json", "facilities.json"]:
        if os.path.exists(fname):
            try:
                with open(fname) as f:
                    return json.load(f)
            except Exception:
                pass
    return [
        {"name": "AIIMS New Delhi",                "lat": 28.5672, "lon": 77.2100, "type": "Government Hospital", "phone": "011-26588500"},
        {"name": "Safdarjung Hospital Delhi",       "lat": 28.5683, "lon": 77.2063, "type": "Government Hospital", "phone": "011-26165060"},
        {"name": "Lady Hardinge Medical College",   "lat": 28.6390, "lon": 77.2118, "type": "Maternity Hospital",  "phone": "011-23408390"},
        {"name": "Fortis La Femme Delhi",           "lat": 28.5638, "lon": 77.2090, "type": "Maternity Hospital",  "phone": "011-42005678"},
        {"name": "KEM Hospital Mumbai",             "lat": 19.0031, "lon": 72.8419, "type": "Government Hospital", "phone": "022-24136051"},
        {"name": "Wadia Maternity Hospital Mumbai", "lat": 18.9918, "lon": 72.8327, "type": "Maternity Hospital",  "phone": "022-23081900"},
        {"name": "Jehangir Hospital Pune",          "lat": 18.5204, "lon": 73.8567, "type": "Private Hospital",    "phone": "020-66810000"},
        {"name": "Narayana Health Bangalore",       "lat": 12.9716, "lon": 77.5946, "type": "Private Hospital",    "phone": "080-71222222"},
        {"name": "Apollo Childrens Chennai",        "lat": 13.0827, "lon": 80.2707, "type": "Children Hospital",   "phone": "044-44800800"},
        {"name": "Civil Hospital Gandhinagar",      "lat": 23.2156, "lon": 72.6369, "type": "Government Hospital", "phone": "079-23222100"},
        {"name": "Sterling Hospital Ahmedabad",     "lat": 23.0225, "lon": 72.5714, "type": "Private Hospital",    "phone": "079-40011000"},
        {"name": "IKDRC Ahmedabad",                 "lat": 23.0393, "lon": 72.5511, "type": "Government Hospital", "phone": "079-27490000"},
        {"name": "SMS Hospital Jaipur",             "lat": 26.9124, "lon": 75.7873, "type": "Government Hospital", "phone": "0141-2518501"},
        {"name": "PGI Chandigarh",                  "lat": 30.7650, "lon": 76.7769, "type": "Government Hospital", "phone": "0172-2755555"},
        {"name": "Fernandez Hospital Hyderabad",    "lat": 17.3850, "lon": 78.4867, "type": "Maternity Hospital",  "phone": "040-40271000"},
        {"name": "AIIMS Bhopal",                    "lat": 23.1765, "lon": 77.3219, "type": "Government Hospital", "phone": "0755-2672355"},
    ]

facilities_data = load_facilities()

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return round(R * 2 * math.asin(math.sqrt(a)), 1)


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding:1.2rem 0 0.5rem;'>
        <div style='font-size:3.2rem;'>🤱</div>
        <h2 style='color:#e91e8c; margin:0.2rem 0 0; font-size:1.3rem;'>Matru-Shishu</h2>
        <p style='color:#9c27b0; margin:0; font-size:0.82rem; font-weight:500;'>Suraksha Dashboard</p>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    # ── Login ─────────────────────────────────
    if not st.session_state.logged_in:
        st.subheader("🔐 Login")
        email    = st.text_input("Email",    placeholder="your@email.com", key="sb_email")
        password = st.text_input("Password", type="password", placeholder="••••••••", key="sb_pass")
        if st.button("Login →", key="btn_login"):
            if email.strip() and password.strip():
                st.session_state.logged_in  = True
                st.session_state.user_email = email.strip()
                st.rerun()
            else:
                st.error("Please fill in both fields.")
        st.caption("💡 Demo: any email & password")
    else:
        st.markdown(f"""
        <div class='info-card' style='padding:0.8rem;'>
            <div class='chat-label-bot'>Logged in as</div>
            <b>{st.session_state.user_email}</b>
        </div>""", unsafe_allow_html=True)
        if st.button("🚪 Logout", key="btn_logout"):
            st.session_state.logged_in  = False
            st.session_state.user_email = ""
            st.rerun()

    st.divider()

    # ── Navigation ─────────────────────────────
    st.subheader("📌 Navigation")
    nav = st.radio("", [
        "🤖  MamaBot Chatbot",
        "🗺️  Nearby Facilities",
        "ℹ️  About",
    ], label_visibility="collapsed", key="nav_radio")

    st.divider()

    st.markdown("""
    <div class='emer-box'>
        🆘 <b>Emergency Numbers</b><br>
        🚑 Ambulance: <b>108</b><br>
        👩 Women Helpline: <b>181</b><br>
        🧒 Child Helpline: <b>1098</b><br>
        💙 iCall (Mental Health): <b>9152987821</b>
    </div><br>
    <div class='tip-box'>
    💡 <b>Tip:</b> Drink 8–10 glasses of water daily during pregnancy — it helps reduce swelling, headaches, and preterm labour risk.
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class='header-card'>
    <h1>🤱 Matru-Shishu Suraksha</h1>
    <p>Empowering Every Mother · Protecting Every Child · Accessible Healthcare for All</p>
</div>
""", unsafe_allow_html=True)

# ═════════════════════════════════════════════
# PAGE: MAMABOT
# ═════════════════════════════════════════════
if "MamaBot" in nav:
    st.subheader("💬 MamaBot — Your Health Assistant")

    col_chat, col_info = st.columns([3, 1.1])

    with col_info:
        st.markdown("""
        <div class='info-card'>
            <h4>💡 Ask MamaBot</h4>
            <p>
            🥗 Pregnancy diet<br>
            ⚠️ Warning signs<br>
            🤰 Labour signs<br>
            💉 Vaccines<br>
            🤱 Breastfeeding<br>
            🍼 Newborn care<br>
            💙 Postpartum health<br>
            🩺 Conditions (GDM, BP, Anaemia)
            </p>
        </div>
        <div class='tip-box' style='margin-top:0.6rem;'>
        ⚠️ MamaBot provides general health information — always consult a qualified doctor for medical advice.
        </div>
        """, unsafe_allow_html=True)

    with col_chat:
        # ── Quick suggestion chips ──────────────
        suggestions = [
            "What to eat in 1st trimester?",
            "Signs of labour",
            "Breastfeeding tips",
            "Baby vaccine schedule",
            "Morning sickness",
            "Warning signs in pregnancy",
            "C-section recovery",
            "Postpartum depression",
        ]
        chip_cols = st.columns(4)
        for i, s in enumerate(suggestions):
            if chip_cols[i % 4].button(s, key=f"chip_{i}", use_container_width=True):
                resp = get_bot_response(s)
                st.session_state.chat_history.append({"role": "user", "msg": s})
                st.session_state.chat_history.append({"role": "bot",  "msg": resp})
                st.rerun()

        _, c2 = st.columns([6, 1])
        if c2.button("🗑️ Clear"):
            st.session_state.chat_history = []
            st.rerun()

        # ── Chat window ─────────────────────────
        chat_html = "<div style='max-height:400px; overflow-y:auto; padding:0.5rem 0.2rem;'>"
        if not st.session_state.chat_history:
            chat_html += """<div class='chat-bot'>
                <div class='chat-label-bot'>🤱 MamaBot</div>
                Hello! I'm <b>MamaBot</b>, your maternal &amp; child health assistant.<br>
                Type a question, click a chip above, or use 🎤 <b>Voice Input</b> below!
            </div>"""
        for msg in st.session_state.chat_history:
            content = (msg['msg']
                       .replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                       .replace('\n', '<br>'))
            if msg["role"] == "user":
                chat_html += f"<div class='chat-user'><div class='chat-label-user'>You</div>{content}</div>"
            else:
                chat_html += f"<div class='chat-bot'><div class='chat-label-bot'>🤱 MamaBot</div>{content}</div>"
        chat_html += "</div>"
        st.markdown(chat_html, unsafe_allow_html=True)

        # ── Text input ──────────────────────────
        with st.form("chat_form", clear_on_submit=True):
            ic, bc = st.columns([5, 1])
            user_input = ic.text_input("", placeholder="Type your question here…", label_visibility="collapsed")
            submitted  = bc.form_submit_button("Send ➤")

        if submitted and user_input.strip():
            resp = get_bot_response(user_input.strip())
            st.session_state.chat_history.append({"role": "user", "msg": user_input.strip()})
            st.session_state.chat_history.append({"role": "bot",  "msg": resp})
            st.rerun()

        # ── Voice Input ─────────────────────────
        st.markdown("---")
        st.markdown("**🎤 Voice Input** *(Works in Chrome & Edge)*")
        st.caption("Click the mic → speak → copy the result → paste it in the chat box above and hit Send.")

        components.html("""
        <div style="
            background:white; border-radius:16px; padding:1.3rem 1.5rem;
            border:2px dashed #e91e8c; text-align:center;
            font-family:'Segoe UI',sans-serif;
        ">
            <div id="status" style="
                font-size:0.85rem; color:#9c27b0; font-weight:600;
                margin-bottom:0.9rem; min-height:1.3rem;
            ">Click the microphone to start speaking</div>

            <button id="micBtn" onclick="toggleMic()" style="
                background:linear-gradient(135deg,#e91e8c,#9c27b0); color:white;
                border:none; border-radius:50%; width:68px; height:68px;
                font-size:1.9rem; cursor:pointer;
                box-shadow:0 4px 18px rgba(233,30,140,0.35);
                display:inline-flex; align-items:center; justify-content:center;
                transition:0.2s;
            ">🎤</button>

            <div id="live-box" style="
                display:none; margin-top:0.9rem; padding:0.7rem 1rem;
                background:#fff0f6; border-radius:10px;
                font-size:0.9rem; color:#555; text-align:left;
                border:1px solid rgba(233,30,140,0.2); min-height:2.5rem;
            "></div>

            <div id="result-area" style="display:none; margin-top:0.9rem;">
                <p style="font-size:0.82rem; color:#777; margin:0 0 0.4rem;">
                    👇 Copy this and paste it into the chat box:
                </p>
                <input id="voiceOut" type="text" readonly style="
                    width:100%; padding:0.55rem 0.9rem; border-radius:10px;
                    border:1.5px solid #e91e8c; font-size:0.9rem;
                    color:#333; background:white; box-sizing:border-box;
                ">
                <div style="display:flex; gap:0.5rem; margin-top:0.5rem; justify-content:center;">
                    <button onclick="copyText()" style="
                        background:linear-gradient(135deg,#e91e8c,#9c27b0); color:white;
                        border:none; border-radius:20px; padding:0.4rem 1.4rem;
                        cursor:pointer; font-weight:600; font-size:0.85rem;
                    ">📋 Copy Text</button>
                    <button onclick="clearResult()" style="
                        background:#f5f5f5; color:#555;
                        border:none; border-radius:20px; padding:0.4rem 1.2rem;
                        cursor:pointer; font-weight:600; font-size:0.85rem;
                    ">🔄 Try Again</button>
                </div>
                <div id="copied-msg" style="
                    font-size:0.8rem; color:#4caf50; font-weight:700;
                    margin-top:0.4rem; display:none;
                ">✅ Copied! Now paste it into the chat box above.</div>
            </div>

            <p style="font-size:0.75rem; color:#aaa; margin:0.8rem 0 0;">
                🌐 Works in Chrome &amp; Edge · Supports Hindi + English
            </p>
        </div>

        <style>
        @keyframes pulse {
            0%,100% { box-shadow: 0 4px 18px rgba(233,30,140,0.35); }
            50%      { box-shadow: 0 0 0 14px rgba(233,30,140,0.0); }
        }
        </style>

        <script>
        let recog = null, isListening = false;
        const btn      = document.getElementById('micBtn');
        const status   = document.getElementById('status');
        const liveBox  = document.getElementById('live-box');
        const resArea  = document.getElementById('result-area');
        const voiceOut = document.getElementById('voiceOut');
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;

        function toggleMic() {
            if (!SpeechRec) {
                status.textContent = '❌ Voice not supported. Please use Google Chrome or Microsoft Edge.';
                status.style.color = '#f44336';
                return;
            }
            if (isListening) { recog.stop(); return; }

            recog = new SpeechRec();
            recog.lang = 'en-IN';
            recog.interimResults = true;
            recog.maxAlternatives = 1;

            recog.onstart = () => {
                isListening = true;
                btn.textContent = '⏹️';
                btn.style.background = 'linear-gradient(135deg,#ff1744,#d50000)';
                btn.style.animation = 'pulse 1s infinite';
                status.textContent = '🔴 Listening… speak your question now';
                status.style.color = '#f44336';
                liveBox.style.display = 'block';
                liveBox.textContent = '';
                resArea.style.display = 'none';
            };
            recog.onresult = (e) => {
                const t = Array.from(e.results).map(r => r[0].transcript).join('');
                liveBox.textContent = t;
                if (e.results[e.results.length - 1].isFinal) {
                    voiceOut.value = t;
                    resArea.style.display = 'block';
                }
            };
            recog.onerror = (e) => {
                status.textContent = '⚠️ Error: ' + e.error + ' — please try again';
                status.style.color = '#f44336';
                resetBtn();
            };
            recog.onend = () => {
                status.textContent = isListening
                    ? '✅ Done! Copy the text and paste into the chat box.'
                    : 'Click mic to try again.';
                status.style.color = '#4caf50';
                resetBtn();
            };
            recog.start();
        }

        function resetBtn() {
            isListening = false;
            btn.textContent = '🎤';
            btn.style.background = 'linear-gradient(135deg,#e91e8c,#9c27b0)';
            btn.style.animation = '';
        }

        function copyText() {
            voiceOut.select();
            voiceOut.setSelectionRange(0, 99999);
            try {
                document.execCommand('copy');
                document.getElementById('copied-msg').style.display = 'block';
                setTimeout(() => { document.getElementById('copied-msg').style.display = 'none'; }, 3500);
            } catch(e) {
                navigator.clipboard.writeText(voiceOut.value).catch(() => {});
            }
        }

        function clearResult() {
            resArea.style.display = 'none';
            liveBox.style.display = 'none';
            status.textContent = 'Click the microphone to start speaking';
            status.style.color = '#9c27b0';
            voiceOut.value = '';
        }
        </script>
        """, height=370)

# ═════════════════════════════════════════════
# PAGE: FACILITIES MAP
# ═════════════════════════════════════════════
elif "Facilities" in nav:
    st.subheader("🗺️ Find Nearby Medical Facilities")
    st.caption("Powered by OpenStreetMap via Folium — 100% free, no API key needed!")

    left, right = st.columns([2.2, 1])

    with right:
        st.markdown("""
        <div class='info-card'>
            <h4>📌 Find Your Coordinates</h4>
            <p>1. Open <a href='https://maps.google.com' target='_blank'>Google Maps</a><br>
            2. Long-press your location<br>
            3. Copy the lat/lon shown</p>
        </div>
        <div class='info-card' style='margin-top:0.6rem;'>
            <h4>🔴 Map Marker Colors</h4>
            <p>🔴 Government Hospital<br>
            🟣 Private Hospital<br>
            🩷 Maternity Hospital<br>
            🔵 Children's Hospital<br>
            🟠 Medical College</p>
        </div>
        """, unsafe_allow_html=True)

    with left:
        lc1, lc2 = st.columns(2)
        lat_in  = lc1.number_input("📍 Your Latitude",  value=23.2156, format="%.4f")
        lon_in  = lc2.number_input("📍 Your Longitude", value=72.6369, format="%.4f")
        radius  = st.slider("🔍 Search Radius (km)", 10, 1000, 200, 10)
        all_types   = sorted(set(f.get("type", "Other") for f in facilities_data))
        filter_type = st.multiselect("🏷️ Filter by Type (blank = show all)", all_types)
        search_btn  = st.button("🔍 Find Facilities", use_container_width=True)

    if search_btn:
        st.session_state.user_location = (lat_in, lon_in)

    if st.session_state.user_location:
        ulat, ulon = st.session_state.user_location
        nearby = []
        for f in facilities_data:
            d = haversine(ulat, ulon, f["lat"], f["lon"])
            if d <= radius and (not filter_type or f.get("type","") in filter_type):
                nearby.append({**f, "distance_km": d})
        nearby.sort(key=lambda x: x["distance_km"])

        # Stats
        s1, s2, s3 = st.columns(3)
        s1.markdown(f"<div class='stat-card'><div class='num'>{len(nearby)}</div><div class='lbl'>Facilities Found</div></div>", unsafe_allow_html=True)
        s2.markdown(f"<div class='stat-card'><div class='num'>{nearby[0]['distance_km'] if nearby else '—'} km</div><div class='lbl'>Nearest Facility</div></div>", unsafe_allow_html=True)
        s3.markdown(f"<div class='stat-card'><div class='num'>{radius} km</div><div class='lbl'>Search Radius</div></div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # Map
        try:
            import folium
            from streamlit_folium import st_folium

            COLOR_MAP = {
                "Government Hospital": "red",
                "Private Hospital":    "purple",
                "Maternity Hospital":  "pink",
                "Children Hospital":   "blue",
                "Medical College":     "orange",
            }

            m = folium.Map(location=[ulat, ulon], zoom_start=7, tiles="OpenStreetMap")
            folium.Marker([ulat, ulon],
                          popup="📍 <b>Your Location</b>",
                          tooltip="You are here",
                          icon=folium.Icon(color="red", icon="home", prefix="fa")).add_to(m)
            folium.Circle([ulat, ulon], radius=radius * 1000,
                          color="#e91e8c", fill=True, fill_opacity=0.06, weight=2).add_to(m)
            for f in nearby:
                color = COLOR_MAP.get(f.get("type", ""), "gray")
                popup_html = (f"<b>🏥 {f['name']}</b><br>📋 {f.get('type','N/A')}<br>"
                              f"📏 {f['distance_km']} km<br>📞 {f.get('phone','N/A')}<br>"
                              f"<a href='https://www.google.com/maps?q={f['lat']},{f['lon']}' "
                              f"target='_blank'>🗺️ Google Maps</a>")
                folium.Marker([f["lat"], f["lon"]],
                              popup=folium.Popup(popup_html, max_width=250),
                              tooltip=f"{f['name']} ({f['distance_km']} km)",
                              icon=folium.Icon(color=color, icon="plus-sign")).add_to(m)

            st_folium(m, use_container_width=True, height=480)

        except ImportError:
            st.warning("📦 `folium` and `streamlit-folium` are required for the map. They are already in your requirements.txt — just redeploy!")

        # List
        if nearby:
            st.subheader(f"📋 {len(nearby)} Facilities Found")
            for f in nearby:
                maps_url = f"https://www.google.com/maps?q={f['lat']},{f['lon']}"
                dirs_url = f"https://www.google.com/maps/dir/?api=1&destination={f['lat']},{f['lon']}"
                st.markdown(f"""
                <div class='info-card'>
                    <h4>🏥 {f['name']}
                        <span style='font-size:0.78rem; color:#aaa; font-weight:400;'> · {f.get('type','')}</span>
                    </h4>
                    <p>📏 <b>{f['distance_km']} km</b> away &nbsp;·&nbsp; 📞 {f.get('phone','N/A')}
                       &nbsp;·&nbsp; <a href='{maps_url}' target='_blank'>🗺️ View Map</a>
                       &nbsp;·&nbsp; <a href='{dirs_url}' target='_blank'>🧭 Directions</a></p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning(f"No facilities found within {radius} km. Try increasing the search radius.")
    else:
        st.info("👆 Enter your coordinates above and click **Find Facilities** to search.")

# ═════════════════════════════════════════════
# PAGE: ABOUT
# ═════════════════════════════════════════════
else:
    st.subheader("ℹ️ About Matru-Shishu Suraksha")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class='info-card'>
            <h4>🎯 Mission</h4>
            <p>Matru-Shishu Suraksha reduces maternal and infant mortality in India by making
            healthcare information accessible to every mother — especially in underserved areas —
            through an intelligent chatbot and facility-finder tool.</p>
        </div>
        <div class='info-card' style='margin-top:0.7rem;'>
            <h4>🤖 MamaBot Features</h4>
            <p>• Trimester-wise pregnancy nutrition<br>
            • Warning signs &amp; emergency guidance<br>
            • Labour and delivery information<br>
            • Newborn care &amp; immunization schedules<br>
            • Breastfeeding guidance<br>
            • Postpartum &amp; mental health support<br>
            • 🎤 Voice input (Chrome/Edge)</p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class='info-card'>
            <h4>🗺️ Facility Finder</h4>
            <p>Locate government hospitals, maternity homes, children's hospitals,
            and clinics near you — completely free using OpenStreetMap (no Google API key needed).</p>
        </div>
        <div class='info-card' style='margin-top:0.7rem;'>
            <h4>⚙️ Tech Stack</h4>
            <p>• <b>App:</b> Streamlit (Python)<br>
            • <b>Maps:</b> Folium + OpenStreetMap (free)<br>
            • <b>Chatbot:</b> Your JSON dataset + Fuzzy Match<br>
            • <b>Voice:</b> Web Speech API (browser-native)<br>
            • <b>Hosting:</b> Streamlit Community Cloud (free)</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style='text-align:center; color:#9c27b0; padding:0.8rem; font-size:0.88rem;'>
        🤱 <b>Matru-Shishu Suraksha</b> · Made with ❤️ for Maternal &amp; Child Healthcare in India<br>
        🚑 108 &nbsp;|&nbsp; 👩 Women: 181 &nbsp;|&nbsp; 🧒 Child: 1098 &nbsp;|&nbsp; 💙 iCall: 9152987821
    </div>
    """, unsafe_allow_html=True)