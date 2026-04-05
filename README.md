---
title: Bugfixerenv
emoji: 🐛
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
tags:
  - openenv
---

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

- **Easy** — Single character change. All 4 test cases fail with buggy code.
- **Medium** — Subtle algorithmic error. 2 of 5 tests pass with bug (partial reward = 0.40).
- **Hard** — Two independent bugs. Fixing one yields partial reward (0.29–0.71), both needed for 1.0.

---

## Reward Function

```
reward = tests_passed / total_tests   # range: 0.0 – 1.0
```

Partial progress is always rewarded. A submission passing 3 of 5 tests receives 0.60, not 0. This creates a meaningful gradient for learning agents.

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/`      | Health check |
| `POST` | `/reset` | Start a new episode |
| `POST` | `/step`  | Submit a fix attempt |
| `GET`  | `/state` | Peek at current state |

---

## Setup & Running

```bash
git clone https://github.com/rakshithakh/bugfixerenv
cd bugfixerenv
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Browse docs at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## Docker

```bash
docker build -t bugfixerenv .
docker run -p 7860:7860 bugfixerenv
```

---

## Baseline Inference

```bash
export API_BASE_URL=https://rakshithakho-bugfixerenv.hf.space
export MODEL_NAME=meta-llama/Llama-3.3-70B-Instruct
export HF_TOKEN=hf_xxx

python inference.py
```

### Baseline Scores

| Task | Score |
|------|-------|
| easy | 1.00 |
| medium | 1.00 |
| hard | 1.00 |
| **average** | **1.00** |

---

## Reproducible Scores

All test cases are fully deterministic. `temperature=0.0` ensures reproducible LLM outputs. Same input always produces same score.

---

## Project Structure

```
bugfixerenv/
├── main.py          # FastAPI app
├── env.py           # Core environment logic
├── grader.py        # Scoring / test execution
├── tasks.py         # Task definitions
├── inference.py     # Baseline agent
├── openenv.yaml     # OpenEnv spec
├── pyproject.toml   # Project metadata
├── uv.lock          # Locked dependencies
├── requirements.txt
├── Dockerfile
├── README.md
└── server/
    └── app.py       # Server entry point
```
