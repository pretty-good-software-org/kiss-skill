"""Regression tests for the derived-repository name-drift smoke helper."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from smoke_template import (  # noqa: E402
    MISMATCHED_PLUGIN_NAME,
    assert_apm_deployed_tree,
    assert_skillctl_rejects_plugin_name_drift,
)

ORIGINAL_MANIFEST_BYTES = b'{\n  "name": "fixture-skill",\n  "version": "1.0.0"\n}\n'


def write_plugin(root: Path) -> Path:
    (root / ".claude-plugin").mkdir(parents=True)
    (root / ".claude-plugin/plugin.json").write_bytes(ORIGINAL_MANIFEST_BYTES)
    return root


def fake_lint_skill(returncode: int, output: str):
    def run_lint_skill(repository: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=["mise", "run", "lint:skill"], returncode=returncode, stdout=output, stderr=""
        )

    return run_lint_skill


def write_skill_tree(root: Path) -> tuple[Path, Path]:
    source_root = root / "skills" / "fixture-skill"
    source_root.mkdir(parents=True)
    (source_root / "SKILL.md").write_text("skill")
    deployed_skills_root = root / ".agents" / "skills"
    deployed_skill = deployed_skills_root / "fixture-skill" / "SKILL.md"
    deployed_skill.parent.mkdir(parents=True)
    deployed_skill.write_text("skill")
    return deployed_skills_root, source_root


def test_rejects_unexpected_sibling_package_in_apm_deployed_tree(tmp_path: Path) -> None:
    deployed_skills_root, source_root = write_skill_tree(tmp_path)
    unexpected = deployed_skills_root / "unexpected-package" / "SKILL.md"
    unexpected.parent.mkdir()
    unexpected.write_text("unexpected")

    with pytest.raises(RuntimeError, match="APM deployed tree"):
        assert_apm_deployed_tree(deployed_skills_root, source_root, "fixture-skill")


def test_rejects_unexpected_sibling_file_in_apm_deployed_tree(tmp_path: Path) -> None:
    deployed_skills_root, source_root = write_skill_tree(tmp_path)
    (deployed_skills_root / "unexpected-file.txt").write_text("unexpected")

    with pytest.raises(RuntimeError, match="APM deployed tree"):
        assert_apm_deployed_tree(deployed_skills_root, source_root, "fixture-skill")


def test_passes_and_restores_manifest_when_skillctl_reports_the_name_drift_diagnostic(
    tmp_path: Path,
) -> None:
    repository = write_plugin(tmp_path)
    diagnostic = (
        f'FAIL: plugin name "{MISMATCHED_PLUGIN_NAME}" must match skill name "fixture-skill"\n'
    )
    assert_skillctl_rejects_plugin_name_drift(
        repository, run_lint_skill=fake_lint_skill(1, diagnostic)
    )
    assert (repository / ".claude-plugin/plugin.json").read_bytes() == ORIGINAL_MANIFEST_BYTES, (
        "the manifest must be restored byte-for-byte after a passing check"
    )


def test_raises_and_still_restores_manifest_when_skillctl_wrongly_accepts_the_drift(
    tmp_path: Path,
) -> None:
    repository = write_plugin(tmp_path)
    passing_output = "skill and plugin structure are valid\n"
    with pytest.raises(RuntimeError, match="must reject a plugin name that drifts"):
        assert_skillctl_rejects_plugin_name_drift(
            repository, run_lint_skill=fake_lint_skill(0, passing_output)
        )
    assert (repository / ".claude-plugin/plugin.json").read_bytes() == ORIGINAL_MANIFEST_BYTES, (
        "the manifest must be restored even when skillctl wrongly accepts the drift"
    )


def test_raises_and_still_restores_manifest_when_the_diagnostic_text_is_missing(
    tmp_path: Path,
) -> None:
    repository = write_plugin(tmp_path)
    unrelated_failure = "FAIL: SKILL.md not found\n"
    with pytest.raises(RuntimeError, match="must report the name-drift diagnostic"):
        assert_skillctl_rejects_plugin_name_drift(
            repository, run_lint_skill=fake_lint_skill(1, unrelated_failure)
        )
    assert (repository / ".claude-plugin/plugin.json").read_bytes() == ORIGINAL_MANIFEST_BYTES, (
        "the manifest must be restored even when the diagnostic text does not match"
    )
