# AI Reel Intelligence Platform
## 🏆 College Hackathon — Competition-Ready Submission

> **"We don't build another algorithm that tells students what to watch. We build an AI agent that understands what their scrolling behavior *means*."**

---

## 🌟 What Makes This Different

Most recommendation systems ask: _"Is this related?"_

**This system asks: "Is this related AND actually useful AND not clickbait?"**

The full decision pipeline:

```
Student Watches Reel
        ↓
Behavior Analyzer (weights: watch%, likes, saves, rewatches)
        ↓
Gemini AI → Interest Inference (primary + secondary interests)
        ↓
Gemini Embeddings → Semantic Similarity (text-embedding-004)
        ↓
Candidate Generation (all available reels)
        ↓
Hype / Clickbait Detector (penalizes low-quality bait)
        ↓
Multi-Signal Scoring:
  ├─ Semantic Relevance  (Gemini Embeddings)
  ├─ Interest Match      (AI-inferred profile)
  ├─ Educational Value   (content quality score)
  ├─ Career Relevance    (long-term value)
  ├─ Difficulty Match    (student level)
  └─ Hype Penalty        (clickbait detection)
        ↓
Exploration vs Exploitation (70 / 20 / 10 split)
        ↓
Final Recommendation + AI Reasoning ("Why you see this")
        ↓
Feedback Loop (👍👎🔖🚫) → Updates Profile
        ↓
Interest Evolution Snapshot (daily timeline)
```

---

## 🚀 Features

| Feature | Status |
|---|---|
| 🧠 AI Interest Inference (Gemini 1.5 Flash) | ✅ |
| 🔍 "Why did I get this?" Explainability | ✅ |
| 🛡️ Hype & Clickbait Detector | ✅ |
| 🎯 Exploration vs Exploitation (70/20/10) | ✅ |
| 📊 AI Recommendation Score Breakdown | ✅ |
| 🧬 Technology DNA Page (Bubble Visualization) | ✅ |
| 📈 Personal Technology Roadmap | ✅ |
| 📉 Interest Evolution Timeline | ✅ |
| 🔄 Feedback Loop (updates profile) | ✅ |
| 💬 Gemini Embeddings Semantic Similarity | ✅ |
| 🗃️ MongoDB Atlas + SQLite fallback | ✅ |
| 🔒 API key in `.env` (never in HTML/JS) | ✅ |
| ☁️ Deployment-ready (Render / Railway) | ✅ |

---

## 🏗️ Project Structure

```
ai-reel-recommender/
│
├── app.py                    # Flask app factory
├── run.py                    # Entry point
├── config.py                 # Config from .env
├── db_service.py             # MongoDB + SQLite abstraction
├── requirements.txt
├── .env                      # ← Your API keys go here (never commit)
├── .gitignore
│
├── routes/
│   ├── auth.py               # Register, Login, Logout
│   ├── reels.py              # Reel feed + interaction logging
│   ├── recommendations.py    # Recommendation, Feedback, Roadmap, Evolution
│   ├── analytics.py          # Analytics + Interest Profile API
│   └── profile.py            # Profile, Persona import, API key config
│
├── services/
│   ├── ai_service.py         # Gemini 1.5 Flash (interest, reasoning, roadmap)
│   ├── embedding_service.py  # Gemini text-embedding-004 (semantic similarity)
│   ├── behavior_analyzer.py  # Weights watch%, likes, saves, rewatches
│   ├── hype_detector.py      # Detects clickbait from title + transcript
│   ├── interest_engine.py    # Orchestrates AI inference + evolution snapshots
│   └── recommendation_engine.py  # Multi-signal scoring + 70/20/10 exploration
│
├── utils/
│   └── scoring.py            # calculate_final_score(), difficulty_match()
│
├── templates/
│   ├── base.html             # Sidebar layout + nav
│   ├── login.html / register.html
│   ├── dashboard.html        # Overview cards + quick recommendation
│   ├── reels.html            # Simulated reel feed
│   ├── recommendations.html  # Recommendation + score breakdown
│   ├── analytics.html        # Charts (Chart.js)
│   ├── dna.html              # Technology DNA page ← NEW
│   └── profile.html          # Settings, personas, API key
│
└── static/
    ├── css/style.css          # Glassmorphism dark theme
    └── js/
        ├── main.js
        ├── dashboard.js
        ├── reels.js
        ├── recommendations.js
        ├── analytics.js
        ├── dna.js             # SVG bubbles, roadmap, evolution chart ← NEW
        └── profile.js
```

---

## ⚙️ Setup

### 1. Clone & create virtual environment

```bash
git clone <your-repo-url>
cd ai-reel-recommender
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

### 2. Configure `.env`

```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
MONGO_URI=YOUR_MONGODB_ATLAS_URI
SECRET_KEY=some-random-secret-string
FLASK_DEBUG=True
```

> Get your free Gemini API key at: https://aistudio.google.com/apikey
> The app runs perfectly **without** a Gemini key using the built-in mock AI engine.

### 3. Run

```bash
python run.py
```

Open: **http://127.0.0.1:5000**

---

## 🧪 Test Personas

On the **Profile** page, import a pre-built test persona to instantly populate your interaction history:

| Persona | Behavior | Expected AI Output |
|---|---|---|
| `software_engineer` | High Java + DSA watch%, saves | Primary: Software Engineering |
| `ai_hacker` | High AI reel completion, saved | Primary: Artificial Intelligence & ML |
| `cybersecurity` | 98% SQL injection reel + saves | Primary: Cybersecurity & Cryptography |
| `clickbait_victim` | 98% completion of hype reels | Low quality score, Hype Detector fires |

---

## 📡 Key API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/register` | Create account |
| `POST` | `/api/login` | Login |
| `GET` | `/api/reels` | Get reel feed |
| `POST` | `/api/interactions` | Log a reel interaction |
| `GET` | `/api/recommendations` | Get AI recommendation |
| `POST` | `/api/feedback` | Submit 👍👎🔖🚫 feedback |
| `GET` | `/api/roadmap` | Get personalized roadmap |
| `GET` | `/api/evolution` | Get interest evolution history |
| `GET` | `/api/analytics` | Get behavior analytics |
| `GET` | `/api/analytics/interest-profile` | Full AI interest profile |
| `POST` | `/api/profile/import-persona` | Import test persona |

---

## 🔐 Security

- API keys are stored in `.env` and loaded server-side via `python-dotenv`
- The browser **never** sees your Gemini API key
- Users can add their own key via Settings → it's stored in their Flask session only
- `.gitignore` excludes `.env`, `__pycache__`, `.venv`, and the SQLite database

---

## 🚀 Deployment (Render)

1. Push to GitHub (`.env` is gitignored)
2. Create a new **Web Service** on [render.com](https://render.com)
3. Set environment variables in Render's dashboard
4. Build command: `pip install -r requirements.txt`
5. Start command: `python run.py`

---

## 🏆 Competition Talking Points

> **"Our system doesn't ask 'Is this Java content?' — it asks 'What does watching 4 Java reels at 94% completion while saving 2 of them tell us about this student's true learning intent?'"**

- The **Hype Detector** rejects "10 AI tools that will replace you!" while accepting "How transformers actually work"
- The **Exploration mode** ensures students discover Cloud → DevOps → System Design even if they only searched for Java
- The **DNA Page** gives judges a visual story — not just a list of recommendations
- The **Feedback Loop** means the system gets smarter with every interaction
- Everything is explainable — no black-box decisions
