from __future__ import annotations

import asyncio
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from app.core.config import get_settings

_settings = get_settings()
_TMPFS = "/tmp:rw,exec,size=64m"  # noqa: S108


@dataclass(frozen=True)
class JudgeCase:
    input: str
    expected_output: str | None


@dataclass(frozen=True)
class JudgeCaseResult:
    input: str
    expected_output: str | None
    actual_output: str
    status: str


def _case_status(code: int) -> str:
    if code == 124:
        return "time_limit_exceeded"
    if code != 0:
        return "runtime_error"
    return "ok"


def _normalize(value: str) -> str:
    return "\n".join(line.rstrip() for line in value.strip().splitlines())


async def judge_cpp(code: str, cases: list[JudgeCase]) -> dict[str, object]:
    if not cases:
        return {
            "result": "ungraded",
            "passed": 0,
            "total": 0,
            "message": "该任务尚未配置自动判题用例。",
        }

    docker = shutil.which("docker")
    if docker is None:
        return {
            "result": "ungraded",
            "passed": 0,
            "total": len(cases),
            "message": "判题服务不可用：未找到 Docker。",
        }

    token = uuid4().hex
    with tempfile.TemporaryDirectory(prefix="momocode-judge-") as tmp:
        workdir = Path(tmp)
        (workdir / "main.cpp").write_text(code, encoding="utf-8")
        for index, case in enumerate(cases, start=1):
            (workdir / f"in-{index:02d}.txt").write_text(case.input, encoding="utf-8")

        script = f"""
set -u
ulimit -f 1024
if ! g++ -O2 -std=c++17 -o /tmp/main /input/main.cpp 2>/tmp/compile.err; then
  echo "__COMPILE_{token}__"
  head -c 32768 /tmp/compile.err
  exit 0
fi
for f in /input/in-*.txt; do
  name=$(basename "$f" .txt)
  timeout 2 /tmp/main < "$f" > "/tmp/$name.out" 2>"/tmp/$name.err"
  status=$?
  echo "__CASE_{token}__${{name}}__$status"
  head -c 32768 "/tmp/$name.out"
  echo ""
  echo "__CASE_END_{token}__"
done
"""
        mount = f"{workdir.resolve()}:/input:ro"  # noqa: ASYNC240
        command = [
            docker,
            "run",
            "--rm",
            "--network",
            "none",
            "--memory",
            f"{_settings.judge_memory_mb}m",
            "--cpus",
            "0.5",
            "--pids-limit",
            "64",
            "--read-only",
            "--tmpfs",
            _TMPFS,
            "--security-opt",
            "no-new-privileges",
            "-v",
            mount,
            _settings.judge_docker_image,
            "sh",
            "-c",
            script,
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=_settings.judge_timeout_seconds,
            )
        except TimeoutError:
            process.kill()
            await process.wait()
            return {
                "result": "runtime_error",
                "passed": 0,
                "total": len(cases),
                "message": "判题超时。",
            }
        except OSError as exc:
            return {
                "result": "ungraded",
                "passed": 0,
                "total": len(cases),
                "message": f"判题服务启动失败：{exc}",
            }

    text = stdout.decode("utf-8", errors="replace")
    if process.returncode != 0 and not text.strip():
        return {
            "result": "ungraded",
            "passed": 0,
            "total": len(cases),
            "message": "判题容器启动失败。",
            "stderr": stderr.decode("utf-8", errors="replace")[:2000],
        }
    if f"__COMPILE_{token}__" in text:
        compile_output = text.split(f"__COMPILE_{token}__", 1)[1].strip()
        return {
            "result": "compile_error",
            "passed": 0,
            "total": len(cases),
            "compile_output": compile_output[:4000],
        }

    results: list[JudgeCaseResult] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        prefix = f"__CASE_{token}__"
        end_marker = f"__CASE_END_{token}__"
        if not line.startswith(prefix):
            index += 1
            continue
        parts = line.split("__")
        if len(parts) < 4:
            index += 1
            continue
        name = parts[2]
        exit_code = int(parts[3])
        index += 1
        output_lines: list[str] = []
        while index < len(lines) and lines[index] != end_marker:
            output_lines.append(lines[index])
            index += 1
        case_index = int(name.split("-")[-1]) - 1
        if 0 <= case_index < len(cases):
            actual = "\n".join(output_lines).strip()
            expected = cases[case_index].expected_output
            status = _case_status(exit_code)
            if (
                status == "ok"
                and expected is not None
                and _normalize(actual) != _normalize(expected)
            ):
                status = "wrong_answer"
            results.append(
                JudgeCaseResult(
                    input=cases[case_index].input,
                    expected_output=expected,
                    actual_output=actual[:4000],
                    status=status,
                )
            )
        index += 1

    passed = sum(1 for item in results if item.status == "ok")
    if passed == len(cases):
        result = "correct"
    elif passed > 0:
        result = "partial"
    elif any(item.status == "time_limit_exceeded" for item in results):
        result = "time_limit_exceeded"
    elif any(item.status == "runtime_error" for item in results):
        result = "runtime_error"
    else:
        result = "incorrect"

    if len(results) < len(cases):
        result = "runtime_error"

    return {
        "result": result,
        "passed": passed,
        "total": len(cases),
        "score": passed / len(cases),
        "cases": [
            {
                "input": item.input,
                "expected_output": item.expected_output,
                "actual_output": item.actual_output,
                "status": item.status,
            }
            for item in results
        ],
        "stderr": stderr.decode("utf-8", errors="replace")[:2000],
    }
