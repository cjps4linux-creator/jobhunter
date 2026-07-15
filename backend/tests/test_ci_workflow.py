from __future__ import annotations

from pathlib import Path

import yaml

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml"


def test_ci_workflow_file_exists():
    assert WORKFLOW.is_file(), WORKFLOW


def test_ci_trigger_branches_are_master():
    data = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    assert data["on"]["push"]["branches"] == ["master"]
    assert data["on"]["pull_request"]["branches"] == ["master"]


def test_ci_has_lint_test_and_contract_jobs():
    data = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    jobs = data.get("jobs", {})
    assert "lint" in jobs
    assert "test" in jobs
    assert "api-contract" in jobs


def test_ci_test_job_uses_pytest_with_coverage():
    data = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = " ".join(
        step.get("run", "") for step in data["jobs"]["test"]["steps"]
    )
    assert "pytest" in steps
    assert "--cov-fail-under=72" in steps


def test_ci_api_contract_job_runs_contract_tests():
    data = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = " ".join(
        step.get("run", "") for step in data["jobs"]["api-contract"]["steps"]
    )
    assert "tests/test_api_contract.py" in steps
