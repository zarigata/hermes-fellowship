#!/usr/bin/env python3
"""Hermes -> Claude Code: selectable setup, provider routing and evidence receipts."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import shlex
import subprocess
import sys
import tempfile
import time
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from council import lock_profile, stop_group, final_result, load_task

ROOT = Path(__file__).resolve().parent
MIN_CLAUDE = (2, 1, 257)


def read(path):
    return json.loads(Path(path).read_text())


def write(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temp = path.with_suffix(path.suffix + '.tmp')
    with temp.open('w') as f:
        os.chmod(temp, 0o600)
        json.dump(obj, f, indent=2)
        f.write('\n')
    temp.replace(path)


def workspace(path):
    p = Path(path).expanduser().resolve(strict=True)
    if not p.is_dir():
        raise ValueError('Workspace is not a directory')
    return p


def check_claude():
    cli = shutil.which('claude')
    if not cli:
        raise ValueError('Install Claude Code from https://code.claude.com/docs/en/setup first')
    v = subprocess.run([cli, '--version'], capture_output=True, text=True, timeout=15, check=True)
    found = re.search(r'(\d+)\.(\d+)\.(\d+)', v.stdout)
    if not found or tuple(map(int, found.groups())) < MIN_CLAUDE:
        raise ValueError('Claude Code >= 2.1.257 required for subagent routing controls')
    return cli


def make_config(preset, model=None, base_url=None, context=None, bundle=None, intent='manual'):
    c = dict(read(ROOT / 'presets/models.json')[preset])
    c.update(preset=preset, intent=intent)
    for k, v in [('model', model), ('base_url', base_url), ('context', context), ('plugins', bundle)]:
        if v is not None:
            c[k] = v
    if not c['model'] or not c['base_url']:
        raise ValueError('This preset requires an exact --model and/or --base-url')
    u = urlparse(c['base_url'])
    if u.username or u.password or u.query or u.fragment or not u.hostname:
        raise ValueError('Endpoint must not contain credentials, query or fragment')
    if u.scheme != 'https' and not (u.scheme == 'http' and u.hostname in ('localhost', '127.0.0.1', '::1')):
        raise ValueError('Use HTTPS for non-loopback servers')
    if not 16384 <= c['context'] <= 1000000:
        raise ValueError('Context must be 16384..1000000 and within the loaded server capacity')
    if c['model'].startswith('claude-') or '[1m]' in c['model']:
        raise ValueError('These custom-provider presets require the real non-Claude model ID, without [1m]')
    c['output'] = min(c['output'], c['context'] // 8)
    if c['context'] < 65536:
        c['concurrency'] = 1
    if c['plugins'] not in read(ROOT / 'presets/plugins.json'):
        raise ValueError('Unknown plugin bundle')
    return c


def routing(c):
    token = {'ollama': 'ollama', 'lmstudio': 'lmstudio'}.get(c['provider'])
    if c['provider'] == 'zai':
        token = os.environ.get('ZAI_API_KEY')
        if not token:
            raise ValueError('Set ZAI_API_KEY in your environment; never commit it')
    elif c['provider'] in ('custom', 'lmstudio'):
        token = os.environ.get('FELLOWSHIP_API_KEY') or token or 'local'
    env = {
        'ANTHROPIC_BASE_URL': c['base_url'], 'ANTHROPIC_AUTH_TOKEN': token,
        'ANTHROPIC_API_KEY': '', 'ANTHROPIC_MODEL': c['model'],
        'CLAUDE_CODE_USE_BEDROCK': '0', 'CLAUDE_CODE_USE_VERTEX': '0',
        'CLAUDE_CODE_USE_FOUNDRY': '0',
        'CLAUDE_CODE_SUBAGENT_MODEL': c['model'], 'CLAUDE_CODE_SUBAGENT_MODEL_FORCE': '1',
        'CLAUDE_CODE_MAX_CONTEXT_TOKENS': str(c['context']),
        'CLAUDE_CODE_MAX_OUTPUT_TOKENS': str(c['output']),
        'CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS': str(c['concurrency']),
        'CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH': '1',
        'CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS': '2000',
        'CLAUDE_CODE_MAX_RETRIES': '2', 'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC': '1',
        'PONYTAIL_DEFAULT_MODE': 'lite',
    }
    for tier in ('HAIKU', 'SONNET', 'OPUS'):
        env['ANTHROPIC_DEFAULT_' + tier + '_MODEL'] = c['model']
    if c['plugins'] == 'lean':
        env['ENABLE_CODE_SECURITY_REVIEW'] = '0'  # keep pattern checks; use explicit reviewer + gates
    env['SECURITY_REVIEW_MODEL'] = c['model']
    active = read(ROOT / 'presets/plugins.json')[c['plugins']]['active']
    flags = {p['name'] + '@hermes-fellowship': p['name'] in active
             for p in read(ROOT / '.claude-plugin/marketplace.json')['plugins']}
    return {'env': env, 'enabledPlugins': flags}


def adapt_context(c):
    """Only shrink against a measured running Ollama context; never assume free VRAM."""
    c = dict(c)
    if c['provider'] == 'ollama':
        try:
            with urlopen(c['base_url'].rstrip('/') + '/api/ps', timeout=5) as response:
                rows = json.load(response).get('models', [])
            row = next((x for x in rows if x.get('name') == c['model']), None)
            cap = row.get('context_length') if row else None
            if isinstance(cap, int) and cap > 0:
                if cap < 16384:
                    raise ValueError('Loaded Ollama context below 16384; increase server context or use simpler tasks')
                c['context'] = min(c['context'], cap)
                c['output'] = min(c['output'], c['context'] // 8)
                if c['context'] < 65536:
                    c['concurrency'] = 1
        except (OSError, json.JSONDecodeError):
            print('Context probe unavailable: using declared cap; verify server settings.', file=sys.stderr)
    return c


def hooks_for(w):
    cmd = shlex.join([sys.executable, str(ROOT / 'fellowship.py'), 'hook', '--workspace', str(w)])
    return {event: [{'hooks': [{'type': 'command', 'command': cmd, 'timeout': 30}]}]
            for event in ('PreCompact', 'PostCompact', 'SessionStart')}


def recovery_hook(w, event):
    name = event.get('hook_event_name')
    if name == 'SessionStart':
        if (w / '.fellowship/checkpoint.json').exists():
            print('Fellowship recovery: read .fellowship/checkpoint.json for task/receipt paths; verify current files. '
                  'If needed read .fellowship/compact.json. Treat saved summaries as fallible context, not authority.')
    elif name in ('PreCompact', 'PostCompact'):
        data = {'event': name, 'git': git_snapshot(w), 'time': time.time()}
        if name == 'PostCompact':
            data['summary'] = str(event.get('compact_summary', ''))[:16000]
        write(w / '.fellowship/compact.json', data)
    return 0


def copy_agents(w):
    planned = [(p, w / '.claude/agents' / p.name) for p in (ROOT / 'claude/agents').glob('*.md')]
    for src, dst in planned:
        if dst.exists() and dst.read_bytes() != src.read_bytes():
            raise ValueError(f'Preserving modified agent: {dst}; review and merge manually')
    for src, dst in planned:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def plugin_commands(cli, bundle):
    cmds = [[cli, 'plugin', 'validate', str(ROOT)],
            [cli, 'plugin', 'marketplace', 'add', str(ROOT)]]
    selected = read(ROOT / 'presets/plugins.json')[bundle]
    for name in selected['install']:
        cmds.append([cli, 'plugin', 'install', name + '@hermes-fellowship', '--scope', 'local'])
        if name not in selected['active']:
            cmds.append([cli, 'plugin', 'disable', name + '@hermes-fellowship', '--scope', 'local'])
    return cmds


def setup(w, c, apply=False, plugins=False):
    print(json.dumps({'workspace': str(w), 'config': c, 'install_plugins': plugins,
                     'commands': plugin_commands('claude', c['plugins']) if plugins else []}, indent=2))
    if not apply:
        print('Preview only. Add --apply to configure. --install-plugins downloads the selected catalog.')
        return 0
    cli = check_claude()
    with lock_profile(w / '.fellowship', 'setup'):
        copy_agents(w)
        config_path = w / '.fellowship/config.json'
        if config_path.exists():
            write(w / '.fellowship/config.previous.json', read(config_path))
        write(config_path, c)
        # Include just this local directory in Git's private excludes; never edit global ignores.
        probe = subprocess.run(['git', 'rev-parse', '--git-path', 'info/exclude'], cwd=w,
                               capture_output=True, text=True)
        if probe.returncode == 0:
            ex = Path(probe.stdout.strip())
            if not ex.is_absolute():
                ex = w / ex
            ex.parent.mkdir(parents=True, exist_ok=True)
            old = ex.read_text() if ex.exists() else ''
            if '\n.fellowship/\n' not in '\n' + old:
                ex.write_text(old + '\n.fellowship/\n.claude/settings.local.json\n')
        if plugins:
            for cmd in plugin_commands(cli, c['plugins']):
                subprocess.run(cmd, cwd=w, check=True, timeout=300)
    print('Configured. Keep this distribution directory: the marketplace references it. Run doctor, then a small task.')
    return 0


def git_snapshot(w):
    result = {}
    for key, args in [('head', ['rev-parse', 'HEAD']), ('status', ['status', '--short']),
                      ('diffstat', ['diff', '--stat'])]:
        p = subprocess.run(['git'] + args, cwd=w, text=True, capture_output=True, timeout=15)
        result[key] = p.stdout[:12000] if p.returncode == 0 else 'unavailable'
    return result


def run_process(cmd, w, prompt, out, err, seconds, env=None):
    with Path(out).open('w') as stdout, Path(err).open('w') as stderr:
        os.chmod(out, 0o600); os.chmod(err, 0o600)
        p = subprocess.Popen(cmd, cwd=w, env=env, stdin=subprocess.PIPE, stdout=stdout,
                             stderr=stderr, text=True, start_new_session=True)
        try:
            p.communicate(prompt, timeout=seconds)
            return p.returncode, 'finished'
        except subprocess.TimeoutExpired:
            stop_group(p)
            return None, 'timeout_unknown_effects'
        except KeyboardInterrupt:
            stop_group(p)
            return None, 'interrupted_unknown_effects'


def validate_gates(path):
    gates = read(path)
    if not isinstance(gates, list) or not gates:
        raise ValueError('Provide at least one explicit quality gate command array')
    for g in gates:
        if not isinstance(g, dict) or set(g) - {'name', 'command', 'timeout'}:
            raise ValueError('Invalid quality gate')
        if not isinstance(g.get('name'), str) or not g['name'].strip():
            raise ValueError('Gate needs a name')
        cmd = g.get('command')
        if not isinstance(cmd, list) or not cmd or not all(isinstance(x, str) and x for x in cmd):
            raise ValueError('Gate command must be a nonempty argv array')
        if not isinstance(g.get('timeout', 300), int) or not 1 <= g.get('timeout', 300) <= 1800:
            raise ValueError('Gate timeout must be 1..1800 seconds')
    return gates


def gates_run(w, gates, directory):
    results = []
    for i, g in enumerate(gates):
        code, state = run_process(g['command'], w, '', directory / f'gate-{i}.log',
                                 directory / f'gate-{i}.err', g.get('timeout', 300))
        results.append({'name': g['name'], 'command': g['command'], 'exit_code': code,
                        'state': state, 'passed': code == 0 and state == 'finished'})
    return results


def execute(w, task_path, gates_path=None, seconds=1800, turns=24, plan=False):
    if not 1 <= seconds <= 14400 or not 1 <= turns <= 100:
        raise ValueError('Invalid timeout or turn budget')
    task = load_task(task_path)
    gates = validate_gates(gates_path) if gates_path else []
    # Snapshot user-reviewed gates before the model can edit repository files.
    c = adapt_context(read(w / '.fellowship/config.json'))
    settings = routing(c)
    settings['hooks'] = hooks_for(w)
    cli = check_claude()
    brief = json.dumps(task, ensure_ascii=False)
    if len(brief) > min(16000, c['context'] // 2):
        raise ValueError('Brief too large: save source material in files and reference specific paths; no silent truncation')
    with lock_profile(w / '.fellowship', 'claude-writer'):
        runs = w / '.fellowship/runs'; runs.mkdir(parents=True, exist_ok=True, mode=0o700)
        d = Path(tempfile.mkdtemp(prefix='run-', dir=runs))
        write(d / 'task.json', task)
        before = git_snapshot(w)
        write(w / '.fellowship/checkpoint.json', {'state': 'running', 'run': str(d), 'task_file': str(d / 'task.json'), 'git': before})
        prompt = brief + '\nUse the requested workspace. Final response: files changed, decisions, actual checks, unresolved risks and next action.'
        cmd = [cli, '-p', '--model', c['model'], '--output-format', 'stream-json', '--verbose',
               '--max-turns', str(turns), '--permission-mode', 'plan' if plan else 'default',
               '--append-system-prompt', (ROOT / 'claude/COORDINATOR.md').read_text()]
        # A private, short-lived file puts routing above project settings; contains token only during execution.
        with tempfile.TemporaryDirectory(prefix='fellowship-settings-') as temp:
            settings_path = Path(temp) / 'settings.json'; write(settings_path, settings)
            cmd += ['--settings', str(settings_path)]
            env = dict(os.environ)
            for k in ('CLAUDE_CODE_AUTO_COMPACT_WINDOW', 'DISABLE_COMPACT', 'ANTHROPIC_CUSTOM_MODEL_OPTION',
                      'ANTHROPIC_SMALL_FAST_MODEL', 'CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT'):
                env.pop(k, None)
            env.update(settings['env'])
            code, state = run_process(cmd, w, prompt, d / 'events.jsonl', d / 'stderr.log', seconds, env)
        result = final_result(d / 'events.jsonl')
        success = (code == 0 and state == 'finished' and result is not None and
                   result.get('subtype') == 'success' and result.get('is_error') is False and
                   not result.get('permission_denials'))
        checks = gates_run(w, gates, d) if success and gates and not plan else []
        status = ('verified_gates_passed' if checks and all(x['passed'] for x in checks)
                  else 'checks_failed' if checks else 'completed_unverified' if success else 'failed')
        receipt = {'status': status, 'process_state': state, 'process_exit_code': code,
                   'model': c['model'], 'context': c['context'], 'plan_only': plan,
                   'result': result, 'gates': checks, 'git_before': before, 'git_after': git_snapshot(w),
                   'run_directory': str(d), 'note': 'Passing these gates covers only their assertions; human/product acceptance may remain.'}
        write(d / 'receipt.json', receipt)
        write(w / '.fellowship/checkpoint.json', {'state': status, 'receipt': str(d / 'receipt.json'),
                                                'task_file': str(d / 'task.json'), 'git': receipt['git_after']})
        print(json.dumps(receipt, indent=2))
        return 0 if status == 'verified_gates_passed' or (plan and success) else 1


def doctor(w):
    cli = check_claude(); c = read(w / '.fellowship/config.json'); settings = routing(c)
    info = {'claude': cli, 'provider': c['provider'], 'model': c['model'], 'client_context': c['context'],
            'note': 'Endpoint listing does not prove tool calls work. Run a tiny plan before real work. Server context must be configured separately.'}
    if c['provider'] != 'zai':
        suffix = '/api/tags' if c['provider'] == 'ollama' else '/v1/models'
        headers = {'Authorization': 'Bearer ' + settings['env']['ANTHROPIC_AUTH_TOKEN']}
        with urlopen(Request(c['base_url'].rstrip('/') + suffix, headers=headers), timeout=10) as resp:
            data = json.load(resp)
        ids = [x.get('name') for x in data.get('models', [])] if c['provider'] == 'ollama' else [x.get('id') for x in data.get('data', [])]
        info['available_models'] = ids
        if c['model'] not in ids:
            raise ValueError('Configured model is not listed by server; use its exact model ID')
    print(json.dumps(info, indent=2)); return 0


def audit_updates():
    results = []
    sources = {(p['source']['url'], p['source']['sha']) for p in read(ROOT / '.claude-plugin/marketplace.json')['plugins']}
    for url, sha in sorted(sources):
        p = subprocess.run(['git', 'ls-remote', url, 'HEAD'], capture_output=True, text=True, timeout=30)
        latest = p.stdout.split()[0] if p.returncode == 0 and p.stdout.split() else None
        results.append({'source': url, 'pinned': sha, 'upstream_head': latest,
                        'review_needed': latest != sha, 'reachable': latest is not None})
    print(json.dumps(results, indent=2))
    return 0 if all(r['reachable'] for r in results) else 1


def wizard(w):
    models = list(read(ROOT / 'presets/models.json'))
    for i, name in enumerate(models, 1): print(f'{i}. {name}')
    preset = models[int(input('Model preset number: ')) - 1]
    model = input('Exact model ID (Enter for preset): ').strip() or None
    endpoint = input('Endpoint (Enter for preset): ').strip() or None
    context = input('Actual server context tokens (Enter for preset): ').strip()
    bundle = input('Plugin pack lean / balanced / full [lean]: ').strip() or 'lean'
    intent = 'url-install' if input('Treat future links to this exact kit as install requests? [y/N]: ').lower() == 'y' else 'manual'
    c = make_config(preset, model, endpoint, int(context) if context else None, bundle, intent)
    setup(w, c)
    if input('Apply this setup and download the selected plugins? [y/N]: ').lower() == 'y':
        return setup(w, c, True, True)
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__); sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('catalog'); sub.add_parser('audit-updates')
    for name in ('setup', 'wizard', 'doctor', 'run', 'check', 'hook'):
        s = sub.add_parser(name); s.add_argument('--workspace', required=True)
        if name == 'setup':
            s.add_argument('--preset', choices=list(read(ROOT / 'presets/models.json')), default='ollama-qwen-lean')
            s.add_argument('--model'); s.add_argument('--base-url'); s.add_argument('--context', type=int)
            s.add_argument('--bundle', choices=['lean', 'balanced', 'full'])
            s.add_argument('--intent', choices=['manual', 'url-install'], default='manual')
            s.add_argument('--apply', action='store_true'); s.add_argument('--install-plugins', action='store_true')
        if name in ('run', 'check'): s.add_argument('--gates', required=name == 'check')
        if name == 'run':
            s.add_argument('--task-file', required=True); s.add_argument('--timeout', type=int, default=1800)
            s.add_argument('--max-turns', type=int, default=24); s.add_argument('--plan', action='store_true')
    a = p.parse_args(argv)
    try:
        if a.cmd == 'catalog': print(json.dumps(read(ROOT / 'presets/plugins.json'), indent=2)); return 0
        if a.cmd == 'audit-updates': return audit_updates()
        w = workspace(a.workspace)
        if a.cmd == 'setup': return setup(w, make_config(a.preset, a.model, a.base_url, a.context, a.bundle, a.intent), a.apply, a.install_plugins)
        if a.cmd == 'wizard': return wizard(w)
        if a.cmd == 'hook': return recovery_hook(w, json.load(sys.stdin))
        if a.cmd == 'doctor': return doctor(w)
        if a.cmd == 'run': return execute(w, a.task_file, a.gates, a.timeout, a.max_turns, a.plan)
        gates = validate_gates(a.gates)
        with lock_profile(w / '.fellowship', 'claude-writer'):
            d = w / '.fellowship/checks'; d.mkdir(parents=True, exist_ok=True, mode=0o700)
            result = gates_run(w, gates, d); write(d / 'receipt.json', result)
        print(json.dumps(result, indent=2)); return 0 if all(x['passed'] for x in result) else 1
    except (ValueError, KeyError, IndexError, OSError, subprocess.SubprocessError) as e:
        print(f'Error: {e}', file=sys.stderr); return 1


if __name__ == '__main__':
    sys.exit(main())
