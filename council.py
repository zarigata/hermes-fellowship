#!/usr/bin/env python3
"""Hermes Fellowship: profile installer and bounded specialist launcher (stdlib)."""
from __future__ import annotations

import argparse
import contextlib
import fcntl
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent


def registry():
    return json.loads((ROOT / "council.json").read_text())


def hermes_root():
    # Hermes may set HERMES_HOME for tools inside an active standard profile.
    base = Path.home() / ".hermes"
    configured = os.environ.get("HERMES_HOME")
    if configured:
        home = Path(configured).expanduser().resolve()
        if home != base.resolve() and home.parent != (base / "profiles").resolve():
            raise ValueError("Custom HERMES_HOME roots are unsupported; use the standard ~/.hermes profile layout.")
    return base


def clean_env():
    env = dict(os.environ)
    env.pop("HERMES_HOME", None)
    return env


def profile_name(agent):
    if agent not in registry()["agents"]:
        raise ValueError(f"Unknown agent: {agent}")
    return "fellowship-" + agent


@contextlib.contextmanager
def lock_profile(base, profile):
    locks = base / "fellowship-locks"
    locks.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (locks / (profile + ".lock")).open("a") as handle:
        os.chmod(handle.name, 0o600)
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError(f"{profile} is busy in another Fellowship launcher. Try after it finishes.") from error
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def install(apply=False):
    base = hermes_root()
    names = list(registry()["agents"])
    targets = [base / "profiles" / profile_name(a) for a in names]
    if not apply:
        print("Preview only. Creates seven fresh profiles; does not copy credentials or start agents.")
        for target in targets:
            print(target)
        return 0
    hermes = shutil.which("hermes")
    if not hermes:
        raise ValueError("Install Hermes from its official documentation first.")
    with lock_profile(base, "installer"):
        existing = [str(p) for p in targets if p.exists() or p.is_symlink()]
        if existing:
            raise ValueError("Refusing to overwrite existing profiles: " + ", ".join(existing))
        for agent, target in zip(names, targets):
            subprocess.run([hermes, "profile", "create", profile_name(agent), "--no-alias",
                            "--description", registry()["agents"][agent]["role"]], check=True, env=clean_env())
            if not target.is_dir() or target.is_symlink():
                raise ValueError(f"Hermes did not create the expected directory: {target}")
            pack = target / "fellowship"
            pack.mkdir(mode=0o700)
            for filename in ("council.py", "council.json", "COMMON.md", "fellowship.py", "INSTALL.md"):
                shutil.copy2(ROOT / filename, pack / filename)
            for dirname in ("agents", "docs", "claude", "presets", ".claude-plugin"):
                shutil.copytree(ROOT / dirname, pack / dirname)
            soul = (ROOT / "COMMON.md").read_text() + "\n\n" + (ROOT / "agents" / f"{agent}.md").read_text()
            soul = soul.replace("{{PACK_ROOT}}", str(pack))
            (target / "SOUL.md").write_text(soul)
            settings = {"terminal.cwd": ".", "agent.max_turns": "60",
                        "delegation.max_concurrent_children": "3",
                        "delegation.max_iterations": "40",
                        "delegation.max_spawn_depth": "1",
                        "delegation.worktree_isolation": "true"}
            for key, value in settings.items():
                subprocess.run([hermes, "-p", profile_name(agent), "config", "set", key, value], check=True, env=clean_env())
            print(f"Installed {agent.upper()}. Configure: hermes -p {profile_name(agent)} setup")
    print("Ready for configuration. No models, accounts, MCP servers, gateways, or schedules were activated.")
    return 0


def load_task(path):
    task = json.loads(Path(path).read_text())
    if not isinstance(task, dict):
        raise ValueError("Task must be a JSON object.")
    allowed = {"goal", "context", "acceptance", "authorized_actions"}
    if set(task) - allowed:
        raise ValueError("Unknown task fields: " + ", ".join(sorted(set(task) - allowed)))
    for field in ("goal", "context"):
        if not isinstance(task.get(field), str) or not task[field].strip():
            raise ValueError(f"Task requires a nonempty {field} string.")
    for field in ("acceptance", "authorized_actions"):
        if not isinstance(task.get(field), list) or not task[field] or not all(isinstance(x, str) and x.strip() for x in task[field]):
            raise ValueError(f"Task requires a nonempty {field} list of strings.")
    return task


def build_command(hermes, agent, turns):
    if not 1 <= turns <= 200:
        raise ValueError("max-turns must be between 1 and 200.")
    return [hermes, "-p", profile_name(agent), "chat", "--oneshot", "--query-file", "-",
            "--format", "stream-json", "--max-turns", str(turns)]


def final_result(path):
    result = None
    with Path(path).open(errors="replace") as stream:
        for line in stream:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict) and event.get("type") == "result":
                result = event
    return result


def stop_group(proc):
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        pass
    # Kill surviving descendants even if their original parent already exited.
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    proc.wait()


def run_agent(agent, workspace, task_file, seconds=1800, turns=60):
    if agent == "gandalf":
        raise ValueError("Start the coordinator interactively: hermes -p fellowship-gandalf chat")
    if os.environ.get("FELLOWSHIP_WORKER"):
        raise ValueError("Nested profile launches are disabled. Return the handoff to GANDALF.")
    if not 1 <= seconds <= 14400:
        raise ValueError("timeout must be between 1 and 14400 seconds.")
    base = hermes_root()
    profile = profile_name(agent)
    workspace = Path(workspace).expanduser().resolve(strict=True)
    if not workspace.is_dir():
        raise ValueError("Workspace must be a directory.")
    task = load_task(task_file)
    hermes = shutil.which("hermes")
    if not hermes:
        raise ValueError("Hermes executable is missing.")
    target = base / "profiles" / profile
    if not (target / "fellowship" / "council.json").is_file():
        raise ValueError(f"Fellowship profile not installed: {profile}")
    cmd = build_command(hermes, agent, turns)
    role_text = (ROOT / "COMMON.md").read_text() + "\n" + (ROOT / "agents" / f"{agent}.md").read_text()
    role_text = role_text.replace("{{PACK_ROOT}}", str(target / "fellowship"))
    prompt = (role_text + "\n\nAssigned task (authorization remains subject to the user's actual request):\n"
              + json.dumps(task, ensure_ascii=False, indent=2)
              + f"\nWorkspace: {workspace}\nVerify terminal cwd before any edit. "
              + "Do not launch another profile. Return the evidence contract from COMMON.md.")
    with lock_profile(base, profile):
        runs = base / "fellowship-runs"
        runs.mkdir(parents=True, exist_ok=True, mode=0o700)
        run_dir = Path(tempfile.mkdtemp(prefix=agent + "-", dir=runs))
        started = time.time()
        env = dict(clean_env(), FELLOWSHIP_WORKER=agent)
        state = "unknown"
        returncode = None
        with (run_dir / "events.jsonl").open("w") as out, (run_dir / "stderr.log").open("w") as err:
            os.chmod(out.name, 0o600)
            os.chmod(err.name, 0o600)
            proc = subprocess.Popen(cmd, cwd=workspace, env=env, stdin=subprocess.PIPE,
                                    stdout=out, stderr=err, text=True, start_new_session=True)
            try:
                proc.communicate(prompt, timeout=seconds)
                returncode = proc.returncode
                state = "process_finished"
            except subprocess.TimeoutExpired:
                stop_group(proc)
                state = "timeout_unknown_effects"
            except KeyboardInterrupt:
                stop_group(proc)
                state = "interrupted_unknown_effects"
        result = final_result(run_dir / "events.jsonl")
        ok = state == "process_finished" and returncode == 0 and result is not None and result.get("exit_code") == 0
        receipt = {"agent": agent, "profile": profile, "workspace": str(workspace),
                   "started_at": started, "duration_seconds": round(time.time() - started, 2),
                   "status": "completed_unreviewed" if ok else ("failed" if state == "process_finished" else state),
                   "process_exit_code": returncode, "result": result, "run_directory": str(run_dir),
                   "note": "A completed model turn is not proof that acceptance criteria passed. Review artifacts and tests."}
        receipt_path = run_dir / "receipt.json"
        receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
        os.chmod(receipt_path, 0o600)
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 0 if ok else 1


def doctor():
    required = ["hermes", "git"]
    optional = ["claude", "gh", "docker", "ansible-playbook", "tofu", "trivy", "holmes", "gws"]
    statuses = {name: bool(shutil.which(name)) for name in required + optional}
    print(json.dumps({"required": {n: statuses[n] for n in required},
                      "optional": {n: statuses[n] for n in optional},
                      "note": "Executable presence only; does not verify credentials, provider access, or integrations."}, indent=2))
    return 0 if all(statuses[n] for n in required) else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    sub.add_parser("doctor")
    ins = sub.add_parser("install")
    ins.add_argument("--apply", action="store_true", help="Create new profiles; default is preview.")
    run = sub.add_parser("run")
    run.add_argument("--agent", choices=list(registry()["agents"]), required=True)
    run.add_argument("--workspace", required=True)
    run.add_argument("--task-file", required=True)
    run.add_argument("--timeout", type=int, default=1800)
    run.add_argument("--max-turns", type=int, default=60)
    args = parser.parse_args(argv)
    try:
        if args.command == "list":
            print(json.dumps(registry(), indent=2))
            return 0
        if args.command == "doctor":
            return doctor()
        if args.command == "install":
            return install(args.apply)
        return run_agent(args.agent, args.workspace, args.task_file, args.timeout, args.max_turns)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
