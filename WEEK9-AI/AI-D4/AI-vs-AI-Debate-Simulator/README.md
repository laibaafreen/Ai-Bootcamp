# AI vs AI Debate Simulator ⚔️

Two AI agents debate opposing sides of a topic across multiple rounds; an impartial third AI judges the winner.

---

## 🚀 Features

- **Multi-Round Structured Debate**: Alternate turns between PROPOSITION (FOR) and OPPOSITION (AGAINST) for 2 or 3 rounds.
- **Round-by-Round Display**: Clear, formatted debate transcripts with speaker badges and round separation.
- **Impartial Judge Adjudication**: Objective evaluation declaring a winner with reasoned justification.
- **Transcript Export**: Download full transcripts directly from the UI.
- **Dual Architecture**: FastAPI backend + Streamlit frontend.

---

## 🛠️ Setup & Installation

### 1. Clone & Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the project root:
```env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-3.6-flash
```

---

## ▶️ Running the Application

### Step 1: Start FastAPI Backend (Terminal 1)
```bash
uvicorn main:app --reload --port 8000
```
or
```bash
python -m backend.main
```

### Step 2: Start Streamlit Frontend (Terminal 2)
```bash
streamlit run app.py
```

The Streamlit UI will open at `http://localhost:8501`.