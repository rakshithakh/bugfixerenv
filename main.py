"""
BugFixerEnv – FastAPI Application
Exposes the OpenEnv-compatible HTTP interface.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from env import BugFixerEnv, Action

app = FastAPI(
    title="BugFixerEnv",
    description=(
        "OpenEnv-compatible environment where an agent is given a buggy Python "
        "function and must submit a corrected version. Reward = test-pass rate (0–1)."
    ),
    version="1.0.0",
)

env = BugFixerEnv()


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class ResetRequest(BaseModel):
    task_id: str = "easy"


class StepRequest(BaseModel):
    action: dict


# ---------------------------------------------------------------------------
# Endpoints
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
def reset(request: ResetRequest = None):
    task_id = (request.task_id if request else None) or "easy"
    try:
        obs = env.reset(task_id)
        return obs.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/step")
def step(request: StepRequest):
    try:
        action = Action(fixed_code=request.action.get("fixed_code", ""))
        result = env.step(action)
        return result.model_dump()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/state")
def state():
    return env.state().model_dump()
