"""
BugFixerEnv – Core Environment
Implements the OpenEnv interface: reset() / step() / state()
Includes typed Pydantic models for Observation, Action, and Reward.
"""

from pydantic import BaseModel, Field
from typing import Optional
from tasks import TASKS
from grader import grade


# ---------------------------------------------------------------------------
# Typed Pydantic Models (OpenEnv spec requirement)
# ---------------------------------------------------------------------------

class Observation(BaseModel):
    task_id: str = Field(..., description="Task identifier: easy | medium | hard")
    description: str = Field(..., description="What the function should do")
    buggy_code: str = Field(..., description="The broken Python function")
    steps_taken: int = Field(..., description="Number of steps taken so far")
    max_steps: int = Field(..., description="Maximum steps allowed per episode")
    last_reward: float = Field(..., description="Reward from the most recent step")
    done: bool = Field(..., description="Whether the episode is finished")


class Action(BaseModel):
    fixed_code: str = Field(..., description="Corrected Python source code")


class Reward(BaseModel):
    value: float = Field(..., ge=0.0, le=1.0, description="Reward value between 0.0 and 1.0")
    passed: int = Field(..., description="Number of test cases passed")
    total: int = Field(..., description="Total number of test cases")


class StepResult(BaseModel):
    state: Observation
    reward: float = Field(..., ge=0.0, le=1.0)
    done: bool
    info: dict


# ---------------------------------------------------------------------------
# Core Environment
# ---------------------------------------------------------------------------

class BugFixerEnv:
    """
    RL-style environment where an agent is shown a buggy Python function
    and must submit a fixed version. Reward = fraction of test cases passed.
    """

    MAX_STEPS = 5

    def __init__(self) -> None:
        self._task_id: Optional[str] = None
        self._obs: Optional[Observation] = None
        self._done: bool = True
        self._steps: int = 0

    # ------------------------------------------------------------------
    # OpenEnv interface
    # ------------------------------------------------------------------

    def reset(self, task_id: str = "easy") -> Observation:
        if task_id not in TASKS:
            raise ValueError(
                f"Unknown task_id '{task_id}'. Valid options: {list(TASKS.keys())}"
            )
        self._task_id = task_id
        self._done = False
        self._steps = 0
        self._obs = self._build_obs(task_id, steps=0, last_reward=0.0, done=False)
        return self._obs

    def step(self, action: Action) -> StepResult:
        if self._obs is None or self._task_id is None:
            raise RuntimeError("Call reset() before step().")

        if self._done:
            return StepResult(
                state=self._obs,
                reward=0.0,
                done=True,
                info={"message": "Episode finished. Call /reset to start again."},
            )

        fixed_code = action.fixed_code.strip()
        if not fixed_code:
            score, info = 0.0, {"passed": 0, "total": 0, "details": [],
                                 "message": "Empty submission."}
        else:
            score, info = grade(TASKS[self._task_id], fixed_code)

        self._steps += 1
        done = (score == 1.0) or (self._steps >= self.MAX_STEPS)
        self._done = done
        self._obs = self._build_obs(
            self._task_id, steps=self._steps, last_reward=score, done=done
        )

        return StepResult(
            state=self._obs,
            reward=score,
            done=done,
            info=info,
        )

    def state(self) -> Observation:
        if self._obs is None:
            return Observation(
                task_id="none",
                description="No active episode. Call /reset first.",
                buggy_code="",
                steps_taken=0,
                max_steps=self.MAX_STEPS,
                last_reward=0.0,
                done=True,
            )
        return self._obs

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_obs(self, task_id: str, steps: int, last_reward: float, done: bool) -> Observation:
        task = TASKS[task_id]
        return Observation(
            task_id=task_id,
            description=task["description"],
            buggy_code=task["buggy_code"],
            steps_taken=steps,
            max_steps=self.MAX_STEPS,
            last_reward=last_reward,
            done=done,
        )
