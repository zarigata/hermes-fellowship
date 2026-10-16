# Hermes Fellowship

**GANDALF runs the mission. Claude Code runs the engineering team.**

A practical starter for an entrepreneur and vibe coder: Hermes handles daily assistance, product judgment and task routing; Claude Code handles implementation through eight named specialists. Supports Qwen3.8 through Ollama, loaded LM Studio models, local GLM-compatible deployments, Z.AI GLM and custom Anthropic-compatible endpoints. This is configuration and orchestration code, not a trained model or a promise of autonomous production reliability.

## Install by asking Hermes

Copy this into Hermes (choose the GitHub account you can access):

> Install Hermes Fellowship from https://github.com/zarigata/hermes-fellowship. Read INSTALL.md, use the selectable setup, configure my project for Claude Code, and let me choose the model server and plugin pack. Preserve existing files and credentials. Do not deploy anything.

Mirror: https://github.com/Dagoth-Ur-69/hermes-fellowship

Or install the native Hermes coordinator distribution:

```sh
hermes profile install github.com/zarigata/hermes-fellowship --alias
hermes -p fellowship-gandalf setup
hermes -p fellowship-gandalf chat
```

The distribution installs files; setup then installs the chosen Claude plugins. Git must be authenticated for these private repositories. A bare pasted URL does not execute code. The wizard offers an explicit `url-install` preference for future links to this exact kit; the Hermes coordinator interprets it. This is a prompt-level preference, not a global URL interceptor.

For a local checkout:

```sh
python3 fellowship.py wizard --workspace /absolute/path/to/your/project
```

Requirements: Python 3.10+, Git, Hermes for the coordinator, Claude Code 2.1.257+ and a configured model provider. Linux/macOS/WSL. The installer does not download model weights or install the Claude/Hermes executables. [Complete setup](INSTALL.md).

## The team

| Layer | Character | Responsibility |
|---|---|---|
| Hermes | GANDALF | Central coordinator, budget, decisions, evidence |
| Hermes | SAMWISE | Daily administration, summaries, follow-ups |
| Hermes | DRAGONBORN, SAURON, GIMLI, GALADRIEL, LEGOLAS | Specialist perspectives and routing into Claude Code |
| Claude Code | ELROND | Customer problem, product scope and priorities |
| Claude Code | ARAGORN | Architecture and task decomposition |
| Claude Code | DRAGONBORN | Code implementation and debugging |
| Claude Code | GALADRIEL | Independent correctness review |
| Claude Code | GIMLI | DevOps, CI/CD and infrastructure plans |
| Claude Code | SAURON | Incidents and reliability investigation |
| Claude Code | LEGOLAS | Documentation and technical research |
| Claude Code | BOROMIR | Security and trust-boundary review |

## Choose the workload, not the biggest swarm

| Pack | Installed | Active by default | Intended use |
|---|---:|---:|---|
| `lean` | 10 | 4 | Small context/local model; Ponytail lite, Caveman, memory upkeep, pattern security checks |
| `balanced` | 10 | 6 | Superpowers workflow, review, docs, browser tests |
| `full` | 20 | 6 | Full catalog available on demand, including LSPs and bounded iteration |

Installing 20 plugins does not mean injecting all 20 into every request. Ponytail and Superpowers are alternative workflow leaders. Caveman is a communication style, not a reasoning upgrade. Hosted MCP tools can send data outside your machine even with a local model. [Catalog and prerequisites](docs/PLUGINS.md).

## Run a task and verify it

```sh
python3 fellowship.py doctor --workspace /absolute/project
python3 fellowship.py run --workspace /absolute/project \
  --task-file /absolute/task.json --gates /absolute/quality-gates.json
```

Use `examples/code-review.json` as a brief template. Define project-specific test commands using `examples/quality-gates.json`. A model result without passing supplied gates is **completed_unverified**, returns a nonzero exit, and must not be called done. Plan-only runs can return success without gates, explicitly labeled unverified. Receipts, logs and recovery checkpoints stay under the project's private `.fellowship/` directory.

## Reliability and maintenance

Client context is capped to the selected preset; Ollama's reported running context can reduce it automatically. Actual model/server capacity remains a hard limit. Native Claude compaction stays enabled. Compact checkpoints, bounded brief size, one writer and limited agent concurrency reduce context pressure; they do not make a small model equal a stronger one. See [model presets](docs/MODELS.md) and [execution contract](docs/ORCHESTRATION.md).

CI runs the test suite on changes and weekly. Weekly source audits compare the pinned plugin commits to upstream without executing new plugin code. Dependabot proposes GitHub Actions updates. Upgrade plugins by reviewing lock changes, installing in a disposable project, running your smoke suite, then promoting the tested commit. No unattended production changes.

[Research and source links](docs/RESEARCH.md) · [Workflows](docs/WORKFLOWS.md) · [Validation limits](TEST_REPORT.md)
