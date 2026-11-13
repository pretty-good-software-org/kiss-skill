---
last_validated: 2026-11-12T19:30:00+01:00
project_type: agent-skill
---

# Agent Instructions: kiss-skill

## Repository Overview

`kiss-skill` publishes the `kiss` Agent Skill as a Claude plugin. The skill closes a decision with several valid
options: it picks the smallest option that meets the actual requirement, writes the decision into the decision doc or
ticket, and parks every non-essential refinement as an explicit "to refine later" item. The repository is public under
the MIT license and derives from `template-agent-skill`.

## Ownership

- `apm.yml` is the source of the plugin manifest: `apm pack --force` generates `.claude-plugin/plugin.json`, and
  `mise run test:plugin-manifest` fails when the committed manifest drifts from that output.
- `skills/kiss/SKILL.md` is the authoritative skill. The plugin name, skill directory, and frontmatter name are `kiss`;
  the repository name `kiss-skill` differs on purpose and is not part of the plugin identity. The skill description
  matches `apm.yml` and `plugin.json` byte for byte.
- The released `github:pretty-good-software-org/skillctl` binary, pinned in the development profile, validates the
  plugin manifest and the skill metadata through `mise run lint:skill`.
- `.mise.toml` and `mise.lock` pin the tools CI uses; the development profile adds `skillctl`, `orgctl`, and the Git
  hook tools.
- `pyproject.toml` and `uv.lock` own Python dependencies. Every `uv run` in the Mise tasks and Lefthook hooks passes
  `--locked`; run `uv lock` after editing dependencies. `UV_NO_MANAGED_PYTHON=1` forces uv onto Mise's Python.
- Changie owns `CHANGELOG.md`: add entries under `.changes/unreleased/`, batch them into `.changes/<version>.md`, and
  merge.
- Repository settings are managed in `pretty-good-software-org/org-github-infrastructure`; do not change them in the
  GitHub UI.

## Repository Structure

```text
.
├── .actionlint.yml
├── .changes
│   ├── header.tpl.md
│   └── unreleased
│       └── .gitkeep
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
├── CHANGELOG.md
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
│       └── python-runtime
├── mise.development.lock
├── mise.lock
├── pyproject.toml
├── skills
│   └── kiss
│       └── SKILL.md
├── tests
│   └── test_template_contract.py
└── uv.lock
```

## Commands

```bash
mise run setup:default
mise run format:markdown
mise run lint:default
mise run test:default
MISE_ENV=development mise run lint:development
```

`lint:development` runs `lint:default` plus `lint:skill`, the private `skillctl` validation. Use the fastest loop that
exercises the change: a focused pytest test first, then the complete lint and test tasks.

## Development Guidelines

This repository is public. Keep product names, customer data, hostnames, session links, and local paths out of files and
commit messages; examples use neutral text. Generic repository behavior comes from `template-agent-skill`; change it
there first.

## Testing

The contract tests pin the plugin name to `kiss` and keep the manifest, the skill identity, locked `uv run` calls, and
Dependabot settings consistent. The skill itself is instructions for an agent; verify a behavior change by running an
agent with the installed skill and record what you ran in the pull request.

## Git Workflow

Check status first, work on feature branches, use Conventional Commits, and open a pull request; run
`mise run lint:default` and `mise run test:default` before opening it. To release, bump `version` in `apm.yml`, run
`apm pack --force`, batch the changie entries for that version, and merge to `main` through a pull request. Tag the
merged commit `v<version>` with an annotated tag and publish a GitHub release; consumers pin the tagged commit.
