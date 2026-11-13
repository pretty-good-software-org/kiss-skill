---
last_validated: 2026-09-05T10:04:03Z
project_type: agent-skill-template
---

# Agent Instructions: template-agent-skill

## Repository Overview

`template-agent-skill` is the canonical organization template for repositories that publish one standalone Agent Skill
as a Claude plugin. It derives from `template-python` and adds skill metadata validation, `orgctl` initialization,
tests, and CI while using native vendor lint configuration.

## Ownership

- `.claude-plugin/plugin.json` and `skills/<plugin-name>/SKILL.md` expose one plugin identity. `apm.yml` is the
  source of the manifest: `apm pack --force` generates `.claude-plugin/plugin.json`, and `mise run test:plugin-manifest`
  fails when the committed manifest drifts from that output.
- `template.init.toml` owns identity replacement and nested skill-directory rename in derived repositories.
- The released `github:pretty-good-software-org/skillctl` binary owns Claude plugin manifest validation, including exact
  optional marketplace dependency validation. The template does not copy a validator into `tools/`. This is distinct
  from `platform-skill-create/scripts/validate_skill.py`, which is separate product runtime behavior owned by a
  different repository, not this template.
- `tools/smoke_template.py`, `tests/test_smoke_template.py`, and `mise-tasks/test/template-smoke` own the released
  `orgctl repo init` smoke test and are template-only: `template.init.toml`'s top-level `remove` list deletes all three
  during initialization, so no derived repository retains them.
- `tools/smoke_template.py`'s `assert_skillctl_rejects_plugin_name_drift` mutates the derived repository's
  `.claude-plugin/plugin.json` to a literal mismatched name, runs the real skill lint task (`mise run lint:skill`,
  which runs `skillctl validate claude-plugin .` from the development profile) expecting a nonzero exit and the literal
  name-drift diagnostic, and restores the manifest's exact original bytes in a `finally` block before
  the rest of `verify_derived_repository` runs. `tests/test_smoke_template.py` regression-tests this helper's
  pass, wrong-verdict,
  and wrong-diagnostic paths against an injected `run_lint_skill` callable, without the cost of a real
  `orgctl`/`mise`/`skillctl` invocation.
- Mise pins runtimes and command-line tools in the base profile, while development-only tools include `skillctl` v2.1.0
  so local validation can run without exposing private credentials in CI; the development profile pins `orgctl`
  v0.12.2, which runs `orgctl repo init` with the `remove` manifest mechanism in the explicit template smoke test and
  provides `orgctl merge --expected-head`. Its releases carry no GitHub artifact attestations, so the locked checksums
  are its provenance control.
- `UV_NO_MANAGED_PYTHON=1` forces uv to use Mise's Python rather than a separately managed interpreter.
- `pyproject.toml` and `uv.lock` own Python dependencies. Every `uv run` in the Mise tasks and Lefthook hooks passes
  `--locked`, so a `uv.lock` that no longer matches `pyproject.toml` fails them instead of being re-locked silently;
  run `uv lock` after editing dependencies. Dependabot uses the `uv` ecosystem so its updates refresh `uv.lock`.
- `pyproject.toml` carries the inline `[tool.ruff]` configuration and the Agent Skill template source roots.
- `.yamllint.yml` owns this template's Yamllint settings, uses no runtime policy downloads, and excludes generated
  `apm.lock.yaml` and `apm_modules/` content so dependency resolution cannot make repository lint inspect generated or
  third-party YAML.
- Ruff owns Python linting and formatting; rumdl owns Markdown formatting and linting. CI uses only the public/base
  toolchain; private skill validation is installed in the development profile for local use.

## Repository Structure

```text
.
├── .actionlint.yml
├── .changes
│   ├── header.tpl.md
│   ├── unreleased
│   │   └── .gitkeep
│   ├── v2.0.0.md
│   ├── v2.0.1.md
│   └── v2.1.0.md
├── .changie.yaml
├── .claude-plugin
│   └── plugin.json
├── .coderabbit.yaml
├── .github
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── dependabot.yml
│   └── workflows
│       ├── lint.yml
│       └── test.yml
├── .gitignore
├── .mise.ci.toml
├── .mise.development.toml
├── .mise.toml
├── .miserc.toml
├── .rumdl.toml
├── .yamllint.yml
├── AGENTS.md
├── CLAUDE.md
├── LICENSE
├── README.md
├── apm.yml
├── cog.toml
├── lefthook
│   ├── commit-msg.yml
│   ├── files.yml
│   ├── lint.yml
│   ├── python.yml
│   └── secrets.yml
├── lefthook.yml
├── mise-tasks
│   ├── check
│   │   └── markdown-format
│   ├── format
│   │   └── markdown
│   ├── lint
│   │   ├── actionlint
│   │   ├── default
│   │   ├── development
│   │   ├── python
│   │   ├── rumdl
│   │   ├── skill
│   │   └── yamllint
│   ├── setup
│   │   └── default
│   └── test
│       ├── default
│       ├── plugin-manifest
│       ├── python-runtime
│       └── template-smoke
├── mise.development.lock
├── mise.lock
├── pyproject.toml
├── skills
│   └── template-agent-skill
│       └── SKILL.md
├── template.init.toml
├── tests
│   ├── test_smoke_template.py
│   └── test_template_contract.py
├── tools
│   └── smoke_template.py
└── uv.lock
```

## Commands

```bash
mise run setup:default
mise run format:markdown
mise run lint:default
mise run test:default
mise run lint:development
MISE_ENV=development mise run test:template-smoke
```

`lint:development` runs `lint:default` plus `lint:skill`, the private `skillctl` validation. Use the fastest loop that
exercises the changed layer: a focused pytest test first, then skill validation, then complete lint and test tasks. Run
the explicit smoke task for changes to `template.init.toml`; it copies the repository to a temporary directory, sets a
derived origin URL, and runs the released `orgctl repo init` command. The smoke task selects `MISE_ENV=development`
explicitly. The default test task must remain runnable after initialization and in CI without cross-repository
credentials.

## Template Contract

- Keep exactly one authoritative `skills/<plugin-name>/SKILL.md`; never retain a root `SKILL.md` compatibility alias.
- Keep plugin name and frontmatter name identical.
- Keep plugin and skill descriptions byte-for-byte identical.
- Keep `plugin.json` limited to `name`, `version`, `description`, and the vendor-required `author` metadata.
- Keep Python dependencies exact and refresh `uv.lock` after changes.
- Keep template smoke logic repository-only under `tools/`; generated plugins start without placeholder runtime
  resources or non-standard archive packaging. The released `skillctl` binary validates optional marketplace
  dependencies directly; no copied validator belongs in the template.
- Keep `tools/smoke_template.py`, `tests/test_smoke_template.py`, and `mise-tasks/test/template-smoke` listed in
  `template.init.toml`'s `remove` list; derived repositories must not retain any of the three paths.
- Do not add behavior-specific instructions to this generic template.
- Do not edit derived repositories from this template; improvements flow into this canonical source first.

## Development Guidelines

Change generic repository behavior in the highest applicable canonical template before propagating it here. Keep Mise
tasks as thin entry points over locked ecosystem tooling, and use focused tests before aggregate checks. Local setup
requires authenticated GitHub CLI access for organization repository initialization.

## Testing

Test external-input boundaries and logic, not static mappings guaranteed by structure. Every regression test must fail
when its protected behavior is broken. `skillctl`'s own test suite covers structural validation (empty values, naming
mismatches, escaping links, metadata drift, symbolic links) upstream; this repository no longer duplicates that
coverage. Template contract tests reject packaging and distributed repository tooling,
assert the copied repository validator stays deleted, and assert `template.init.toml`'s `remove` list names exactly the
template-only smoke fixture. The runtime ownership test verifies that uv resolves the Python executable pinned by Mise.
APM metadata remains minimal and the smoke test proves auto-detected nested-skill installation and audit.

## Git Workflow

Check status first, work on feature branches, use Conventional Commits, and create a pull request. Before opening one,
run `mise run lint:default` and `mise run test:default`. Merge only after trusted CI proves the checked-in native lint
configuration and skill tooling. Repository settings and template status are managed in
`pretty-good-software-org/org-github-infrastructure`; do not change them manually in the GitHub UI.
