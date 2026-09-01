from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

try:
    from .debate import run_debate
    from .models import DebateRequest, DebateResponse
except ImportError:
    from debate import run_debate
    from models import DebateRequest, DebateResponse

app = FastAPI(
    title="AI vs AI Debate Simulator API",
    description="Backend API for running multi-round AI debates with automated judging.",
    version="1.0.0",
)

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "AI vs AI Debate Simulator API is running",
    }


@app.post("/debate", response_model=DebateResponse)
def debate_endpoint(request: DebateRequest) -> DebateResponse:
    """Run a multi-round debate on the specified topic and return full transcript and verdict."""
    topic = request.topic.strip() if request.topic else ""
    if not topic:
        raise HTTPException(status_code=400, detail="Debate topic cannot be empty.")

    if request.num_rounds not in (2, 3):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid num_rounds ({request.num_rounds}). Debate simulator supports strictly 2 or 3 rounds.",
        )

    try:
        return run_debate(topic=topic, num_rounds=request.num_rounds)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Debate execution failed: {str(exc)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

