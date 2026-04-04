"""
BugFixerEnv Task Definitions
Easy → Medium → Hard, each with buggy code + test cases + function name
"""

TASKS = {
    "easy": {
        "id": "easy",
        "description": (
            "Fix the bug in this Python function. "
            "It should return the sum of all integers from 1 to n (inclusive). "
            "For example, sum_to_n(5) should return 15."
        ),
        "buggy_code": """\
def sum_to_n(n):
    total = 0
    for i in range(n):   # BUG is somewhere in this function
        total += i
    return total""",
        "function_name": "sum_to_n",
        "test_cases": [
            {"args": [5],   "expected": 15},
            {"args": [10],  "expected": 55},
            {"args": [1],   "expected": 1},
            {"args": [100], "expected": 5050},
        ],
    },

    "medium": {
        "id": "medium",
        "description": (
            "Fix the bug in this Python function. "
            "It should find the maximum sum of any contiguous subarray (Kadane's algorithm). "
            "For example, max_subarray_sum([-2,1,-3,4,-1,2,1,-5,4]) should return 6."
        ),
        "buggy_code": """\
def max_subarray_sum(nums):
    if not nums:
        return 0
    max_sum = nums[0]
    current_sum = nums[0]
    for num in nums[1:]:
        current_sum = max(num, current_sum - num)   # BUG is somewhere in this function
        max_sum = max(max_sum, current_sum)
    return max_sum""",
        "function_name": "max_subarray_sum",
        "test_cases": [
            {"args": [[-2, 1, -3, 4, -1, 2, 1, -5, 4]], "expected": 6},
            {"args": [[1]],                               "expected": 1},
            {"args": [[-1, -2, -3]],                     "expected": -1},
            {"args": [[5, 4, -1, 7, 8]],                 "expected": 23},
            {"args": [[0, 0, 0]],                        "expected": 0},
        ],
    },

    "hard": {
        "id": "hard",
        "description": (
            "Fix ALL bugs in this Python function. "
            "It should check whether a string of brackets is valid: every opening bracket must "
            "have a matching closing bracket in the correct order. "
            "Handles '()', '[]', '{}'. "
            "For example, is_valid_parentheses('()[]{}') → True, is_valid_parentheses('(]') → False."
        ),
        "buggy_code": """\
def is_valid_parentheses(s):
    stack = []
    mapping = {')': '(', ']': '[', '}': '{'}
    for char in s:
        if char in mapping:
            top = stack.pop() if stack else '#'
            if mapping[char] != top:
                return True          # BUG 1 is on this line
        elif char in '([{':
            stack.append(char)
    return len(stack) > 0            # BUG 2 is on this line""",
        "function_name": "is_valid_parentheses",
        "test_cases": [
            {"args": ["()"],     "expected": True},
            {"args": ["()[]{}"], "expected": True},
            {"args": ["(]"],     "expected": False},
            {"args": ["([)]"],   "expected": False},
            {"args": ["{[]}"],   "expected": True},
            {"args": ["((("],    "expected": False},
            {"args": [""],       "expected": True},
        ],
    },
}
