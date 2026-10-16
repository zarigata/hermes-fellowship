# Tool strategy

Claude Code is the sole coding harness. Hermes remains the coordinator and daily assistant. The 20-plugin catalog is documented in [PLUGINS.md](PLUGINS.md); source commits are pinned in `.claude-plugin/marketplace.json`.

For DevOps, use the tools the project actually needs: GitHub Actions, Docker, Ansible, OpenTofu/Terraform, Trivy, Kubernetes and observability APIs. These are external prerequisites, not installed or authenticated by this kit. Start read-only, use scoped credentials and test a plan before apply. HolmesGPT can be evaluated separately for incident investigation; it is not another coding execution layer.

For daily usage, Hermes-native web/research, filesystem and productivity integrations are appropriate. Configure Google Workspace, mail or calendar only when you need them. More installed tools do not guarantee better decisions; keep enabled capabilities narrow enough for the chosen model and context budget.
