from pathlib import Path

from scripts.seed_content import load_bundle

CONTENT_DIR = Path(__file__).resolve().parents[2] / "content" / "seed" / "v2"


def test_v2_seed_contains_manual_knowledge_and_oj_tasks() -> None:
    bundle = load_bundle(CONTENT_DIR)

    assert len(bundle.categories) == 7
    assert len(bundle.algorithms) == 37
    assert len(bundle.skills) == 94
    assert len(bundle.tasks) == 200

    algorithm_slugs = {item.slug for item in bundle.algorithms}
    expected = {
        "fenwick",
        "segment-tree",
        "scc",
        "two-sat",
        "network-flow",
        "interval-dp",
        "advanced-number-theory",
        "persistent-segment-tree",
        "link-cut-tree",
        "ntt",
        "computational-geometry",
    }
    assert expected <= algorithm_slugs

    tags_by_slug = {item.slug: item.tags for item in bundle.tasks}
    assert "二分" in tags_by_slug["binary-search-template-001"]
    assert "树状数组" in tags_by_slug["manual-fenwick-template-001"]
    assert "BFS" in tags_by_slug["bfs-recognition-001"]
    assert all(item.tags for item in bundle.tasks)

    oj_tasks = [item for item in bundle.tasks if item.source_type == "oj_reference"]
    assert len(oj_tasks) == 106
    assert all(item.oj_platform and item.oj_problem_ref for item in oj_tasks)
    assert all(item.oj_problem_url for item in oj_tasks)
    assert all(item.oj_platform in {"codeforces", "luogu", "atcoder", "other"} for item in oj_tasks)
    assert all("tags=" not in (item.oj_problem_url or "") for item in oj_tasks)
    assert all("training/list" not in (item.oj_problem_url or "") for item in oj_tasks)
    assert all("exam/oj" not in (item.oj_problem_url or "") for item in oj_tasks)
