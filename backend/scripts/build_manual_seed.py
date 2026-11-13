"""Build the v2 content seed from the ICPC/CCPC manual plus the v1 seed.

The manual is the source of truth for section summaries, C++ templates and OJ
problem links. This script parses it once and writes a normal seed bundle so
the regular ``scripts.seed_content`` importer stays the only DB writer.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

from app.core.tags import normalize_tags
from scripts.seed_content import (
    AlgorithmSeed,
    CategorySeed,
    Manifest,
    SeedBundle,
    SkillSeed,
    TaskSeed,
    load_bundle,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MANUAL_PATH = REPO_ROOT / "content" / "source" / "MomoCode_ICPC_CCPC_算法知识点手册.md"
BASE_DIR = REPO_ROOT / "content" / "seed" / "v1"
OUTPUT_DIR = REPO_ROOT / "content" / "seed" / "v2"

SECTION_RE = re.compile(r"^### (\d+\.\d+\.\d+) (.+?)\s*$", re.MULTILINE)
LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", re.DOTALL)
CF_RE = re.compile(
    r"https?://(?:www\.)?codeforces\.com/"
    r"(?:problemset/problem/(\d+)/([A-Za-z]\d*)|contest/(\d+)/problem/([A-Za-z]\d*))"
)
LUOGU_RE = re.compile(r"https?://(?:www\.)?luogu\.com\.cn/problem/([A-Z]+\d+)")
ATCODER_RE = re.compile(r"https?://atcoder\.jp/contests/([^/]+)/tasks/([^/?#]+)")

ROLE_ORDER = {"经典": 0, "进阶": 1, "拓展": 2}
ROLE_SLUG = {"经典": "classic", "进阶": "advanced", "拓展": "extension"}

ALGORITHM_TAGS: dict[str, list[str]] = {
    "binary-search": ["二分", "二分查找", "二分答案"],
    "two-pointers": ["双指针", "滑动窗口"],
    "prefix-sum": ["前缀和"],
    "difference-array": ["差分"],
    "bfs": ["BFS", "广度优先搜索"],
    "dfs": ["DFS", "深度优先搜索"],
    "dijkstra": ["Dijkstra", "最短路"],
    "union-find": ["并查集", "DSU"],
    "knapsack-01": ["背包", "01背包"],
    "lis": ["LIS", "最长上升子序列"],
    "fenwick": ["树状数组", "Fenwick", "BIT"],
    "kruskal-mst": ["最小生成树", "Kruskal", "MST"],
    "greedy": ["贪心"],
    "backtracking": ["回溯", "搜索"],
    "number-theory-basics": ["数论", "快速幂", "素数筛", "GCD"],
    "string-algorithms": ["KMP", "Trie", "字符串哈希"],
    "coordinate-compression": ["离散化"],
    "segment-tree": ["线段树"],
    "monotonic-structures": ["单调栈", "单调队列", "RMQ"],
    "rollback-dsu": ["可撤销并查集", "回滚并查集"],
    "scc": ["SCC", "强连通分量", "Tarjan"],
    "two-sat": ["2-SAT"],
    "lca-hld": ["LCA", "树链剖分", "HLD"],
    "bipartite-matching": ["二分图匹配", "匈牙利算法"],
    "network-flow": ["网络流", "最大流", "Dinic", "费用流"],
    "interval-dp": ["区间DP", "树形DP", "状压DP"],
    "mo-cdq": ["莫队", "CDQ分治"],
    "advanced-number-theory": [
        "进阶数论",
        "莫比乌斯反演",
        "CRT",
        "Miller-Rabin",
        "Pollard-Rho",
    ],
    "advanced-strings": ["后缀数组", "SAM", "AC自动机", "Manacher"],
    "persistent-segment-tree": ["可持久化线段树", "主席树"],
    "balanced-bst": ["平衡树", "Treap", "Splay"],
    "link-cut-tree": ["LCT", "Link-Cut Tree"],
    "general-graph-matching": ["一般图匹配", "Blossom"],
    "min-cut-tree": ["最小割", "最小割树"],
    "dp-optimization": ["DP优化", "斜率优化", "决策单调性"],
    "ntt": ["NTT", "FFT", "多项式", "生成函数"],
    "computational-geometry": ["计算几何", "凸包", "扫描线"],
}

EXISTING_ALGORITHMS = {
    "1.1.1": "binary-search",
    "1.1.2": "prefix-sum",
    "1.1.4": "union-find",
    "1.2.2": "dijkstra",
    "1.3.1": "knapsack-01",
}

NEW_ALGORITHMS: dict[str, tuple[str, str]] = {
    "1.1.3": ("fenwick", "树状数组 Fenwick"),
    "1.2.1": ("kruskal-mst", "Kruskal 最小生成树"),
    "1.3.2": ("greedy", "贪心"),
    "1.3.3": ("backtracking", "回溯与基础搜索"),
    "1.4.1": ("number-theory-basics", "基础数论"),
    "1.4.2": ("string-algorithms", "KMP、Trie 与字符串哈希"),
    "2.1.1": ("coordinate-compression", "离散化"),
    "2.1.2": ("segment-tree", "线段树与懒标记"),
    "2.1.3": ("monotonic-structures", "RMQ、单调栈与单调队列"),
    "2.1.4": ("rollback-dsu", "可撤销并查集"),
    "2.2.1": ("scc", "强连通分量 SCC"),
    "2.2.2": ("two-sat", "2-SAT"),
    "2.2.3": ("lca-hld", "LCA 与树链剖分"),
    "2.2.4": ("bipartite-matching", "二分图匹配"),
    "2.2.5": ("network-flow", "网络流"),
    "2.3.1": ("interval-dp", "区间 DP、树形 DP 与状压 DP"),
    "2.3.2": ("mo-cdq", "莫队、分治与 CDQ"),
    "2.4.1": ("advanced-number-theory", "进阶数论"),
    "2.4.2": ("advanced-strings", "进阶字符串"),
    "3.1.1": ("persistent-segment-tree", "可持久化线段树"),
    "3.1.2": ("balanced-bst", "平衡树：Splay / Treap"),
    "3.1.3": ("link-cut-tree", "Link-Cut Tree"),
    "3.2.1": ("general-graph-matching", "一般图最大匹配 / Blossom"),
    "3.2.2": ("min-cut-tree", "最小割与最小割树"),
    "3.3.1": ("dp-optimization", "高级 DP 优化"),
    "3.3.2": ("ntt", "多项式与生成函数"),
    "3.3.3": ("computational-geometry", "计算几何与扫描线"),
}

CATEGORY_BY_PREFIX = {
    "1.1": "basics",
    "1.2": "graph-search",
    "1.3.1": "dynamic-programming",
    "1.3.2": "basics",
    "1.3.3": "graph-search",
    "1.4": "math-strings",
    "2.1": "data-structures",
    "2.2": "graph-search",
    "2.3": "dynamic-programming",
    "2.4": "math-strings",
    "3.1": "data-structures",
    "3.2": "advanced-graph",
    "3.3.1": "dynamic-programming",
    "3.3.2": "math-strings",
    "3.3.3": "geometry",
}

NEW_CATEGORIES = [
    CategorySeed(
        slug="data-structures",
        name="数据结构",
        description="树状数组、线段树、单调结构、可持久化与高级树结构。",
        sort_order=40,
    ),
    CategorySeed(
        slug="math-strings",
        name="数学与字符串",
        description="数论、组合计数、字符串匹配与多项式。",
        sort_order=50,
    ),
    CategorySeed(
        slug="advanced-graph",
        name="高级图论",
        description="一般图匹配、最小割树等金牌专题。",
        sort_order=60,
    ),
    CategorySeed(
        slug="geometry",
        name="计算几何",
        description="向量、凸包、扫描线与几何关系。",
        sort_order=70,
    ),
]


@dataclass(frozen=True)
class Problem:
    title: str
    url: str
    role: str
    platform: str
    ref: str


@dataclass(frozen=True)
class Section:
    number: str
    title: str
    purpose: str
    implementation: str
    template: str | None
    frequency: str
    related: list[str]
    problems: list[Problem]


def _clean(text: str) -> str:
    text = re.sub(r"^\s*-\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n\s*-\s+", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip().lstrip("：:").strip()


def _extract_block(body: str, marker: str) -> str:
    match = re.search(rf"\*\*{marker}[^\n]*\*\*(.*?)(?=\n-   \*\*|\n\*\*|\Z)", body, re.DOTALL)
    return _clean(match.group(1)) if match else ""


def _extract_template(body: str) -> str | None:
    marker = re.search(r"\*\*C\+\+ 模板", body)
    search_from = marker.end() if marker else 0
    match = re.search(
        r"```[ \t]*(?:cpp|c\+\+)?[ \t]*\r?\n(.*?)```",
        body[search_from:],
        re.DOTALL,
    )
    if match is None:
        return None
    template = match.group(1).strip("\n")
    return template or None


def _extract_related(body: str) -> list[str]:
    block = _extract_block(body, "关联")
    names = [re.sub(r"\s+", " ", match.group(1)).strip() for match in LINK_RE.finditer(block)]
    return [name for name in names if name]


def _problem_from_link(title: str, url: str, role: str) -> Problem | None:
    clean_title = re.sub(r"\s+", " ", title).strip()
    clean_title = re.sub(r"\s*（[^）]*）\s*$", "", clean_title).strip()

    cf_match = CF_RE.search(url)
    if cf_match:
        contest = cf_match.group(1) or cf_match.group(3) or ""
        index = cf_match.group(2) or cf_match.group(4) or ""
        ref = f"CF {contest}{index}"
        return Problem(clean_title or ref, url, role, "codeforces", ref)

    luogu_match = LUOGU_RE.search(url)
    if luogu_match:
        ref = luogu_match.group(1)
        return Problem(clean_title or ref, url, role, "luogu", ref)

    atcoder_match = ATCODER_RE.search(url)
    if atcoder_match:
        contest, task = atcoder_match.group(1), atcoder_match.group(2)
        ref = f"AtCoder {contest}/{task}"
        return Problem(clean_title or ref, url, role, "atcoder", ref)

    return None


def _extract_problems(body: str) -> list[Problem]:
    marker = re.search(r"\*\*题目\*\*", body)
    if marker is None:
        return []

    region = body[marker.end() :]
    cut = re.search(r"\*\*(?:ICPC / CCPC )?考频\*\*|\*\*关联\*\*", region)
    if cut is not None:
        region = region[: cut.start()]

    problems: list[Problem] = []
    seen: set[str] = set()
    role = "经典"
    for part in re.split(r"(经典|进阶|拓展|牛客补充|牛客)", region):
        if part in {"经典", "进阶", "拓展", "牛客补充", "牛客"}:
            role = part
            continue
        if role.startswith("牛客"):
            continue
        for match in LINK_RE.finditer(part):
            problem = _problem_from_link(match.group(1), match.group(2), role)
            if problem is None or problem.url in seen:
                continue
            seen.add(problem.url)
            problems.append(problem)
    return problems


def parse_sections(manual: str) -> list[Section]:
    headings = list(SECTION_RE.finditer(manual))
    sections: list[Section] = []
    for index, heading in enumerate(headings):
        number = heading.group(1)
        title = heading.group(2).strip()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(manual)
        body = manual[heading.end() : end]

        cut = re.search(r"^(?:#{1,2} |-----)", body, re.MULTILINE)
        if cut is not None:
            body = body[: cut.start()]

        purpose = _extract_block(body, "用途")
        implementation = _extract_block(body, "最简单实现")
        frequency = _extract_block(body, "考频")
        if not frequency:
            frequency = _extract_block(body, "ICPC / CCPC 考频")
        sections.append(
            Section(
                number=number,
                title=title,
                purpose=purpose,
                implementation=implementation,
                template=_extract_template(body),
                frequency=frequency,
                related=_extract_related(body),
                problems=_extract_problems(body),
            )
        )
    return sections


def _category_for(number: str) -> str:
    if number in CATEGORY_BY_PREFIX:
        return CATEGORY_BY_PREFIX[number]
    return CATEGORY_BY_PREFIX.get(number[:3], "basics")


def _difficulty_for(number: str) -> int:
    if number.startswith("3."):
        return 5
    if number.startswith("2."):
        return 4 if not number.startswith("2.4") else 5
    if number.startswith("1.4"):
        return 3
    return 2


def _first_sentence(text: str, fallback: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return fallback
    match = re.match(r"(.+?[。；;])", cleaned)
    sentence = match.group(1) if match else cleaned
    return sentence[:200]


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "item"


def _description(section: Section) -> str:
    parts = [f"### {section.title}", "", f"**用途**：{section.purpose or '见本节模板与例题。'}"]
    if section.implementation:
        parts.extend(["", f"**实现要点**：{section.implementation}"])
    if section.template:
        parts.extend(["", "**模板**：", "", "```cpp", section.template, "```"])
    if section.frequency:
        parts.extend(["", f"**考频**：{section.frequency}"])
    parts.extend(["", f"来源：ICPC/CCPC 算法知识点手册 {section.number}。"])
    return "\n".join(parts)


def _base_skills(
    algorithm_slug: str,
    algorithm_name: str,
    section: Section,
) -> tuple[SkillSeed, SkillSeed]:
    recognition = SkillSeed(
        slug=f"{algorithm_slug}-recognition",
        algorithm_slug=algorithm_slug,
        name=f"识别{algorithm_name}适用场景",
        skill_type="recognition",
        description_md=section.purpose or f"判断题目是否适合使用{algorithm_name}。",
        learning_objective=f"看到相关题目特征时，能判断可以使用{algorithm_name}。",
        mastery_evidence_md="识别任务连续正确，且最高提示等级不超过 1。",
        common_mistakes_md=f"忽略{algorithm_name}的适用前提；把模板套到不满足条件的问题上。",
        prerequisites=[],
        sort_order=10,
    )
    template = SkillSeed(
        slug=f"{algorithm_slug}-template",
        algorithm_slug=algorithm_slug,
        name=f"独立复现{algorithm_name}模板",
        skill_type="base_implementation",
        description_md=f"不看参考代码写出{algorithm_name}的核心模板。",
        learning_objective=f"能写出边界、初始化与复杂度正确的{algorithm_name}实现。",
        mastery_evidence_md="无提示或仅 1 级提示完成模板，并通过自评或 OJ 关联。",
        common_mistakes_md="边界与初始化错误；循环顺序或状态转移写反；未验证样例。",
        prerequisites=[recognition.slug],
        sort_order=20,
    )
    return recognition, template


def _recognition_task(
    algorithm_slug: str,
    algorithm_name: str,
    section: Section,
    difficulty: int,
    recognition_slug: str,
    template_slug: str,
) -> TaskSeed:
    return TaskSeed(
        slug=f"manual-{algorithm_slug}-recognition-001",
        title=f"识别：{algorithm_name}",
        training_type="recognition",
        evaluation_mode="auto_recognition",
        difficulty=difficulty,
        source_type="original",
        source_ref=f"manual:{section.number}",
        oj_platform=None,
        oj_problem_ref=None,
        oj_problem_url=None,
        statement_md=(
            f"## {section.title}\n\n"
            f"{section.purpose or '请根据题目特征选择最合适的算法。'}\n\n"
            "请选择最合适的技能。"
        ),
        constraints_md=None,
        input_spec={"answer": "selected_skill_ids", "multi_select": False},
        expected_output_spec={"target_skills": [recognition_slug]},
        code_scaffold=None,
        reference_solution_md=None,
        language="cpp17",
        hints={
            "1": "先看题目要求的操作类型、数据规模与单调性。",
            "2": f"检查是否满足{algorithm_name}的适用前提。",
            "3": "排除不满足前提或复杂度超限的算法。",
        },
        max_hint_level=3,
        error_types=[],
        target_skills=[recognition_slug],
        related_skills=[template_slug],
    )


def _template_task(
    algorithm_slug: str,
    algorithm_name: str,
    section: Section,
    difficulty: int,
    recognition_slug: str,
    template_slug: str,
) -> TaskSeed:
    reference = section.template or "该专题为接口/骨架型内容，请使用经过验证的实现并补充边界测试。"
    scaffold = (
        "#include <bits/stdc++.h>\nusing namespace std;\n\n"
        f"// TODO: 按手册 {section.number} 的模板实现 {algorithm_name}，并验证边界。\n"
    )
    return TaskSeed(
        slug=f"manual-{algorithm_slug}-template-001",
        title=f"模板：{algorithm_name}",
        training_type="template",
        evaluation_mode="self_assessment",
        difficulty=difficulty,
        source_type="original",
        source_ref=f"manual:{section.number}",
        oj_platform=None,
        oj_problem_ref=None,
        oj_problem_url=None,
        statement_md=(
            f"## {section.title}\n\n"
            f"**用途**：{section.purpose or '见参考实现。'}\n\n"
            f"**实现要点**：{section.implementation or '见参考实现。'}\n\n"
            "请从脚手架或空白写出核心模板，完成后对照参考实现检查边界与复杂度。"
        ),
        constraints_md="参考手册中的复杂度与边界；具体题目约束以 OJ 原题为准。",
        input_spec={
            "answer": "code",
            "self_assessment": ["correct", "partial", "incorrect"],
        },
        expected_output_spec={"evaluation": "self_assessment"},
        code_scaffold=scaffold,
        reference_solution_md=reference,
        language="cpp17",
        hints={
            "1": "先明确状态、不变量或核心循环。",
            "2": "写出模板主体，再检查初始化和终止条件。",
            "3": "用最小样例、边界样例和重复元素验证。",
        },
        max_hint_level=3,
        error_types=[],
        target_skills=[template_slug],
        related_skills=[recognition_slug],
    )


def _oj_task(
    algorithm_slug: str,
    section: Section,
    difficulty: int,
    recognition_slug: str,
    template_slug: str,
    problem: Problem,
    index: int,
) -> TaskSeed:
    role_slug = ROLE_SLUG.get(problem.role, "classic")
    ref_slug = _slugify(problem.ref)[:32]
    slug = f"manual-{algorithm_slug}-{_slugify(problem.platform)}-{ref_slug}-{role_slug}"
    if index > 1:
        slug = f"{slug}-{index}"
    slug = slug[:140]

    return TaskSeed(
        slug=slug,
        title=f"OJ：{problem.title}"[:200],
        training_type="variant",
        evaluation_mode="self_assessment",
        difficulty=min(5, difficulty + ROLE_ORDER.get(problem.role, 0)),
        source_type="oj_reference",
        source_ref=f"manual:{section.number}",
        oj_platform=problem.platform,
        oj_problem_ref=problem.ref,
        oj_problem_url=problem.url,
        statement_md=(
            f"## {section.title} · {problem.role}题\n\n"
            f"**题目**：[{problem.title}]({problem.url})\n\n"
            f"**本节要点**：{section.purpose or '先独立完成，再对照模板复盘。'}\n\n"
            "建议先在 OJ 独立完成，再回到 MomoCode 用本节模板复盘；"
            "完成后可在 OJ 提交验证，并把结果作为复习证据。"
        ),
        constraints_md="以 OJ 原题的数据范围与限制为准。",
        input_spec={
            "answer": "code",
            "self_assessment": ["correct", "partial", "incorrect"],
        },
        expected_output_spec={"evaluation": "self_assessment"},
        code_scaffold=None,
        reference_solution_md=None,
        language="cpp17",
        hints={
            "1": "先判断题目对应本节的哪个模型。",
            "2": "套用本节模板前，先确认前提与复杂度。",
            "3": "对照边界样例检查实现，再提交 OJ。",
        },
        max_hint_level=3,
        error_types=[],
        target_skills=[template_slug],
        related_skills=[recognition_slug],
    )


def build_seed(manual_text: str) -> SeedBundle:
    base = load_bundle(BASE_DIR)
    sections = parse_sections(manual_text)

    categories = {item.slug: item for item in base.categories}
    algorithms = {item.slug: item for item in base.algorithms}
    skills = {item.slug: item for item in base.skills}
    tasks = {item.slug: item for item in base.tasks}
    for category in NEW_CATEGORIES:
        categories.setdefault(category.slug, category)

    for section in sections:
        if section.number in EXISTING_ALGORITHMS:
            algorithm_slug = EXISTING_ALGORITHMS[section.number]
            algorithm = algorithms.get(algorithm_slug)
            if algorithm is None:
                continue
            extra = _description(section)
            algorithm.description_md = (
                f"{algorithm.description_md}\n\n{extra}" if algorithm.description_md else extra
            )
            algorithm_name = algorithm.name
        elif section.number in NEW_ALGORITHMS:
            algorithm_slug, algorithm_name = NEW_ALGORITHMS[section.number]
            if algorithm_slug not in algorithms:
                algorithms[algorithm_slug] = AlgorithmSeed(
                    slug=algorithm_slug,
                    category_slug=_category_for(section.number),
                    name=algorithm_name,
                    summary=_first_sentence(section.purpose, algorithm_name),
                    description_md=_description(section),
                    difficulty=_difficulty_for(section.number),
                    prerequisites=section.related[:5],
                )
        else:
            continue

        difficulty = algorithms[algorithm_slug].difficulty
        recognition_slug = f"{algorithm_slug}-recognition"
        template_slug = f"{algorithm_slug}-template"

        if recognition_slug not in skills or template_slug not in skills:
            recognition, template = _base_skills(algorithm_slug, algorithm_name, section)
            skills.setdefault(recognition_slug, recognition)
            skills.setdefault(template_slug, template)

        if section.number in NEW_ALGORITHMS:
            if f"manual-{algorithm_slug}-recognition-001" not in tasks:
                tasks[f"manual-{algorithm_slug}-recognition-001"] = _recognition_task(
                    algorithm_slug,
                    algorithm_name,
                    section,
                    difficulty,
                    recognition_slug,
                    template_slug,
                )
            if f"manual-{algorithm_slug}-template-001" not in tasks:
                tasks[f"manual-{algorithm_slug}-template-001"] = _template_task(
                    algorithm_slug,
                    algorithm_name,
                    section,
                    difficulty,
                    recognition_slug,
                    template_slug,
                )

        for index, problem in enumerate(section.problems, start=1):
            task = _oj_task(
                algorithm_slug,
                section,
                difficulty,
                recognition_slug,
                template_slug,
                problem,
                index,
            )
            tasks.setdefault(task.slug, task)

    skill_to_algorithm = {
        skill.slug: skill.algorithm_slug for skill in skills.values()
    }
    algorithm_names = {algorithm.slug: algorithm.name for algorithm in algorithms.values()}
    for task in tasks.values():
        tags: list[str] = []
        for skill_slug in task.target_skills:
            algorithm_slug = skill_to_algorithm.get(skill_slug)
            if algorithm_slug is None:
                continue
            tags.extend(
                ALGORITHM_TAGS.get(
                    algorithm_slug,
                    [algorithm_names.get(algorithm_slug, algorithm_slug)],
                )
            )
        task.tags = normalize_tags(tags)

    manifest = Manifest(
        version="2026.11.4",
        description=(
            "MomoCode 算法内容 v2：在 v1 基础上导入 ICPC/CCPC 手册的 "
            f"{len(sections)} 个知识章节、模板与 OJ 题目；"
            f"当前共 {len(algorithms)} 个算法、{len(skills)} 个技能、{len(tasks)} 个训练任务。"
        ),
        files=["categories.json", "algorithms.json", "skills.json", "tasks.json"],
    )

    return SeedBundle(
        manifest=manifest,
        categories=list(categories.values()),
        algorithms=list(algorithms.values()),
        skills=list(skills.values()),
        tasks=list(tasks.values()),
    )


def write_bundle(bundle: SeedBundle, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    payloads = {
        "manifest.json": bundle.manifest.model_dump(),
        "categories.json": [item.model_dump() for item in bundle.categories],
        "algorithms.json": [item.model_dump() for item in bundle.algorithms],
        "skills.json": [item.model_dump() for item in bundle.skills],
        "tasks.json": [item.model_dump() for item in bundle.tasks],
    }
    for name, payload in payloads.items():
        text = json.dumps(payload, ensure_ascii=False, indent=2)
        (output_dir / name).write_text(f"{text}\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the v2 manual content seed.")
    parser.add_argument("--manual", type=Path, default=MANUAL_PATH)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()

    manual_text = args.manual.read_text(encoding="utf-8")
    bundle = build_seed(manual_text)
    write_bundle(bundle, args.output_dir)
    print(
        f"Wrote {len(bundle.categories)} categories, {len(bundle.algorithms)} algorithms, "
        f"{len(bundle.skills)} skills, {len(bundle.tasks)} tasks to {args.output_dir}"
    )


if __name__ == "__main__":
    main()
