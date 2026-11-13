from pathlib import Path

from scripts.seed_content import load_bundle

CONTENT_DIR = Path(__file__).resolve().parents[2] / "content" / "seed" / "v1"


def test_seed_content_structure() -> None:
    bundle = load_bundle(CONTENT_DIR)

    assert len(bundle.categories) == 3
    assert len(bundle.algorithms) == 10
    assert len(bundle.skills) == 40
    assert len(bundle.tasks) == 40

    skill_types = {skill.skill_type for skill in bundle.skills}
    assert skill_types == {"recognition", "base_implementation", "variant", "common_error"}

    for algorithm in bundle.algorithms:
        skills = [skill for skill in bundle.skills if skill.algorithm_slug == algorithm.slug]
        assert len(skills) == 4

    skill_to_algorithm = {skill.slug: skill.algorithm_slug for skill in bundle.skills}
    for algorithm in bundle.algorithms:
        task_types = {
            task.training_type
            for task in bundle.tasks
            if any(skill_to_algorithm[slug] == algorithm.slug for slug in task.target_skills)
        }
        assert task_types == {"recognition", "template", "variant", "correction"}

    assert all(task.oj_problem_url is None for task in bundle.tasks)
    assert all(task.source_type == "original" for task in bundle.tasks)
