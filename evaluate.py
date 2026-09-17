"""Run the supplied synthetic evaluation cases against the decision pipeline."""

import json
from pathlib import Path

from src.decision import DecisionServiceError, create_decision
from src.schemas import TicketCreate


CASES_FILE = Path(__file__).resolve().parent / "data" / "sample_test_cases.json"


def main() -> None:
    cases = json.loads(CASES_FILE.read_text(encoding="utf-8"))
    correct = 0
    for case in cases:
        payload = {key: value for key, value in case.items() if key not in {"case_id", "expected_action"}}
        try:
            actual_action = create_decision(TicketCreate(**payload)).action
        except DecisionServiceError as exc:
            actual_action = f"ERROR: {exc}"
        is_correct = actual_action == case["expected_action"]
        correct += is_correct
        result = "correct" if is_correct else "incorrect"
        print(f"{case['case_id']}: {result} (expected {case['expected_action']}, got {actual_action})")

    total = len(cases)
    print(f"\n{total} test cases")
    print(f"Correct: {correct}")
    print(f"Incorrect: {total - correct}")
    print(f"Accuracy: {correct / total:.0%}")


if __name__ == "__main__":
    main()
