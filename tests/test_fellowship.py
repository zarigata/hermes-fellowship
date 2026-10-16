import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import fellowship as f

FAKE = '''#!/usr/bin/env python3
import json, sys, time, os
if '--version' in sys.argv:
 print('2.1.257 (Claude Code)'); sys.exit(0)
prompt=sys.stdin.read()
if 'TIMEOUT_TEST' in prompt: time.sleep(30)
if 'MISSING_TEST' in prompt: sys.exit(0)
settings_path=sys.argv[sys.argv.index('--settings')+1]
settings=json.load(open(settings_path))
e={'type':'result','subtype':'success','is_error':False,'result':prompt,
   'model':os.environ['ANTHROPIC_MODEL'],'settings_path':settings_path,
   'context':settings['env']['CLAUDE_CODE_MAX_CONTEXT_TOKENS']}
if 'ERROR_TEST' in prompt:e['is_error']=True
if 'LIMIT_TEST' in prompt:e['subtype']='error_max_turns'
if 'DENIAL_TEST' in prompt:e['permission_denials']=[{'tool_name':'Bash'}]
print(json.dumps(e))
if 'EXIT_TEST' in prompt:sys.exit(4)
'''


class FellowshipTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.w=Path(self.temp.name)/'project with spaces';self.w.mkdir()
        self.cli=Path(self.temp.name)/'claude';self.cli.write_text(FAKE);self.cli.chmod(0o700)
        self.c=f.make_config('lmstudio-local',model='local-test')
        f.write(self.w/'.fellowship/config.json',self.c)
        self.task=self.w/'task.json';self.gate=self.w/'gates.json'
        self.task_text('Small change')
        self.gates(0)

    def task_text(self, goal):
        f.write(self.task,{'goal':goal,'context':'Read relevant files','acceptance':['tests pass'],
                           'authorized_actions':['edit fixture only']})

    def gates(self, exit_code):
        f.write(self.gate,[{'name':'actual process exit','command':[sys.executable,'-c',f'import sys; sys.exit({exit_code})'],'timeout':5}])

    def run_it(self, gates=True, **kw):
        out=io.StringIO()
        with patch.object(f,'check_claude',return_value=str(self.cli)),contextlib.redirect_stdout(out):
            rc=f.execute(self.w,self.task,self.gate if gates else None,**kw)
        return rc,json.loads(out.getvalue())

    def test_literal_prompt_success_and_private_receipt(self):
        marker=self.w/'bad'
        self.task_text(f'$(touch {marker}) `touch bad` ; quotes "hello"')
        rc,result=self.run_it()
        self.assertEqual(rc,0);self.assertEqual(result['status'],'verified_gates_passed')
        self.assertFalse(marker.exists());self.assertIn('$(touch',result['result']['result'])
        self.assertFalse(Path(result['result']['settings_path']).exists())
        run=Path(result['run_directory'])
        self.assertEqual(run.stat().st_mode & 0o777,0o700)
        self.assertEqual((run/'receipt.json').stat().st_mode & 0o777,0o600)

    def test_missing_result_and_each_error_fail_closed(self):
        for marker in ['MISSING_TEST','ERROR_TEST','LIMIT_TEST','DENIAL_TEST','EXIT_TEST']:
            with self.subTest(marker=marker):
                self.task_text(marker);rc,r=self.run_it()
                self.assertEqual(rc,1);self.assertEqual(r['status'],'failed');self.assertEqual(r['gates'],[])

    def test_timeout_not_success(self):
        self.task_text('TIMEOUT_TEST');rc,r=self.run_it(seconds=1)
        self.assertEqual(rc,1);self.assertEqual(r['process_state'],'timeout_unknown_effects')

    def test_failed_gates_block_success(self):
        self.gates(7);rc,r=self.run_it()
        self.assertEqual(rc,1);self.assertEqual(r['status'],'checks_failed')
        self.assertEqual(r['gates'][0]['exit_code'],7)

    def test_no_gates_is_unverified(self):
        rc,r=self.run_it(gates=False)
        self.assertEqual(rc,1);self.assertEqual(r['status'],'completed_unverified')

    def test_plan_does_not_execute_gates(self):
        self.gates(7);rc,r=self.run_it(plan=True)
        self.assertEqual(rc,0);self.assertTrue(r['plan_only']);self.assertEqual(r['gates'],[])
        self.assertEqual(r['status'],'completed_unverified')

    def test_provider_aliases_and_forced_subagent_match(self):
        env=f.routing(self.c)['env']
        for key in ['ANTHROPIC_MODEL','ANTHROPIC_DEFAULT_HAIKU_MODEL','ANTHROPIC_DEFAULT_SONNET_MODEL',
                    'ANTHROPIC_DEFAULT_OPUS_MODEL','CLAUDE_CODE_SUBAGENT_MODEL']:
            self.assertEqual(env[key],'local-test')
        self.assertEqual(env['CLAUDE_CODE_SUBAGENT_MODEL_FORCE'],'1')
        self.assertEqual(env['ANTHROPIC_API_KEY'],'')
        self.assertNotIn('CLAUDE_CODE_AUTO_COMPACT_WINDOW',env)

    def test_cloud_key_required_and_not_in_saved_config(self):
        c=f.make_config('zai-glm')
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaisesRegex(ValueError,'ZAI_API_KEY'):f.routing(c)
        with patch.dict(os.environ,{'ZAI_API_KEY':'fixture-secret'}):
            self.assertEqual(f.routing(c)['env']['ANTHROPIC_AUTH_TOKEN'],'fixture-secret')
        self.assertNotIn('fixture-secret',json.dumps(c))

    def test_invalid_endpoints_and_model_aliases_rejected(self):
        for url in ['http://remote.example','https://user:secret@host','https://host?key=x','file:///tmp/x']:
            with self.assertRaises(ValueError):f.make_config('custom-anthropic',model='qwen',base_url=url)
        for model in ['claude-sonnet','glm[1m]']:
            with self.assertRaises(ValueError):f.make_config('lmstudio-local',model=model)

    def test_context_probe_shrinks_never_grows(self):
        c=f.make_config('ollama-qwen-balanced')
        for capacity,expected in [(32768,32768),(131072,65536)]:
            data=io.BytesIO(json.dumps({'models':[{'name':c['model'],'context_length':capacity}]}).encode())
            with patch.object(f,'urlopen',return_value=data):self.assertEqual(f.adapt_context(c)['context'],expected)
        data=io.BytesIO(json.dumps({'models':[{'name':c['model'],'context_length':4096}]}).encode())
        with patch.object(f,'urlopen',return_value=data),self.assertRaises(ValueError):f.adapt_context(c)

    def test_empty_or_shell_string_gates_rejected(self):
        for invalid in [[],[{'name':'bad','command':'echo hello'}],[{'name':'bad','command':['true'],'timeout':0}]]:
            f.write(self.gate,invalid)
            with self.assertRaises(ValueError):f.validate_gates(self.gate)

    def test_large_brief_rejected_without_truncation(self):
        self.task_text('x'*17000)
        with patch.object(f,'check_claude',return_value=str(self.cli)),self.assertRaisesRegex(ValueError,'Brief too large'):
            f.execute(self.w,self.task)

    def test_existing_modified_agent_preserved(self):
        f.copy_agents(self.w)
        agent=next((self.w/'.claude/agents').glob('*.md'));agent.write_text('user customization')
        with self.assertRaisesRegex(ValueError,'Preserving modified'):f.copy_agents(self.w)
        self.assertEqual(agent.read_text(),'user customization')

    def test_catalog_has_20_unique_pinned_sources(self):
        plugins=f.read(f.ROOT/'.claude-plugin/marketplace.json')['plugins']
        self.assertEqual(len(plugins),20);self.assertEqual(len({p['name'] for p in plugins}),20)
        for p in plugins:self.assertRegex(p['source']['sha'],r'^[0-9a-f]{40}$')
        packs=f.read(f.ROOT/'presets/plugins.json')
        self.assertEqual(len(packs['lean']['install']),10)
        self.assertTrue(set(packs['lean']['active'])<=set(packs['lean']['install']))
        self.assertNotIn('superpowers',packs['lean']['active'])
        self.assertNotIn('ponytail',packs['balanced']['active'])

    def test_plugin_install_is_project_local(self):
        for cmd in f.plugin_commands('claude','full'):
            if cmd[2] in ('install','disable'):self.assertEqual(cmd[-2:],['--scope','local'])

    def test_compaction_checkpoint_and_session_hint(self):
        f.recovery_hook(self.w,{'hook_event_name':'PostCompact','compact_summary':'Pending regression test'})
        self.assertEqual(f.read(self.w/'.fellowship/compact.json')['summary'],'Pending regression test')
        f.write(self.w/'.fellowship/checkpoint.json',{'state':'running'})
        out=io.StringIO()
        with contextlib.redirect_stdout(out):f.recovery_hook(self.w,{'hook_event_name':'SessionStart'})
        self.assertIn('checkpoint.json',out.getvalue())

    def test_cli_version_gate(self):
        with patch.object(f.shutil,'which',return_value=str(self.cli)):
            self.assertEqual(f.check_claude(),str(self.cli))
        old=subprocess.CompletedProcess([],0,'2.1.100','')
        with patch.object(f.shutil,'which',return_value=str(self.cli)),patch.object(f.subprocess,'run',return_value=old):
            with self.assertRaisesRegex(ValueError,'2.1.257'):f.check_claude()

    def test_setup_preview_does_not_modify_workspace(self):
        empty=Path(self.temp.name)/'preview';empty.mkdir()
        with contextlib.redirect_stdout(io.StringIO()):f.setup(empty,self.c,False,True)
        self.assertEqual(list(empty.iterdir()),[])


if __name__=='__main__':unittest.main()
