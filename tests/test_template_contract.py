"""Contract checks for orgctl initialization of derived repositories."""

from __future__ import annotations

import json
import re

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def assert_plugin_manifest_contract(manifest: dict[str, object]) -> None:
    required_fields = ["name", "version", "description", "author"]
    allowed_fields = required_fields + ["dependencies"]
    expected_fields = required_fields + (["dependencies"] if "dependencies" in manifest else [])
    assert list(manifest) == expected_fields, (
        "plugin manifest fields must be canonical and keep marketplace dependencies ordered"
    )
    assert set(manifest) <= set(allowed_fields)
    if "dependencies" in manifest:
        dependencies = manifest["dependencies"]
        assert isinstance(dependencies, list), "marketplace dependencies must be an ordered list"
        for dependency in dependencies:
            assert isinstance(dependency, dict), "marketplace dependencies must be objects"
            assert set(dependency) == {"name", "marketplace"}, (
                "marketplace dependencies must contain exactly name and marketplace"
            )
            assert all(isinstance(value, str) for value in dependency.values()), (
                "marketplace dependency name and marketplace must be strings"
            )


def test_every_uv_run_in_tasks_and_hooks_passes_locked() -> None:
    entry_points = sorted((REPO_ROOT / "mise-tasks").rglob("*")) + sorted(
        (REPO_ROOT / "lefthook").glob("*.yml")
    )
    unlocked = [
        f"{path.relative_to(REPO_ROOT)}:{number}: {line.strip()}"
        for path in entry_points
        if path.is_file()
        for number, line in enumerate(path.read_text().splitlines(), start=1)
        if re.search(r"\buv run(?! --locked\b)", line)
    ]
    assert unlocked == [], (
        f"plain uv run re-locks a stale uv.lock silently; pass --locked: {unlocked}"
    )


def test_dependabot_updates_python_dependencies_through_uv() -> None:
    config = (REPO_ROOT / ".github/dependabot.yml").read_text()
    ecosystems = re.findall(r"^\s*- package-ecosystem: (\S+)$", config, flags=re.MULTILINE)
    assert ecosystems == ["github-actions", "uv"], (
        f"the pip ecosystem bumps pyproject.toml without refreshing uv.lock: {ecosystems}"
    )


def test_yamllint_ignores_generated_apm_artifacts() -> None:
    config = (REPO_ROOT / ".yamllint.yml").read_text()
    expected_ignore = """ignore: |
  apm.lock.yaml
  apm_modules/
"""
    assert expected_ignore in config, (
        "Yamllint must not lint generated APM locks or downloaded dependencies"
    )


def test_template_init_renames_the_nested_skill_directory() -> None:
    manifest_path = REPO_ROOT / "template.init.toml"
    if manifest_path.exists():
        manifest = tomllib.loads(manifest_path.read_text())
        assert manifest["rename"] == {"skills/template-agent-skill": "skills/{repo}"}, (
            "orgctl must rename the canonical nested skill directory"
        )
        return
    plugin = json.loads((REPO_ROOT / ".claude-plugin/plugin.json").read_text())
    assert not (REPO_ROOT / "SKILL.md").exists(), (
        "initialized repository must not keep a root skill"
    )
    skill_path = REPO_ROOT / "skills" / plugin["name"] / "SKILL.md"
    assert skill_path.is_file(), "initialized repository must retain the nested skill"
    assert plugin["name"] == REPO_ROOT.name, (
        "initialized plugin identity must use the repository name"
    )


def test_template_init_removes_only_the_template_smoke_fixture_in_order() -> None:
    manifest_path = REPO_ROOT / "template.init.toml"
    smoke_fixture_paths = [
        REPO_ROOT / "tools/smoke_template.py",
        REPO_ROOT / "tests/test_smoke_template.py",
        REPO_ROOT / "mise-tasks/test/template-smoke",
    ]
    if not manifest_path.exists():
        present_paths = [
            str(path.relative_to(REPO_ROOT)) for path in smoke_fixture_paths if path.exists()
        ]
        assert present_paths == [], (
            f"initialized repository must not retain the template-only smoke fixture: "
            f"{present_paths}"
        )
        return
    manifest = tomllib.loads(manifest_path.read_text())
    assert manifest["remove"] == [
        "tools/smoke_template.py",
        "tests/test_smoke_template.py",
        "mise-tasks/test/template-smoke",
    ], (
        "orgctl must remove exactly the template-only smoke fixture, "
        "script and its test before the task"
    )
    for entry in manifest["remove"]:
        assert (REPO_ROOT / entry).is_file(), (
            f"remove entry {entry} must name a real, git-tracked template-only path"
        )
    assert "template.init.toml" not in manifest["remove"], (
        "the manifest deletes itself through its own dedicated orgctl step, never via remove"
    )


def test_template_delegates_validation_to_skillctl_and_omits_packaging() -> None:
    tools = REPO_ROOT / "tools"
    if (REPO_ROOT / "template.init.toml").exists():
        assert (tools / "smoke_template.py").is_file(), (
            "the canonical template must retain its initialization smoke test"
        )
        assert (REPO_ROOT / "tests/test_smoke_template.py").is_file(), (
            "the canonical template must retain the name-drift smoke helper regression test"
        )
    obsolete_paths = [
        REPO_ROOT / "tools/validate_skill.py",
        REPO_ROOT / "tests/test_validate_skill.py",
        REPO_ROOT / "scripts/package_skill.py",
        REPO_ROOT / "scripts/validate_skill.py",
        REPO_ROOT / "tools/package_skill.py",
        REPO_ROOT / "mise-tasks/package/skill",
        REPO_ROOT / "tests/test_package_skill.py",
    ]
    present_paths = [str(path.relative_to(REPO_ROOT)) for path in obsolete_paths if path.exists()]
    assert present_paths == [], (
        f"skillctl owns validation; derived plugins must not inherit a copied validator, "
        f"packaging, or runtime tooling: {present_paths}"
    )


def test_ci_lint_excludes_private_skillctl_and_development_lint_includes_it() -> None:
    default_task = (REPO_ROOT / "mise-tasks/lint/default").read_text()
    development_task = (REPO_ROOT / "mise-tasks/lint/development").read_text()
    assert "lint:skill" not in default_task, "CI lint must not require private skillctl"
    assert "lint:skill" in development_task, "development lint must retain skill validation"


def test_template_pins_skillctl_v2_and_validates_directly() -> None:
    tool_name = "github:pretty-good-software-org/skillctl"
    mise_config = tomllib.loads((REPO_ROOT / ".mise.development.toml").read_text())
    assert mise_config["tools"][tool_name] == "2.1.0", (
        "the template must pin the released skillctl v2.1 plugin contract"
    )

    expected_task = """#!/usr/bin/env bash
#MISE description="Validate the plugin and Agent Skill structure"
set -euo pipefail

MISE_ENV=development mise exec -- skillctl validate claude-plugin .
"""
    assert (REPO_ROOT / "mise-tasks/lint/skill").read_text() == expected_task, (
        "plugin repositories must invoke skillctl directly"
    )
    assert not (REPO_ROOT / "tools/validate_skillctl.py").exists(), (
        "plugin repositories must not retain the retired skillctl adapter"
    )

    expected_lock = {
        "version": "2.1.0",
        "backend": tool_name,
        "platforms.linux-arm64": {
            "checksum": "sha256:2aab0283884caa9b14edfb219a892554c50b3e390f7ba3c9ef460eee3591dcb6",
            "url": "https://github.com/pretty-good-software-org/skillctl/releases/download/v2.1.0/skillctl_2.1.0_linux_arm64.tar.gz",
            "url_api": "https://api.github.com/repos/pretty-good-software-org/skillctl/releases/assets/491538630",
        },
        "platforms.linux-arm64-musl": {
            "checksum": "sha256:2aab0283884caa9b14edfb219a892554c50b3e390f7ba3c9ef460eee3591dcb6",
            "url": "https://github.com/pretty-good-software-org/skillctl/releases/download/v2.1.0/skillctl_2.1.0_linux_arm64.tar.gz",
            "url_api": "https://api.github.com/repos/pretty-good-software-org/skillctl/releases/assets/491538630",
        },
        "platforms.linux-x64": {
            "checksum": "sha256:42c2e345794229875776ec46ee8390d99fe3d2baccf0b47e199341dc66f71420",
            "url": "https://github.com/pretty-good-software-org/skillctl/releases/download/v2.1.0/skillctl_2.1.0_linux_amd64.tar.gz",
            "url_api": "https://api.github.com/repos/pretty-good-software-org/skillctl/releases/assets/491538663",
        },
        "platforms.linux-x64-musl": {
            "checksum": "sha256:42c2e345794229875776ec46ee8390d99fe3d2baccf0b47e199341dc66f71420",
            "url": "https://github.com/pretty-good-software-org/skillctl/releases/download/v2.1.0/skillctl_2.1.0_linux_amd64.tar.gz",
            "url_api": "https://api.github.com/repos/pretty-good-software-org/skillctl/releases/assets/491538663",
        },
        "platforms.macos-arm64": {
            "checksum": "sha256:44cf3ab753d747fd3f658644a6e1742b89105104a4fa925db6aa8617e10dc0c5",
            "url": "https://github.com/pretty-good-software-org/skillctl/releases/download/v2.1.0/skillctl_2.1.0_darwin_arm64.tar.gz",
            "url_api": "https://api.github.com/repos/pretty-good-software-org/skillctl/releases/assets/491538631",
        },
        "platforms.macos-x64": {
            "checksum": "sha256:b173fc3dbabc0d4bd793cb1f91ce2b05b6d1fb28caf8af65c5f08532fb1f882c",
            "url": "https://github.com/pretty-good-software-org/skillctl/releases/download/v2.1.0/skillctl_2.1.0_darwin_amd64.tar.gz",
            "url_api": "https://api.github.com/repos/pretty-good-software-org/skillctl/releases/assets/491538661",
        },
    }
    for platform in expected_lock:
        if platform.startswith("platforms."):
            expected_lock[platform]["provenance"] = "github-attestations"
    lock = tomllib.loads((REPO_ROOT / "mise.development.lock").read_text())
    actual = lock["tools"][tool_name]
    assert actual[0]["version"] == "2.1.0" and actual[0]["backend"] == tool_name, (
        "the development lock must pin exactly one skillctl release"
    )
    for platform in expected_lock:
        if platform.startswith("platforms."):
            assert actual[0][platform] == expected_lock[platform], (
                f"skillctl lock entry missing {platform}"
            )


def test_template_locks_apm_0260_for_all_platforms_without_attestations() -> None:
    tool_name = "github:microsoft/apm"
    expected_platforms = {
        "linux-arm64": (
            "sha256:c4d6b5ab6d9bdca3c3c324db7ce8d1c4faf7b317f45a55a50ae2571eaa506d25",
            "https://github.com/microsoft/apm/releases/download/v0.26.0/apm-linux-arm64.tar.gz",
            "https://api.github.com/repos/microsoft/apm/releases/assets/481831784",
        ),
        "linux-arm64-musl": (
            "sha256:c4d6b5ab6d9bdca3c3c324db7ce8d1c4faf7b317f45a55a50ae2571eaa506d25",
            "https://github.com/microsoft/apm/releases/download/v0.26.0/apm-linux-arm64.tar.gz",
            "https://api.github.com/repos/microsoft/apm/releases/assets/481831784",
        ),
        "linux-x64": (
            "sha256:3afba455c5283852ba4c392f668be7c27b65bc4a0fa60a8b53a4626c52628431",
            "https://github.com/microsoft/apm/releases/download/v0.26.0/apm-linux-x86_64.tar.gz",
            "https://api.github.com/repos/microsoft/apm/releases/assets/481831780",
        ),
        "linux-x64-musl": (
            "sha256:3afba455c5283852ba4c392f668be7c27b65bc4a0fa60a8b53a4626c52628431",
            "https://github.com/microsoft/apm/releases/download/v0.26.0/apm-linux-x86_64.tar.gz",
            "https://api.github.com/repos/microsoft/apm/releases/assets/481831780",
        ),
        "macos-arm64": (
            "sha256:febddd0a8beb4be7b411e708ed746937a14482d5e0935eb776b7f35e320654df",
            "https://github.com/microsoft/apm/releases/download/v0.26.0/apm-darwin-arm64.tar.gz",
            "https://api.github.com/repos/microsoft/apm/releases/assets/481831785",
        ),
        "macos-x64": (
            "sha256:6cc47251bbefabe36224bcc5370c1ef08405d4fd15900b42e11ba672ae29483f",
            "https://github.com/microsoft/apm/releases/download/v0.26.0/apm-darwin-x86_64.tar.gz",
            "https://api.github.com/repos/microsoft/apm/releases/assets/481831787",
        ),
    }
    lock = tomllib.loads((REPO_ROOT / "mise.lock").read_text())
    entries = lock["tools"][tool_name]
    assert len(entries) == 1, "APM must have exactly one locked release entry"
    entry = entries[0]
    assert entry["version"] == "0.26.0"
    assert entry["backend"] == tool_name
    actual_platforms = {
        key.removeprefix("platforms.") for key in entry if key.startswith("platforms.")
    }
    assert actual_platforms == set(expected_platforms)
    assert "provenance" not in entry, "APM uses the documented checksum-only exception"
    for platform, (checksum, url, url_api) in expected_platforms.items():
        actual = entry[f"platforms.{platform}"]
        assert actual == {"checksum": checksum, "url": url, "url_api": url_api}, (
            f"APM lock entry for {platform} must match the published artifact exactly"
        )


def test_template_declares_minimal_apm_metadata_matching_plugin_identity() -> None:
    apm_lines = [
        line
        for line in (REPO_ROOT / "apm.yml").read_text().splitlines()
        if line and not line.startswith("#")
    ]
    manifest = {}
    description_lines: list[str] = []
    for line in apm_lines:
        if line == "description: >-":
            manifest["description"] = ""
            continue
        if line.startswith("  ") and "description" in manifest:
            description_lines.append(line.strip())
            continue
        if line == "author:":
            break
        key, value = line.split(": ", 1)
        manifest[key] = json.loads(value) if value.startswith('"') else value
    manifest["description"] = " ".join(description_lines)
    plugin = json.loads((REPO_ROOT / ".claude-plugin/plugin.json").read_text())
    assert list(manifest) == ["name", "version", "description"]
    assert manifest["name"] == plugin["name"]
    assert manifest["version"] == plugin["version"]
    assert manifest["description"] == plugin["description"]
    apm_text = (REPO_ROOT / "apm.yml").read_text()
    assert "author:\n  name: pretty-good-software-org" in apm_text
    assert "target: claude" in apm_text
    assert "includes" not in manifest and "dependencies" not in manifest


def test_manifest_contract_allows_ordered_marketplace_dependencies() -> None:
    manifest = {
        "name": "example",
        "version": "1.0.0",
        "description": "Example",
        "author": {"name": "example"},
        "dependencies": [
            {"name": "base-plugin", "marketplace": "core"},
            {"name": "follow-up-plugin", "marketplace": "extras"},
        ],
    }
    assert_plugin_manifest_contract(manifest)


def test_template_plugin_and_nested_skill_publish_one_identity() -> None:
    manifest = json.loads((REPO_ROOT / ".claude-plugin/plugin.json").read_text())
    skill_path = REPO_ROOT / "skills" / manifest["name"] / "SKILL.md"
    skill_text = skill_path.read_text()
    assert_plugin_manifest_contract(manifest)
    assert manifest["name"] == "template-agent-skill", "template plugin identity must remain stable"
    assert f"name: {manifest['name']}" in skill_text, "nested SKILL.md must expose plugin identity"
    assert f'description: "{manifest["description"]}"' in skill_text, (
        "nested description must mirror plugin.json"
    )
    assert skill_path.is_file(), "the authoritative skill must be nested under its plugin directory"
    assert not (REPO_ROOT / "SKILL.md").exists(), (
        "template must not retain a root compatibility skill"
    )
