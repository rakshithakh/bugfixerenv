"""
BugFixerEnv – FastAPI Application
Exposes the OpenEnv-compatible HTTP interface.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from env import BugFixerEnv


# ---------------------------------------------------------------------------
# App + single shared environment instance
# ---------------------------------------------------------------------------

app = FastAPI(
    title="BugFixerEnv",
    description=(
        "OpenEnv-compatible environment where an agent is given a buggy Python "
        "function and must submit a corrected version.  Reward = test-pass rate (0–1)."
    ),
    version="1.0.0",
)

env = BugFixerEnv()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ResetRequest(BaseModel):
    task_id: str = "easy"


class StepRequest(BaseModel):
    action: dict


# ---------------------------------------------------------------------------
# Endpoints  (match hackathon spec exactly)
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "name":    "BugFixerEnv",
        "version": "1.0.0",
        "status":  "running",
        "tasks":   ["easy", "medium", "hard"],
        "docs":    "/docs",
    }


@app.post("/reset")
def reset(request: ResetRequest = None):            # noqa: B008
    """Start a new episode.  Optionally pass {"task_id": "easy"|"medium"|"hard"}."""
    task_id = (request.task_id if request else None) or "easy"
    try:
        return env.reset(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/step")
def step(request: StepRequest):
    """
    Submit a fix attempt.
    Body: {"action": {"fixed_code": "<your python code>"}}
    """
    try:
        return env.step(request.action)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/state")
def state():
    """Return the current observation without advancing the episode."""
    return env.state()
