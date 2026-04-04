"""
BugFixerEnv Grader
Executes submitted code against task test cases.
Returns deterministic score 0.0–1.0 with partial progress signals.
"""

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from typing import Any


# ---------------------------------------------------------------------------
# Safe execution helpers
# ---------------------------------------------------------------------------

def _execute(code: str, function_name: str, args: list) -> Any:
    """Run the student's function inside an isolated namespace."""
    namespace: dict = {}
    exec(compile(code, "<submitted>", "exec"), namespace)   # noqa: S102
    func = namespace.get(function_name)
    if func is None:
        raise NameError(f"Function '{function_name}' not found in submitted code.")
    return func(*args)


def _run_one(code: str, function_name: str, args: list, expected: Any, timeout: int = 5):
    """
    Run a single test case with a wall-clock timeout.
    Returns (passed: bool, message: str).
    """
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(_execute, code, function_name, args)
        try:
            result = future.result(timeout=timeout)
        except FuturesTimeout:
            return False, "Timed out (possible infinite loop)"
        except Exception as exc:
            return False, f"Runtime error: {exc}"

    if result == expected:
        return True, "passed"
    return False, f"Expected {expected!r}, got {result!r}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def grade(task: dict, fixed_code: str) -> tuple[float, dict]:
    """
    Grade submitted fixed_code against the task's test cases.

    Returns
    -------
    score : float   – fraction of tests passed (0.0–1.0)
    info  : dict    – {"passed": int, "total": int, "details": [...]}
    """
    test_cases   = task["test_cases"]
    function_name = task["function_name"]

    passed  = 0
    details = []

    for idx, tc in enumerate(test_cases, start=1):
        ok, msg = _run_one(fixed_code, function_name, tc["args"], tc["expected"])
        details.append({"test": idx, "passed": ok, "message": msg})
        if ok:
            passed += 1

    score = round(passed / len(test_cases), 4) if test_cases else 0.0
    info  = {"passed": passed, "total": len(test_cases), "details": details}
    return score, info
