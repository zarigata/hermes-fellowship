# Provider presets and context budgets

Research checked 2026-10-16. Presets are starting configurations, not benchmark winners.

| Preset | Provider/model | Client context | Output | Parallel subagents |
|---|---|---:|---:|---:|
| ollama-qwen-lean | Ollama qwen3.8:27b | 32,768 | 4,096 | 1 |
| ollama-qwen-balanced | Ollama qwen3.8:27b | 65,536 | 8,192 | 1 |
| lmstudio-local | Exact loaded model ID required | 32,768 | 4,096 | 1 |
| glm-local | Exact locally served GLM model ID required | 32,768 | 4,096 | 1 |
| zai-glm | Z.AI glm-5.3 | 131,072 | 8,192 | 2 |
| zai-glm-fast | Z.AI glm-5.3-flash | 65,536 | 4,096 | 1 |
| custom-anthropic | Exact endpoint and model ID required | 32,768 | 4,096 | 1 |

Qwen3.8:27b is an actual Ollama listing. It may be too large for your hardware; choose a supported smaller/quantized model after checking RAM/VRAM, KV-cache cost, speed and tool-call accuracy. The project does not infer hardware capacity or download weights. `glm-local` does not imply cloud GLM-5.3 fits on a consumer GPU. Select a model you can actually load.

Ollama and LM Studio expose Anthropic-compatible APIs for Claude Code. An OpenAI-compatible `/v1/chat/completions` endpoint alone is insufficient. LM Studio's documented integration requires 0.4.1+. Use its exact model ID from `/v1/models`; display names and download filenames may differ. Ollama's `doctor` uses `/api/tags`. Remote endpoints require HTTPS; insecure LAN HTTP is rejected.

Ollama recommends 64k+ context for coding; the 32k lean pack is a deliberate constrained fallback for smaller tasks. LM Studio recommends at least 25k. Raising client context does not raise server context or create GPU memory. Configure the server first. The wrapper reduces context automatically when a loaded Ollama model reports a smaller capacity; other servers use your declared cap. It refuses a measured capacity below16k.

`CLAUDE_CODE_MAX_CONTEXT_TOKENS` is the documented setting for unknown/custom model names. The wrapper maps Haiku/Sonnet/Opus aliases and forcibly maps subagents to the selected model. It caps output, file reads, retries, concurrency and nesting. It does not use a fabricated compaction percentage flag. `CLAUDE_CODE_AUTO_COMPACT_WINDOW` has a documented minimum100k, so it is not used to pretend a32k model has a32k native override. Actual client context plus native compaction and small briefs manage the budget.

No preset has been benchmarked on your hardware. Before relying on one, run: (1) read-only repository summary, (2) a small bug fix with a failing-then-passing test, (3) independent review of an intentionally seeded defect, (4) a mocked DevOps plan with no production credentials. Record latency, tool-call failures, correctness and token use. Keep the model/version/quantization stable during comparison. Increase context or switch models only when evidence warrants it; there is no automatic paid fallback.

See [Ollama](https://docs.ollama.com/integrations/claude-code), [Qwen3.8](https://ollama.com/library/qwen3.8:27b), [LM Studio](https://lmstudio.ai/blog/claudecode), [Z.AI](https://docs.z.ai/devpack/tool/claude), [Claude environment variables](https://code.claude.com/docs/en/env-vars).
