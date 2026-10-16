# Curated 20-plugin catalog

Selection is based on workflow fit and primary-source documentation, not a claim of universal rank. Source revisions are pinned in `.claude-plugin/marketplace.json`. Claude installs the original upstream code; it is not copied into this repo.

| Plugin | Why / prerequisite | Source |
|---|---|---|
| superpowers | Primary workflow for balanced/full; do not combine as a second planner with Ponytail. | [Pinned upstream](https://github.com/obra/superpowers/tree/bb92a77741419a4ab5f06e711a283343f1ada0c3) |
| feature-dev | On-demand feature planning; overlaps with the main workflow, so keep disabled until needed. | [Pinned upstream](https://github.com/anthropics/claude-plugins-official/tree/ea10b213686c90bb1984b2016937310e05336cf3/plugins/feature-dev) |
| pr-review-toolkit | Focused independent review of implementation, errors and tests. | [Pinned upstream](https://github.com/anthropics/claude-plugins-official/tree/ea10b213686c90bb1984b2016937310e05336cf3/plugins/pr-review-toolkit) |
| code-review | Additional review workflow; use on demand to avoid duplicate reviews. | [Pinned upstream](https://github.com/anthropics/claude-plugins-official/tree/ea10b213686c90bb1984b2016937310e05336cf3/plugins/code-review) |
| claude-md-management | Maintain concise project guidance; review generated guidance diffs. | [Pinned upstream](https://github.com/anthropics/claude-plugins-official/tree/ea10b213686c90bb1984b2016937310e05336cf3/plugins/claude-md-management) |
| hookify | Create workflow hooks; review generated commands before activating them. | [Pinned upstream](https://github.com/anthropics/claude-plugins-official/tree/ea10b213686c90bb1984b2016937310e05336cf3/plugins/hookify) |
| security-guidance | Pattern checks; lean disables additional LLM reviews, with explicit security review/gates instead. | [Pinned upstream](https://github.com/anthropics/claude-plugins-official/tree/ea10b213686c90bb1984b2016937310e05336cf3/plugins/security-guidance) |
| claude-security | On-demand security investigation; scanner results require triage. | [Pinned upstream](https://github.com/anthropics/claude-plugins-official/tree/ea10b213686c90bb1984b2016937310e05336cf3/plugins/claude-security) |
| frontend-design | UI implementation assistance; validate accessibility and actual product flows. | [Pinned upstream](https://github.com/anthropics/claude-plugins-official/tree/ea10b213686c90bb1984b2016937310e05336cf3/plugins/frontend-design) |
| commit-commands | Git workflow shortcuts; review staged changes and destination before publishing. | [Pinned upstream](https://github.com/anthropics/claude-plugins-official/tree/ea10b213686c90bb1984b2016937310e05336cf3/plugins/commit-commands) |
| context7 | Current library docs via an external service; check data policy and access requirements. | [Pinned upstream](https://github.com/anthropics/claude-plugins-official/tree/ea10b213686c90bb1984b2016937310e05336cf3/external_plugins/context7) |
| playwright | Browser automation; Node/browser dependencies and sandbox prerequisites apply. | [Pinned upstream](https://github.com/anthropics/claude-plugins-official/tree/ea10b213686c90bb1984b2016937310e05336cf3/external_plugins/playwright) |
| github | Repository integration; requires GitHub authentication and scoped access. | [Pinned upstream](https://github.com/anthropics/claude-plugins-official/tree/ea10b213686c90bb1984b2016937310e05336cf3/external_plugins/github) |
| serena | Symbol navigation/refactoring; runtime and supported language-server setup required. | [Pinned upstream](https://github.com/anthropics/claude-plugins-official/tree/ea10b213686c90bb1984b2016937310e05336cf3/external_plugins/serena) |
| typescript-lsp | Requires typescript-language-server and TypeScript installed on PATH. | [Pinned upstream](https://github.com/anthropics/claude-plugins-official/tree/ea10b213686c90bb1984b2016937310e05336cf3/plugins/typescript-lsp) |
| pyright-lsp | Requires pyright-langserver installed on PATH. | [Pinned upstream](https://github.com/anthropics/claude-plugins-official/tree/ea10b213686c90bb1984b2016937310e05336cf3/plugins/pyright-lsp) |
| jdtls-lsp | Requires jdtls and compatible Java installation. | [Pinned upstream](https://github.com/anthropics/claude-plugins-official/tree/ea10b213686c90bb1984b2016937310e05336cf3/plugins/jdtls-lsp) |
| ralph-loop | Optional iteration; use a finite explicit budget, never an unattended endless loop. | [Pinned upstream](https://github.com/anthropics/claude-plugins-official/tree/ea10b213686c90bb1984b2016937310e05336cf3/plugins/ralph-loop) |
| ponytail | Lean workflow; PONYTAIL_DEFAULT_MODE=lite. Community plugin, pinned canonical repository. | [Pinned upstream](https://github.com/DietrichGebert/ponytail/tree/6f1c2bfff0c837d268929a7c4e490918eb4fab29) |
| caveman | Concise prose only. Preserve code, precise reasoning and test evidence. Plugin only; no router installation. | [Pinned upstream](https://github.com/JuliusBrussee/caveman/tree/d262ab3882952a59312ff3537cd86d894523c5ab) |

## Installation and activation

`lean` and `balanced` install10 plugins; `full` installs20. Only4 or6 are active by default. `python3 fellowship.py catalog` shows the exact selections. All install/disable commands use local scope for the selected project. The launcher supplies session activation flags for this catalog; unrelated plugins may remain enabled in user/project/managed settings. Inspect the effective configuration before using a local-only workflow.

Example on-demand activation: `claude plugin enable frontend-design@hermes-fellowship --scope local`. To use it through the Fellowship launcher as well, add it to the chosen pack’s `active` list and review the configuration diff; session flags otherwise keep it disabled. Do not activate every review/planning plugin together.

A pin locks the plugin repository revision, not every dependency downloaded by its hooks or MCP commands. External MCPs may require accounts, credentials, network access or paid service plans. Install errors are surfaced; the kit does not silently install system packages. Upgrade pins in reviewed branches and smoke-test before promoting.
