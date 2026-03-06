# 🤱 Matru-Shishu Suraksha

> **Empowering Every Mother · Protecting Every Child · Accessible Healthcare for All**

Matru-Shishu Suraksha is an AI-powered maternal and child healthcare web application built to reduce maternal and infant mortality in India by making trusted health information accessible to every mother — regardless of location or literacy level.

---

## 💡 About the Project

Millions of mothers in India — especially in rural and semi-urban areas — lack access to timely, reliable healthcare guidance during pregnancy, childbirth, and early childcare. **Matru-Shishu Suraksha** bridges this gap through two core features:

- 🤖 **MamaBot** — a conversational health assistant that answers questions about pregnancy nutrition, warning signs, labour, vaccines, breastfeeding, newborn care, and postpartum health in plain, friendly language.
- 🗺️ **Facility Finder** — a location-based tool that helps users discover nearby hospitals, maternity homes, and children's clinics within a customisable search radius, displayed on an interactive map.

The application is designed to be simple enough for first-time users, yet comprehensive enough to serve as a daily health companion throughout the pregnancy journey.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 MamaBot Chatbot | Answers maternal & child health queries using a trained Q&A dataset backed by MongoDB Atlas |
| 🗺️ Nearby Facility Finder | Locates hospitals and clinics by coordinates using free OpenStreetMap — no API key needed |
| 🎤 Voice Input | Browser-native speech-to-text so users can speak their questions (Chrome & Edge) |
| 🔐 User Authentication | Session-based login to personalise the experience |
| 📊 Smart Data Fallback | Loads from MongoDB Atlas → local JSON → built-in knowledge base, in order of availability |
| 📱 Responsive Design | Works on mobile, tablet, and desktop |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend & App | [Streamlit](https://streamlit.io) (Python) |
| Chatbot Dataset | MongoDB Atlas + local JSON (Q&A pairs) |
| Fuzzy Matching | Python `difflib` |
| Maps | [Folium](https://python-visualization.github.io/folium/) + OpenStreetMap |
| Voice Input | Web Speech API (browser-native) |
| Hosting | Streamlit Community Cloud (free tier) |
| Backend (original) | Flask + Jinja2 |

---

## 🚀 Live Demo

> 🔗 **[Launch App →](https://your-app-link.streamlit.app)**
> *(Replace this link with your Streamlit Cloud URL after deployment)*

---

## 📂 Project Structure

```
matru-shishu-suraksha/
├── streamlit_app.py              # Main Streamlit application
├── app.py                        # Original Flask backend
├── requirements.txt              # Python dependencies
├── chatbot_qa_dataset.json       # MamaBot Q&A training data
├── chatbot_dialogue_dataset.json # Dialogue-style training data
├── combined_conversations.json   # Combined dataset
├── templates/                    # Flask HTML templates
├── static/                       # CSS, JS, images
└── .streamlit/
    └── secrets.toml              # 🔒 Local secrets (not committed)
```

---

## ⚙️ Setup & Run Locally

**1. Clone the repository**
```bash
git clone https://github.com/paradise-007/matru-shishu-suraksha.git
cd matru-shishu-suraksha
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Add your MongoDB URI** *(optional — app works without it)*

Create `.streamlit/secrets.toml`:
```toml
MONGO_URI       = "mongodb+srv://<user>:<pass>@<cluster>.mongodb.net/"
MONGO_DB        = "matru_shishu"
MONGO_COLLECTION = "chatbot_data"
```

**4. Run the app**
```bash
streamlit run streamlit_app.py
```
Open `http://localhost:8501` in your browser.

---

## 🩺 Health Topics Covered by MamaBot

- Trimester-wise pregnancy nutrition
- Foods to avoid during pregnancy
- Warning signs and emergency guidance
- Signs of labour (true vs. false)
- Fetal kick counting
- Vaccination schedules (mother & baby)
- Breastfeeding and milk supply
- Newborn care and jaundice
- Gestational diabetes, anaemia, preeclampsia
- C-section recovery
- Postpartum depression support

---

## 🆘 Emergency Contacts (India)

| Service | Number |
|---|---|
| 🚑 Ambulance | 108 |
| 👩 Women Helpline | 181 |
| 🧒 Child Helpline | 1098 |
| 💙 Mental Health (iCall) | 9152987821 |

---

## 🤝 Contributing

Contributions are welcome! If you'd like to improve MamaBot's knowledge base, add regional language support, or expand the facility database:

1. Fork the repository
2. Create a new branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -m "Add: your description"`
4. Push and open a Pull Request

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).

---

## 👤 Author

**Vishv** — [@paradise-007](https://github.com/paradise-007)

> *"Every mother deserves access to safe, informed healthcare. This project is a small step toward that future."*

---

<div align="center">
Made with ❤️ for Maternal & Child Healthcare in India
</div>
