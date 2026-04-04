"""
BugFixerEnv – Core Environment
Implements the OpenEnv interface: reset() / step() / state()
"""

from tasks import TASKS
from grader import grade


class BugFixerEnv:
    """
    An RL-style environment where an agent is shown a buggy Python function
    and must submit a fixed version.  Reward = fraction of test cases passed.

    Observation space
    -----------------
    {
        "task_id"      : str   – "easy" | "medium" | "hard"
        "description"  : str   – what the function should do
        "buggy_code"   : str   – the broken implementation
        "steps_taken"  : int   – number of step() calls so far
        "max_steps"    : int   – episode ends after this many steps
        "last_reward"  : float – reward from the most recent step
        "done"         : bool  – whether the episode is finished
    }

    Action space
    ------------
    {
        "fixed_code" : str   – corrected Python source code
    }
    """

    MAX_STEPS = 5

    def __init__(self) -> None:
        self._task_id: str | None     = None
        self._state:   dict | None    = None
        self._done:    bool           = True
        self._steps:   int            = 0

    # ------------------------------------------------------------------
    # OpenEnv interface
    # ------------------------------------------------------------------

    def reset(self, task_id: str = "easy") -> dict:
        """Start a new episode for the given task."""
        if task_id not in TASKS:
            raise ValueError(
                f"Unknown task_id '{task_id}'. Valid options: {list(TASKS.keys())}"
            )

        self._task_id = task_id
        self._done    = False
        self._steps   = 0
        self._state   = self._build_state(task_id, steps=0, last_reward=0.0, done=False)
        return self._state

    def step(self, action: dict) -> dict:
        """
        Submit a fix attempt.

        Parameters
        ----------
        action : {"fixed_code": str}

        Returns
        -------
        {"state": dict, "reward": float, "done": bool, "info": dict}
        """
        if self._state is None or self._task_id is None:
            raise RuntimeError("Call reset() before step().")

        if self._done:
            return {
                "state":  self._state,
                "reward": 0.0,
                "done":   True,
                "info":   {"message": "Episode finished. Call /reset to start again."},
            }

        fixed_code = action.get("fixed_code", "").strip()
        if not fixed_code:
            score, info = 0.0, {"passed": 0, "total": 0, "details": [],
                                 "message": "Empty submission."}
        else:
            score, info = grade(TASKS[self._task_id], fixed_code)

        self._steps += 1
        done = (score == 1.0) or (self._steps >= self.MAX_STEPS)
        self._done  = done
        self._state = self._build_state(
            self._task_id, steps=self._steps, last_reward=score, done=done
        )

        return {
            "state":  self._state,
            "reward": score,
            "done":   done,
            "info":   info,
        }

    def state(self) -> dict:
        """Return the current observation without advancing the episode."""
        if self._state is None:
            return {"message": "No active episode. Call /reset first."}
        return self._state

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_state(self, task_id: str, steps: int, last_reward: float, done: bool) -> dict:
        task = TASKS[task_id]
        return {
            "task_id":      task_id,
            "description":  task["description"],
            "buggy_code":   task["buggy_code"],
            "steps_taken":  steps,
            "max_steps":    self.MAX_STEPS,
            "last_reward":  last_reward,
            "done":         done,
        }
