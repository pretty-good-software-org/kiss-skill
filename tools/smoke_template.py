#!/usr/bin/env python3
"""Instantiate the repository with orgctl and verify the derived result."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path

DERIVED_NAME = "example-agent-skill"
DERIVED_ORIGIN = f"git@github.com:pretty-good-software-org/{DERIVED_NAME}.git"
IGNORED_NAMES = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "dist",
    "node_modules",
}
MISMATCHED_PLUGIN_NAME = "smoke-test-name-mismatch"


def build_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.pop("VIRTUAL_ENV", None)
    environment["MISE_ENV"] = "development"
    return environment


def run(directory: Path, arguments: list[str]) -> None:
    result = subprocess.run(arguments, cwd=directory, env=build_environment(), text=True)
    if result.returncode != 0:
        command = " ".join(arguments)
        raise RuntimeError(f"run {command} in {directory}: exit status {result.returncode}")


def run_capture(directory: Path, arguments: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments, cwd=directory, env=build_environment(), text=True, capture_output=True
    )


def invoke_lint_skill(repository: Path) -> subprocess.CompletedProcess[str]:
    return run_capture(repository, ["mise", "run", "lint:skill"])


def assert_skillctl_rejects_plugin_name_drift(
    repository: Path,
    run_lint_skill: Callable[[Path], subprocess.CompletedProcess[str]] = invoke_lint_skill,
) -> None:
    manifest_path = repository / ".claude-plugin/plugin.json"
    original_bytes = manifest_path.read_bytes()
    original_name = json.loads(original_bytes)["name"]
    try:
        mutated_manifest = json.loads(original_bytes)
        mutated_manifest["name"] = MISMATCHED_PLUGIN_NAME
        manifest_path.write_text(json.dumps(mutated_manifest))
        result = run_lint_skill(repository)
        combined_output = result.stdout + result.stderr
        if result.returncode == 0:
            raise RuntimeError(
                f"skillctl must reject a plugin name that drifts from the skill name, got: "
                f"{combined_output!r}"
            )
        diagnostic = (
            f'plugin name "{MISMATCHED_PLUGIN_NAME}" must match skill name "{original_name}"'
        )
        if diagnostic not in combined_output:
            raise RuntimeError(
                f"skillctl must report the name-drift diagnostic {diagnostic!r}, "
                f"got: {combined_output!r}"
            )
    finally:
        manifest_path.write_bytes(original_bytes)


def copy_source(source: Path, destination: Path) -> None:
    ignore = shutil.ignore_patterns(*sorted(IGNORED_NAMES))
    shutil.copytree(source, destination, dirs_exist_ok=True, ignore=ignore)


def initialize_git(repository: Path) -> None:
    run(repository, ["git", "init", "-q", "-b", "main"])
    run(repository, ["git", "add", "-A"])
    commit_command = [
        "git",
        "-c",
        "user.name=template-smoke",
        "-c",
        "user.email=template-smoke@example.com",
        "commit",
        "-qm",
        "chore: seed template fixture",
    ]
    run(repository, commit_command)
    run(repository, ["git", "remote", "add", "origin", DERIVED_ORIGIN])


def assert_paths_absent(repository: Path, paths: list[Path], label: str) -> None:
    present = [str(path.relative_to(repository)) for path in paths if path.exists()]
    if present:
        raise RuntimeError(f"initialized repository retained {label}: {present}")


def assert_identity_replaced(repository: Path) -> None:
    grep_result = subprocess.run(
        ["git", "grep", "-n", "template-agent-skill"],
        cwd=repository,
        capture_output=True,
        text=True,
    )
    if grep_result.returncode == 0:
        raise RuntimeError(f"template identity remains after initialization:\n{grep_result.stdout}")
    if grep_result.returncode != 1:
        raise RuntimeError(f"search initialized repository: exit status {grep_result.returncode}")


def assert_initialized(repository: Path) -> None:
    manifest_path = repository / "template.init.toml"
    if manifest_path.exists():
        raise RuntimeError(f"orgctl must remove {manifest_path}")

    if (repository / "SKILL.md").exists():
        raise RuntimeError("orgctl must not retain a root compatibility skill")
    manifest = json.loads((repository / ".claude-plugin/plugin.json").read_text())
    skill_path = repository / "skills" / manifest["name"] / "SKILL.md"
    if not skill_path.is_file():
        raise RuntimeError(f"orgctl must retain the nested authoritative skill at {skill_path}")

    assert_paths_absent(
        repository,
        [repository / "tools/validate_skill.py", repository / "tests/test_validate_skill.py"],
        "the retired repository-only validator; skillctl now owns validation",
    )

    assert_paths_absent(
        repository,
        [
            repository / "tools/smoke_template.py",
            repository / "tests/test_smoke_template.py",
            repository / "mise-tasks/test/template-smoke",
        ],
        "template-only smoke tooling",
    )

    assert_paths_absent(
        repository,
        [
            repository / "scripts/package_skill.py",
            repository / "scripts/validate_skill.py",
            repository / "tools/package_skill.py",
            repository / "mise-tasks/package/skill",
            repository / "tests/test_package_skill.py",
        ],
        "packaging or runtime tooling",
    )

    assert_identity_replaced(repository)


def assert_apm_deployed_tree(
    deployed_skills_root: Path, source_root: Path, repository_name: str
) -> None:
    source_paths = {
        path.relative_to(source_root) for path in source_root.rglob("*") if path.is_file()
    }
    expected_paths = {Path(repository_name) / path for path in source_paths}
    actual_paths = {
        path.relative_to(deployed_skills_root)
        for path in deployed_skills_root.rglob("*")
        if path.is_file()
    }
    if actual_paths != expected_paths:
        raise RuntimeError(
            f"APM deployed tree {sorted(map(str, actual_paths))}, "
            f"expected only {sorted(map(str, expected_paths))}"
        )


def verify_apm_consumer(repository: Path) -> None:
    # APM copies local packages as distributable content; test fixtures must not
    # contribute host-runtime symlinks to that package boundary.
    for generated_path in (repository / ".venv", repository / ".lint"):
        shutil.rmtree(generated_path, ignore_errors=True)
    consumer = repository.parent / "apm-consumer"
    consumer.mkdir()
    (consumer / "apm.yml").write_text(
        """name: smoke-consumer
version: 1.0.0
description: Isolated APM consumer for template smoke validation
targets:
  - agent-skills
dependencies:
  apm:
    - path: ../example-agent-skill
"""
    )
    run(consumer, ["apm", "install"])
    deployed_root = consumer / ".agents/skills" / repository.name
    deployed_skill = deployed_root / "SKILL.md"
    if not deployed_skill.is_file():
        raise RuntimeError(f"APM must deploy the nested skill subtree to {deployed_skill}")
    source_root = repository / "skills" / repository.name
    assert_apm_deployed_tree(deployed_root.parent, source_root, repository.name)
    run(consumer, ["apm", "audit", "--ci", "--no-policy"])


def verify_derived_repository(repository: Path) -> None:
    run(repository, ["mise", "trust"])
    run(repository, ["mise", "run", "setup:default"])
    assert_skillctl_rejects_plugin_name_drift(repository)
    for command in (
        ["mise", "run", "format:markdown"],
        ["mise", "run", "lint:default"],
        ["claude", "plugin", "validate", "."],
        ["uv", "run", "pytest", "-q"],
    ):
        run(repository, command)
    verify_apm_consumer(repository)


def main() -> int:
    source = Path(__file__).resolve().parent.parent
    with tempfile.TemporaryDirectory(prefix="agent-skill-template-") as temporary_directory:
        repository = Path(temporary_directory) / DERIVED_NAME
        copy_source(source, repository)
        initialize_git(repository)
        run(repository, ["orgctl", "repo", "init", "."])
        assert_initialized(repository)
        verify_derived_repository(repository)
    print("derived repository smoke test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
