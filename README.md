# kiss-skill

An [Agent Skill](https://agentskills.io/specification), `kiss`, that closes a decision with several valid options. The
agent picks the smallest option that meets the actual requirement, writes the decision into the decision doc or
ticket, and parks every non-essential refinement as an explicit "to refine later" item.

| Step              | Result                                                                |
| ----------------- | --------------------------------------------------------------------- |
| State requirement | One sentence on what the decision must achieve now                    |
| List options      | Each valid option with what it adds                                   |
| Pick smallest     | The option with the fewest new parts that fully meets the requirement |
| Write it down     | A dated decision block in the doc, ticket, or thread that owns it     |
| Park the rest     | "To refine later" items, each with a revisit trigger                  |

## Requirements

None beyond an agent that loads Agent Skills.

## Installation

With [APM](https://github.com/microsoft/apm), pinned to a release:

```bash
apm install pretty-good-software-org/kiss-skill#v1.0.0
```

Without APM, copy the skill directory into your agent's skills directory, for example for Claude Code:

```bash
git clone --depth 1 --branch v1.0.0 https://github.com/pretty-good-software-org/kiss-skill.git
cp -R kiss-skill/skills/kiss ~/.claude/skills/
```

## Usage

Ask the agent to apply KISS to an open decision, for example "KISS this decision" or "pick the simplest option and
park the rest". The skill's [`SKILL.md`](skills/kiss/SKILL.md) holds the steps and the decision block.

## Development

Development uses [mise](https://mise.jdx.dev/), which installs the pinned tools from the lock files:

```bash
mise run setup:default
mise run lint:default
mise run test:default
MISE_ENV=development mise run lint:development
```

`setup:default` also installs the Git hooks. `lint:development` adds the private `skillctl` validation. Changes are
recorded with [Changie](https://changie.dev/) in `.changes/` and merged into [`CHANGELOG.md`](CHANGELOG.md).

## License

[MIT](LICENSE)
