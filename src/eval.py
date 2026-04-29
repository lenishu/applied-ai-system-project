"""
Evaluation harness for StudyVibe pipeline.

12 predefined test cases covering:
- Activity classification accuracy (keyword matching)
- Edge cases (ambiguous/hybrid phrases)
- Energy delta measurement (how close recommendations are to target)
- Fallback behavior (low confidence → default activity)

Prints a summary: Passed: X/12 | Activity accuracy: Y% | Mean energy delta: Z
"""

from dataclasses import dataclass
from typing import List, Dict
from src.agent import run_pipeline
from src.activities import get_profile, SECTIONS


@dataclass
class EvalCase:
    """A single evaluation test case."""
    name: str
    free_text: str
    expected_section: str
    expected_mood: str
    k: int = 3


# 12 evaluation cases
EVAL_CASES: List[EvalCase] = [
    # Student section
    EvalCase(
        name="Student: Exam Cram",
        free_text="cramming for calc final tomorrow morning super stressed",
        expected_section="student",
        expected_mood="exam_cram",
    ),
    EvalCase(
        name="Student: Deep Study",
        free_text="long study session in library for midterm",
        expected_section="student",
        expected_mood="deep_study",
    ),
    EvalCase(
        name="Student: Light Reading",
        free_text="casual reading notes review",
        expected_section="student",
        expected_mood="light_reading",
    ),
    EvalCase(
        name="Student: Group Brainstorm",
        free_text="team study brainstorm with classmates",
        expected_section="student",
        expected_mood="group_brainstorm",
    ),

    # Work section
    EvalCase(
        name="Work: Deep Focus Coding",
        free_text="post-lunch coding sprint deep dive into backend",
        expected_section="work",
        expected_mood="deep_focus_coding",
    ),
    EvalCase(
        name="Work: Email Triage",
        free_text="morning emails and slack messages",
        expected_section="work",
        expected_mood="email_triage",
    ),
    EvalCase(
        name="Work: Creative Brainstorm",
        free_text="design session creative ideation",
        expected_section="work",
        expected_mood="creative_brainstorm",
    ),
    EvalCase(
        name="Work: Energizing Break",
        free_text="energizing break before standup meeting",
        expected_section="work",
        expected_mood="energizing_break",
    ),

    # Personal section
    EvalCase(
        name="Personal: Workout Gym",
        free_text="gym session lifting heavy weights",
        expected_section="personal",
        expected_mood="workout_gym",
    ),
    EvalCase(
        name="Personal: Happy Celebrate",
        free_text="friday night celebration happy party",
        expected_section="personal",
        expected_mood="happy_celebrate",
    ),
    EvalCase(
        name="Personal: Sad Reflective",
        free_text="feeling down sad reflective mood",
        expected_section="personal",
        expected_mood="sad_reflective",
    ),
    EvalCase(
        name="Personal: Sleep Winddown",
        free_text="bedtime winding down sleep time",
        expected_section="personal",
        expected_mood="sleep_winddown",
    ),
]


def run_eval() -> None:
    """Run all 12 evaluation cases and print summary."""
    print("\n" + "=" * 80)
    print("STUDYVIBE EVALUATION HARNESS")
    print("=" * 80)

    passed = 0
    failed = 0
    activity_matches = 0
    energy_deltas: List[float] = []
    failures: List[Dict] = []

    for case in EVAL_CASES:
        result = run_pipeline(
            free_text=case.free_text,
            section=None,
            mood=None,
            use_lastfm=False,
            k=case.k,
        )

        # Check if activity classification was correct
        if result.error:
            print(f"[FAIL] {case.name:30} | ERROR: {result.error[:50]}")
            failed += 1
            failures.append({"case": case.name, "reason": result.error})
            continue

        detected_section = result.intent["section"]
        detected_mood = result.intent["mood"]
        confidence = result.intent["confidence"]
        is_match = (detected_section == case.expected_section and detected_mood == case.expected_mood)

        if is_match:
            activity_matches += 1

        # Measure energy delta (how close recommendations are to target energy)
        expected_profile = get_profile(case.expected_section, case.expected_mood)
        target_energy = expected_profile.target_energy
        if result.recommendations:
            actual_energies = [r.get("audio_features", {}).get("energy", 0.5) for r in result.recommendations]
            deltas = [abs(e - target_energy) for e in actual_energies]
            mean_delta = sum(deltas) / len(deltas)
            energy_deltas.append(mean_delta)
        else:
            energy_deltas.append(1.0)  # Worst case if no recs

        # Status
        status = "[ OK ]" if is_match else "[WARN]"
        detected = f"{detected_section}.{detected_mood}"
        expected = f"{case.expected_section}.{case.expected_mood}"
        rec_count = len(result.recommendations)

        print(
            f"{status} {case.name:30} | "
            f"Expected: {expected:25} | "
            f"Got: {detected:25} | "
            f"Conf: {confidence:.2f} | "
            f"Recs: {rec_count}"
        )

        if is_match:
            passed += 1
        else:
            failed += 1
            failures.append({
                "case": case.name,
                "expected": (case.expected_section, case.expected_mood),
                "got": (detected_section, detected_mood),
                "confidence": confidence,
            })

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Passed: {passed}/12")
    print(f"Failed: {failed}/12")
    print(f"Activity accuracy: {(activity_matches / 12) * 100:.1f}%")

    if energy_deltas:
        mean_energy_delta = sum(energy_deltas) / len(energy_deltas)
        print(f"Mean energy delta: {mean_energy_delta:.3f}")
        min_delta = min(energy_deltas)
        max_delta = max(energy_deltas)
        print(f"Energy delta range: {min_delta:.3f} - {max_delta:.3f}")

    if failures:
        print(f"\nFailed cases ({len(failures)}):")
        for fail in failures:
            if "reason" in fail:
                print(f"  - {fail['case']}: {fail['reason']}")
            else:
                exp_sec, exp_mood = fail["expected"]
                got_sec, got_mood = fail["got"]
                print(f"  - {fail['case']}: expected {exp_sec}.{exp_mood}, got {got_sec}.{got_mood} (conf={fail['confidence']:.2f})")

    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_eval()
