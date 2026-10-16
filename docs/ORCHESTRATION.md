# Execution and recovery contract

Hermes GANDALF is the user-facing coordinator. It owns daily work, product priorities, budget, authorization and final acceptance. Hermes role cards are planning perspectives. Claude Code is the engineering execution harness; the real project subagent definitions live in `claude/agents/` and are copied into the target `.claude/agents/`.

1. GANDALF writes a compact JSON brief: goal, context, acceptance criteria, authorized actions. That file describes the request; it cannot grant permissions the user did not give.
2. GANDALF invokes `fellowship.py run --workspace ... --task-file ... --gates ...`. The gates must be explicit, reviewed argv arrays. Commands run with the user's OS privileges; inspect them before using an unfamiliar project.
3. The launcher verifies the Claude version, locks one writer for the workspace, selects a provider and caps context/concurrency. All model aliases and subagents map to the chosen model. There is no remote fallback list. Managed policies still take precedence.
4. The launcher passes the literal brief through stdin, attaches the coordinator contract and starts a bounded Claude Code session. Claude selects internal specialists as needed. Independent review uses a fresh subagent. No requirement to spawn every role.
5. Stream events and stderr are saved privately. A zero process exit alone is insufficient: require a terminal `result` with `subtype: success`, `is_error: false` and no reported permission denials. Missing, failed, timed-out or interrupted results fail closed.
6. After a successful implementation session, deterministic gates execute from the original in-memory gate configuration, with timeouts. Any failure returns nonzero. No gates means completed_unverified, never verified. Plan-only skips gates and is explicitly unverified.
7. GANDALF reads the receipt, diff and evidence. Passing gates covers only what those tests assert. Customer acceptance, staging checks and production behavior remain separate.

## Small context and recovery

The provider preset sets the client context and output budgets. For a loaded Ollama model, `/api/ps` can lower the client cap to the server's actual reported context. If context cannot be measured, the selected cap is an assumption that must match the server configuration. Below 16k this starter refuses execution. It never expands server memory or silently switches providers.

Native Claude compaction remains enabled. Before compaction, a deterministic hook snapshots Git HEAD, status and diff statistics; after compaction it saves the native summary locally. SessionStart points Claude to the private checkpoint. The wrapper also writes start/end checkpoints with task and receipt paths. This preserves useful recovery anchors, not every prior thought. Task prompts and repository files remain authoritative; summaries are fallible. Do not inject entire transcripts into a new context.

On failure, inspect the checkpoint, logs and actual workspace before retrying. GANDALF may run at most two correction attempts after identifying new evidence and a concrete change. This is a coordinator instruction, not an automatic retry daemon. Process timeouts terminate the local process group but cannot revoke remote jobs or guarantee cleanup of detached processes. Never replay deployments blindly.

## Boundaries

Role cards, cooperative locks and `authorized_actions` are not OS sandboxes. Concurrent directly started Claude sessions can bypass the wrapper's lock. Default permission prompts remain enabled; headless tasks may block until timeout or return permission denials. Resolve the concrete missing permission interactively; never disable approvals as a workaround. Production changes need the user's authorization and a tested rollback plan.

## Optional Hermes-only work

`council.py` remains available for daily and specialist-planning profiles. It uses documented `hermes -p NAME chat --oneshot --query-file - --format stream-json`. Native `delegate_task` does not magically load named profile SOUL files or per-task models: supply the relevant role card and brief. Use it for independent research/planning only; the implementation route stays `fellowship.py` -> Claude Code.
