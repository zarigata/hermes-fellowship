# Research decisions — checked 2026-10-16

“Best” here means a practical fit for this user's workflow, supported by current upstream documentation. This is not a universal ranking or an independent model/plugin benchmark. No star-count ranking is used.

## Recommended stack

- **Hermes:** persistent personal coordinator, daily assistance, memory and skill discovery. [Upstream](https://github.com/NousResearch/hermes-agent), [profiles](https://hermes-agent.nousresearch.com/docs/user-guide/profiles), [profile distributions](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/profile-distributions.md).
- **Claude Code:** the sole coding harness, with actual project subagents, plugins and lifecycle hooks. [Subagents](https://code.claude.com/docs/en/sub-agents), [CLI](https://code.claude.com/docs/en/cli-reference), [hooks](https://code.claude.com/docs/en/hooks).
- **Qwen3.8 through Ollama:** a verified available model family, with `qwen3.8:27b` as a concrete starting preset. [Model listing](https://ollama.com/library/qwen3.8:27b), [Qwen announcement](https://qwen.ai/blog?id=qwen3.8), [Claude integration](https://docs.ollama.com/integrations/claude-code). Hardware suitability and task accuracy must be measured locally.
- **LM Studio:** another documented local Claude Code backend through Anthropic's Messages interface. [Official integration](https://lmstudio.ai/blog/claudecode). An OpenAI-only endpoint is insufficient.
- **GLM through Z.AI:** the official guide currently documents GLM-5.3 and GLM-5.3-Flash with the Anthropic-compatible endpoint. [Guide](https://docs.z.ai/devpack/tool/claude). Local GLM requires an actually available model/server; cloud model names are not proof that consumer hardware can serve them.

## Reliability choices derived from those sources

The [environment variable reference](https://code.claude.com/docs/en/env-vars) documents custom context limits, alias mapping, forced subagent model routing, output/retry budgets and concurrency controls. The kit requires Claude Code2.1.257+ for its routing behavior. It leaves native compaction enabled and caps context honestly instead of pretending a small model has unlimited memory. Ollama's [running-model endpoint](https://docs.ollama.com/api/ps) exposes actual loaded context, allowing downward adjustment.

The official [plugin marketplace guide](https://code.claude.com/docs/en/plugin-marketplaces) and [marketplace reference](https://code.claude.com/docs/en/plugin-marketplaces-reference) support a private curated catalog, git subdirectories and SHA pins. The local project installer invokes Claude's own validator before network installation. The catalog pins first-party and community sources; it does not vendor upstream code or audit every transitive package.

[Superpowers](https://github.com/obra/superpowers) supplies an established structured coding workflow. [Ponytail](https://github.com/DietrichGebert/ponytail) supplies another, with lite mode suited to the small default budget. [Caveman](https://github.com/JuliusBrussee/caveman) compresses communication; its advertised token savings are upstream claims, not measured results in this project. We install the Claude plugin, not Caveman's broader router/cloud CLI. Activating overlapping workflows can consume context and conflict, so only one leads each preset.

[Anthropic's official catalog](https://github.com/anthropics/claude-plugins-official) provides review, engineering, security, LSP and external integration entries used here. Inclusion does not mean every listed third-party tool is Anthropic-developed. See the exact 20 selections and requirements in [PLUGINS.md](PLUGINS.md).

## Alternatives and trade-offs

Hermes alone can code, but the requested architecture puts engineering in Claude Code. More agents and plugins can worsen latency, context pressure and coordination. A single small task should often use only one worker. Independent review is useful when it brings fresh evidence; matching role names do not improve model capability by themselves.

For DevOps, correctness depends on scoped credentials, real environment knowledge, testable plans, observability and rollback. Prompt-defined roles cannot enforce production isolation. For everyday usage, add only the mail/calendar/document integrations actually needed, with explicit authorization for sending and publishing.

## What research does not prove

The source review establishes documented compatibility and available components. It does not establish benchmark leadership, live tool-calling quality on the user's quantization/hardware, installation success for every plugin or safe production autonomy. The test report clearly distinguishes mocked launcher checks from live model and plugin checks. Model preset dates and source pins should be revisited through reviewed updates.
