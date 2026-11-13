---
name: template-agent-skill
description: "Template for standalone Agent Skill plugin repositories with validation, locked Python tooling, tests, and CI. Use when: creating or validating the organization template for a dedicated skill repository. Triggers: agent skill template, standalone skill repository, skill plugin template."
license: MIT
---

# Standalone Agent Skill repository template

Use this repository as the canonical starting point for a plugin that contains one Agent Skill. Keep the plugin name and
frontmatter name identical so installation and model discovery expose one stable identity.

## Instantiate the template

Create the repository through `orgctl repo create` with `template-agent-skill`, then run `orgctl repo init` in the
clone. Initialization renames `skills/template-agent-skill/` to `skills/<repository-name>/`, replaces identity strings,
and removes `template.init.toml`.

Before the first commit in the derived repository:

1. Replace this template body with instructions for the target behavior.
2. Replace the generated generic description in both `skills/<repository-name>/SKILL.md` and
   `.claude-plugin/plugin.json` with one exact shared description that states when the skill should trigger.
3. Delete resources and tooling the skill does not need.
4. Add realistic tests for every deterministic script and external-input boundary.
5. Run `mise run lint:default` and `mise run test:default`.

The derived repository is ready only when no template-specific prose remains, validation passes, and tests exercise the
skill's actual boundaries.

## Repository contract

- `.claude-plugin/plugin.json` contains `name`, `version`, `description`, and vendor-required `author` metadata, plus
  optional ordered marketplace `dependencies` objects with exactly `name` and `marketplace` fields. `skillctl` validates
  those objects directly without changing the manifest.
- `skills/<plugin-name>/SKILL.md` contains the same name and description as the plugin manifest.
- Only behavior required by the skill belongs in `references/`, `scripts/`, and `assets/`. Template smoke tooling
  remains in `tools/` outside the plugin runtime boundary.
- `uv.lock` resolves all Python dependencies and Mise pins the Python and uv runtimes.
- The Mise-pinned `skillctl` binary validates optional marketplace dependencies and Agent Skills metadata without
  shipping inside the plugin. It is separate from
  `platform-skill-create/scripts/validate_skill.py`, which is unrelated product runtime behavior owned by a different
  repository.
- CI runs Markdown, YAML, Python, skill validation, and tests.

## Validate

```bash
mise run lint:default
mise run test:default
MISE_ENV=development mise run lint:development
```

Validation checks structure and metadata. Tests protect external-input boundaries. Evaluation of the skill's model
behavior belongs in a separate measured evaluation workflow.
