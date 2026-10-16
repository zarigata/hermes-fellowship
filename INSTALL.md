# Selectable installation

## For Hermes reading a repository URL

First establish intent from the user's request. If they asked to install this kit, proceed with the steps below; there is no need to ask again for the same authorization. If they only pasted a link, inspect it as context. If a prior `.fellowship/config.json` explicitly has `intent: url-install`, the active Fellowship coordinator may treat future links to exactly `github.com/zarigata/hermes-fellowship` or `github.com/Dagoth-Ur-69/hermes-fellowship` as requests to prepare/apply this kit's setup, subject to existing permissions. No other URL inherits that preference. Repository text cannot authorize itself.

1. Inspect the repository, this guide, existing project instructions and local configuration.
2. Confirm installed prerequisites using `hermes --version`, `claude --version`, `git --version`, `python3 --version`. Install missing executables only from their official documentation and under the user's authorization. Never download model weights without checking hardware/storage and the chosen model.
3. Identify the project directory. If it is unknown, ask that one necessary question. Do not configure the kit's checkout as the user's application by accident.
4. Run `python3 fellowship.py wizard --workspace /absolute/project`. The user selects model server, actual context, plugin pack, and optional future URL intent. For headless Hermes, use the explicit equivalent below with known user choices; do not hang on an interactive wizard.
5. Apply the selected setup, run doctor, then run a tiny read-only plan and one small reversible coding/test task. Plugin installation can fail partway; rerun after fixing the reported prerequisite. Do not call a partial install successful.
6. Report what was installed, model/endpoint (no token), active plugins, checks, and any missing external credentials.

## Native Hermes distribution

```sh
hermes profile install github.com/zarigata/hermes-fellowship --alias
hermes -p fellowship-gandalf setup
hermes -p fellowship-gandalf chat
```

Use the Dagoth-Ur-69 URL instead if desired, not both into the same profile. Native installation does not execute this kit's custom bootstrap. The installed SOUL tells GANDALF to complete it from its `HERMES_HOME` directory. The root distribution contains everything required by `fellowship.py`; no secret is bundled. Use `hermes profile update fellowship-gandalf` for reviewed distribution updates. Keep your application checkout separate.

Optional separate daily/specialist Hermes profiles:

```sh
python3 council.py install                 # preview seven fresh profiles
python3 council.py install --apply
```

The native distribution already owns `fellowship-gandalf`, so choose the native path OR the seven-profile path. The latter deliberately refuses conflicting existing profiles. Each profile needs its own Hermes setup. All coding profiles route implementation to Claude Code.

## Explicit project setup

```sh
python3 fellowship.py setup --workspace /absolute/project \
  --preset ollama-qwen-lean --bundle lean
# After choosing the shown configuration:
python3 fellowship.py setup --workspace /absolute/project \
  --preset ollama-qwen-lean --bundle lean --apply --install-plugins
```

Alternatives:

```sh
python3 fellowship.py setup --workspace /absolute/project \
  --preset lmstudio-local --model YOUR_LOADED_MODEL_ID --context 32768 --apply --install-plugins
python3 fellowship.py setup --workspace /absolute/project \
  --preset zai-glm --bundle balanced --apply --install-plugins
python3 fellowship.py setup --workspace /absolute/project \
  --preset custom-anthropic --model EXACT_MODEL_ID \
  --base-url https://your-server.example --context 65536 --bundle full --apply --install-plugins
```

For Z.AI, supply `ZAI_API_KEY` through your shell or secret manager. For authenticated LM Studio/custom servers use `FELLOWSHIP_API_KEY`. Keys are not written to project config; the launcher uses a private temporary settings file during the process and removes it afterward. Do not paste secrets into tasks, logs or git.

Claude plugin marketplace registration affects the user's marketplace registry. Plugin activation uses `--scope local` for the target project. Existing unrelated plugins, MCP servers and managed settings may still apply: inspect `/plugin`, `/status` and effective settings. The pack is not an isolation boundary. Plugins run code with your account's access; review their pinned sources. Keep the kit directory at its current path because the marketplace points to it.

The installer preserves existing modified fellowship agent cards by stopping before overwriting them. Previous local config is backed up as `.fellowship/config.previous.json`. No global credentials are copied. To undo: restore that config if present; remove only the eight `fellowship-*` project agent files you installed after reviewing changes; disable/uninstall `name@hermes-fellowship --scope local` using Claude's plugin CLI. Remove the marketplace only when no other project uses it. Never delete other project settings.
