# 🐛 BugFixerEnv

> An OpenEnv-compatible reinforcement-learning environment where an agent reads a buggy Python function and submits a corrected version.  Reward = fraction of test cases passed (0.0 – 1.0).

---

## Table of Contents
- [Environment Description](#environment-description)
- [Observation Space](#observation-space)
- [Action Space](#action-space)
- [Tasks](#tasks)
- [Reward Function](#reward-function)
- [API Reference](#api-reference)
- [Setup & Running](#setup--running)
- [Docker](#docker)
- [Baseline Inference](#baseline-inference)
- [Reproducible Scores](#reproducible-scores)

---
## Why BugFixerEnv?

Modern software development heavily relies on automated debugging,
code review, and patch generation.

BugFixerEnv provides a controlled environment to evaluate AI agents
on realistic debugging tasks with deterministic scoring.
---
## Environment Description

BugFixerEnv simulates real-world code debugging. At each episode:

1. The environment presents a **buggy Python function** along with a plain-English description of what it _should_ do.
2. The agent submits `fixed_code` containing the corrected function.
3. The environment **executes the submission against hidden test cases** and returns a reward equal to the fraction passed.
4. The episode ends when the agent achieves a perfect score (1.0) or exhausts `max_steps` (5) attempts.

This mirrors the daily workflow of software engineers who must identify and fix bugs in unfamiliar code — a high-value, real-world task.

---

## Observation Space

```json
{
  "task_id":     "easy | medium | hard",
  "description": "What the function should do (natural language)",
  "buggy_code":  "The broken Python function",
  "steps_taken": 0,
  "max_steps":   5,
  "last_reward": 0.0,
  "done":        false
}
```

---

## Action Space

```json
{
  "fixed_code": "<corrected Python source code as a string>"
}
```

The submitted string must contain a valid Python function with the **same name** as the original.

---

## Tasks

| ID | Description | Bugs | Baseline Score |
|----|-------------|------|---------------|
| `easy` | `sum_to_n(n)` — sum integers 1…n | 1 (off-by-one in `range`) | 1.0 |
| `medium` | `max_subarray_sum(nums)` — Kadane's algorithm | 1 (`-` instead of `+`) | 1.0 |
| `hard` | `is_valid_parentheses(s)` — bracket matching | 2 (wrong return values) | 1.0 |

### Difficulty progression

- **Easy** — The bug is a single character change (`range(n)` → `range(1, n+1)`).  All 4 test cases fail with the buggy code.
- **Medium** — A subtle algorithmic error (`current_sum - num` should be `current_sum + num`). 2 of 5 test cases happen to pass with the bug, giving a partial-reward baseline of 0.40.
- **Hard** — Two independent bugs in a stack-based algorithm.  All 7 test cases fail with both bugs present, requiring the agent to find both issues.  Fixing only one bug yields a partial reward (≈ 0.29 – 0.71).

---

## Reward Function

```
reward = tests_passed / total_tests        # range: 0.0 – 1.0
```

**Partial progress is always rewarded.**  A submission that passes 3 of 5 tests receives 0.60, not 0.  This creates a meaningful gradient for learning agents.

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/`       | Health check + metadata |
| `POST` | `/reset`  | Start a new episode |
| `POST` | `/step`   | Submit a fix attempt |
| `GET`  | `/state`  | Peek at current state |

### POST `/reset`

```json
// Request body (optional – defaults to "easy")
{ "task_id": "easy" }

// Response: initial observation
{
  "task_id":    "easy",
  "description": "...",
  "buggy_code":  "...",
  "steps_taken": 0,
  "max_steps":   5,
  "last_reward": 0.0,
  "done":        false
}
```

### POST `/step`

```json
// Request body
{ "action": { "fixed_code": "def sum_to_n(n):\n    ..." } }

// Response
{
  "state":  { /* updated observation */ },
  "reward": 1.0,
  "done":   true,
  "info":   { "passed": 4, "total": 4, "details": [ ... ] }
}
```

### GET `/state`

Returns the current observation without consuming a step.

---

## Setup & Running

### Prerequisites

- Python 3.11+
- A HuggingFace account with API access (for `inference.py`)

### Local setup

```bash
git clone <your-repo>
cd project

pip install -r requirements.txt

# Start the server (default port 8000)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Browse the interactive API docs at [http://localhost:8000/docs](http://localhost:8000/docs).

### Quick smoke-test

```bash
# Reset to easy task
curl -X POST http://localhost:8000/reset \
     -H "Content-Type: application/json" \
     -d '{"task_id": "easy"}'

# Submit a fix
curl -X POST http://localhost:8000/step \
     -H "Content-Type: application/json" \
     -d '{"action": {"fixed_code": "def sum_to_n(n):\n    return sum(range(1, n+1))"}}'

# Check state
curl http://localhost:8000/state
```

---

## Docker

```bash
# Build
docker build -t bugfixerenv .

# Run  (HF Spaces uses port 7860)
docker run -p 7860:7860 \
  -e HF_TOKEN=hf_xxx \
  bugfixerenv
```

---

## Baseline Inference

`inference.py` runs a single-shot LLM agent across all three tasks.

```bash
export API_BASE_URL=http://localhost:8000      # or your HF Space URL
export MODEL_NAME=meta-llama/Llama-3.3-70B-Instruct
export HF_TOKEN=hf_xxx

python inference.py
```

Expected output:

```
============================================================
  BugFixerEnv — Baseline Inference
  Model : meta-llama/Llama-3.3-70B-Instruct
  Server: http://localhost:8000
============================================================

────────────────────────────────────────────────────────────
  Task: EASY
────────────────────────────────────────────────────────────
  Score : 1.0000  (4/4 tests passed)
    [✓] Test 1: passed
    [✓] Test 2: passed
    [✓] Test 3: passed
    [✓] Test 4: passed

────────────────────────────────────────────────────────────
  Task: MEDIUM
────────────────────────────────────────────────────────────
  Score : 1.0000  (5/5 tests passed)
    ...

────────────────────────────────────────────────────────────
  Task: HARD
────────────────────────────────────────────────────────────
  Score : 1.0000  (7/7 tests passed)
    ...

============================================================
  EASY   : 1.0000
  MEDIUM : 1.0000
  HARD   : 1.0000
  ──────────────────────────────────────────────────────────
  FINAL SCORE (avg): 1.0000
============================================================
```

---

## Reproducible Scores

All test cases are fully deterministic.  Given identical submitted code, `grade()` always returns the same score.  No randomness is involved in the environment or grader.

To reproduce the above baseline scores, run `inference.py` with `temperature=0.0` (already set) using `meta-llama/Llama-3.3-70B-Instruct` on HuggingFace.

---

## Project Structure

```
project/
├── main.py          # FastAPI app (API endpoints)
├── env.py           # Core environment logic
├── grader.py        # Scoring / test execution
├── tasks.py         # Task definitions (easy/medium/hard)
├── inference.py     # Baseline LLM agent
├── openenv.yaml     # OpenEnv spec config
├── requirements.txt
├── Dockerfile
└── README.md
```
