"""
BugFixerEnv — Baseline Inference Script

Required env variables:
  API_BASE_URL   – base URL of the running BugFixerEnv server
  MODEL_NAME     – model identifier
  HF_TOKEN       – HuggingFace API token
  OPENAI_API_KEY – alternative to HF_TOKEN (OpenAI key)

STDOUT FORMAT (mandatory):
  [START] task=<task_name> env=bugfixerenv model=<model_name>
  [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
  [END]   success=<true|false> steps=<n> score=<0.000> rewards=<r1,r2,...>
"""

import os
import sys
from typing import List, Optional

import requests
from openai import OpenAI

# ---------------------------------------------------------------------------
# Configuration from environment variables
# ---------------------------------------------------------------------------

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
MODEL_NAME   = os.getenv("MODEL_NAME",   "meta-llama/Llama-3.3-70B-Instruct")
HF_TOKEN     = os.getenv("HF_TOKEN",     "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
BENCHMARK    = "bugfixerenv"

# Accept either HF_TOKEN or OPENAI_API_KEY
API_KEY = HF_TOKEN or OPENAI_API_KEY

if not API_KEY:
    print("[ERROR] Set HF_TOKEN or OPENAI_API_KEY environment variable.", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# OpenAI-compatible client
# If OPENAI_API_KEY is set, use OpenAI directly.
# Otherwise use HuggingFace router.
# ---------------------------------------------------------------------------

if OPENAI_API_KEY and not HF_TOKEN:
    client = OpenAI(api_key=OPENAI_API_KEY)
else:
    client = OpenAI(
        base_url="https://router.huggingface.co/v1/",
        api_key=HF_TOKEN,
    )

# ---------------------------------------------------------------------------
# Structured log helpers — EXACT required format
# ---------------------------------------------------------------------------

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    action_clean = action.replace("\n", "\\n").replace("\r", "")
    error_val = error if error else "null"
    print(
        f"[STEP] step={step} action={action_clean} reward={reward:.2f} "
        f"done={str(done).lower()} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} "
        f"score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are an expert Python debugger. "
    "You will be given a buggy Python function and a description of what it should do. "
    "Return ONLY the fixed Python function — no explanation, no markdown fences, "
    "no comments, just the raw corrected Python code."
)


def build_user_prompt(description: str, buggy_code: str) -> str:
    return (
        f"Description:\n{description}\n\n"
        f"Buggy code:\n{buggy_code}\n\n"
        "Fix all bugs. Return only the corrected Python function."
    )


def strip_fences(text: str) -> str:
    lines = text.strip().splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


# ---------------------------------------------------------------------------
# Single episode
# ---------------------------------------------------------------------------

def run_episode(task_id: str) -> float:
    rewards: List[float] = []
    steps_taken = 0
    success = False
    score = 0.0

    log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)

    try:
        resp = requests.post(
            f"{API_BASE_URL}/reset",
            json={"task_id": task_id},
            timeout=30,
        )
        resp.raise_for_status()
        obs = resp.json()

        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": build_user_prompt(
                    obs["description"], obs["buggy_code"]
                )},
            ],
            max_tokens=512,
            temperature=0.0,
        )
        fixed_code = strip_fences(completion.choices[0].message.content)

        step_resp = requests.post(
            f"{API_BASE_URL}/step",
            json={"action": {"fixed_code": fixed_code}},
            timeout=30,
        )
        step_resp.raise_for_status()
        result = step_resp.json()

        reward = float(result["reward"])
        done   = bool(result["done"])
        steps_taken = 1
        rewards.append(reward)

        log_step(step=1, action=fixed_code, reward=reward, done=done, error=None)

        score   = reward
        success = score >= 1.0

    except Exception as exc:
        error_msg = str(exc)
        log_step(step=steps_taken + 1, action="", reward=0.0, done=True, error=error_msg)
        rewards.append(0.0)
        score   = 0.0
        success = False

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return score


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    tasks  = ["easy", "medium", "hard"]
    scores = []

    for task_id in tasks:
        score = run_episode(task_id)
        scores.append(score)

    avg = sum(scores) / len(scores) if scores else 0.0
    print(f"\nFINAL SCORES  easy={scores[0]:.2f}  medium={scores[1]:.2f}  "
          f"hard={scores[2]:.2f}  avg={avg:.2f}", flush=True)


if __name__ == "__main__":
    main()
