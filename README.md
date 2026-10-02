# 🎓 CampusAI

**An open-source AI learning companion built with Gemma, LangChain, ElevenLabs, and Streamlit.**

Built for **Hacktoberfest Hack Day Dinajpur 2026**.

## ✨ Features

- 📅 AI Study Planner
- 👨‍🏫 Gemma-powered AI Tutor
- 📝 Smart Quiz Generator
- 🔊 ElevenLabs text-to-speech
- 🧩 LangChain prompt/workflow orchestration
- 🌐 Streamlit web interface

## 🏗️ Architecture

```text
Student
   ↓
Streamlit UI
   ↓
LangChain
   ↓
Gemma
   ↓
Educational response
   ↓
ElevenLabs
   ↓
Voice output
```

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| UI | Streamlit |
| LLM | Gemma |
| Orchestration | LangChain |
| Voice | ElevenLabs |
| Language | Python |

## 🚀 Local Setup

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPO_URL
cd campusai
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API keys

Copy `.env.example` to `.env`:

```bash
copy .env.example .env
```

Then add your real API keys.

**Never commit `.env` to GitHub.**

### 5. Run

```bash
streamlit run app.py
```

## 🔐 Environment Variables

```text
GOOGLE_API_KEY
ELEVENLABS_API_KEY
GEMMA_MODEL
ELEVENLABS_MODEL
ELEVENLABS_VOICE_ID
```

The default Gemma model is configurable because model availability can vary by API account.

## 🏆 Hackathon Positioning

### Best Use of Gemma

Gemma is used as the core educational reasoning engine for:

- Personalized study plans
- Concept explanations
- Quiz generation

### Best Project Built with ElevenLabs

ElevenLabs converts AI-generated educational content into natural speech, allowing students to listen to explanations and study plans.

### Open-Source Quality

The repository is organized into separate modules for:

- LLM initialization
- LangChain workflows
- Text-to-speech
- Streamlit UI
- Configuration

## ⚠️ Disclaimer

CampusAI is an educational assistant. It is not a medical, psychological, legal, or financial diagnostic/advisory system.

## 📄 License

MIT License
"# campusAI_langchain_gemma_elevenlabs" 
