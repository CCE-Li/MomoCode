from __future__ import annotations

from app.modules.judge.runner import JudgeCase


def read_judge_config(
    expected_output_spec: object,
) -> tuple[list[JudgeCase], str | None]:
    if not isinstance(expected_output_spec, dict):
        return [], None
    judge = expected_output_spec.get("judge")
    if not isinstance(judge, dict):
        return [], None

    raw_cases = judge.get("test_cases")
    cases: list[JudgeCase] = []
    if isinstance(raw_cases, list):
        for item in raw_cases:
            if not isinstance(item, dict):
                continue
            test_input = item.get("input")
            output = item.get("output")
            if isinstance(test_input, str) and isinstance(output, str):
                cases.append(JudgeCase(input=test_input, expected_output=output))

    harness = judge.get("harness_main")
    return cases, harness if isinstance(harness, str) else None


def read_sample_cases(expected_output_spec: object) -> list[dict[str, str]]:
    if not isinstance(expected_output_spec, dict):
        return []
    judge = expected_output_spec.get("judge")
    if not isinstance(judge, dict):
        return []
    raw_samples = judge.get("samples")
    if not isinstance(raw_samples, list):
        return []

    samples: list[dict[str, str]] = []
    for item in raw_samples:
        if not isinstance(item, dict):
            continue
        test_input = item.get("input")
        output = item.get("output")
        if isinstance(test_input, str) and isinstance(output, str):
            samples.append({"input": test_input, "expected_output": output})
    return samples


def public_expected_output_spec(
    expected_output_spec: object,
) -> dict[str, object] | None:
    if not isinstance(expected_output_spec, dict):
        return None
    public = dict(expected_output_spec)
    public.pop("judge", None)
    return public
