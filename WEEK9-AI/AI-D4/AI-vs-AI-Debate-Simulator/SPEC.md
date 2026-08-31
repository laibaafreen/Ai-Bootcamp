# SPEC.md — AI vs AI Debate Simulator

## 1. Problem Statement

**Who is the user?**
A student, debate-club member, or curious learner who wants to quickly explore both sides of a contentious or ambiguous topic without doing the research themselves.

**What friction are we solving?**
Understanding a topic fully usually means either reading multiple biased sources or manually playing devil's advocate with yourself. This is slow and people tend to only seek out arguments that confirm what they already believe. The Debate Simulator removes that friction: the user types one topic, and two AI debaters instantly generate structured, opposing arguments in real time, followed by an impartial verdict on which side argued more persuasively. It's a fast way to see a balanced, multi-round case for both sides of an issue.

## 2. MVP Scope

**Exactly 3 features — nothing more:**

1. **Multi-round debate** — user submits one topic; two LLM calls (FOR and AGAINST) alternate turns for 2–3 rounds, each responding to the opponent's previous point.
2. **Round-by-round display** — the full transcript is shown turn by turn, clearly labeled by speaker and round number.
3. **Judge verdict** — after the final round, a third LLM call reviews the full transcript and returns a winner plus a short reasoned justification.

**Explicitly out of scope (reject if suggested mid-build):**
- No saving/persisting past debates (no database, no local storage of history)
- No user accounts or login
- No more than 3 rounds
- No topic suggestions/autocomplete, no voice input, no sharing/export features
- No streaming token-by-token UI (full turn is returned and displayed at once)
- No multi-topic or multi-debate comparison views

If a teammate proposes any of the above during the build cycles, the Product Lead's job is to say no and point back to this list.

## 3. Tech Stack

- **Backend:** FastAPI (Python)
- **Data validation:** Pydantic models
- **Frontend:** Streamlit
- **LLM provider:** `google-genai` client
- **Config/secrets:** `python-dotenv`
- **HTTP calls (frontend → backend):** `requests`

## 4. Environment Setup

`.env` (never committed — must be in `.gitignore` from the first commit):
```
GOOGLE_API_KEY=your_key_here
```

`.env.example` (committed, no real values):
```
GOOGLE_API_KEY=
```

**Run instructions (for README):**
```
pip install -r requirements.txt
# Terminal 1
uvicorn main:app --reload
# Terminal 2
streamlit run app.py
```

## 5. Success Criteria (Definition of Done for MVP)

- A user can enter any topic, pick 2 or 3 rounds, and click one button to run the full debate.
- Every round is displayed with a clear FOR/AGAINST label.
- The judge always returns a specific winner (FOR or AGAINST) with 2–4 sentences of reasoning — not a generic "it's a tie" every time.
- Empty topic input is handled with a friendly message, not a crash.
- No API keys appear anywhere in the committed code.
