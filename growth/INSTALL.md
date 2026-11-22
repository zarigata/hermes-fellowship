# Install on the two Atom machines

**Status:** reviewed design and stdlib CLI prototype. Actual Hermes install, OAuth, Instagram/Reddit permissions, SMTP, and hardware stress tests require your devices and accounts.

## Hardware budget

Target: Atom CPU, 2 GB RAM, 32 GB SSD, one USB stick, Debian minimal 64-bit if CPU supports it (check `uname -m`; if 32-bit, verify Hermes/Python dependency support separately first). No graphical desktop. Keep at least 8 GB free on SSD. USB flash is better used for encrypted backups, not a continuously written SQLite database. If using the USB as the boot disk, expect higher write wear; use log rotation and external backups. SSD failure and USB flash wear are real risks.

Per machine: one Hermes profile, one remote model, one lightweight Python process when requested, SQLite file stored outside git. Avoid heavy parallel tools; no local LLM, Chromium, full video render stack or huge containers. Use `ffmpeg` on a more capable machine or defer short-video rendering until needed.

## 1. Prepare both machines

```sh
sudo apt-get update
sudo apt-get install --no-install-recommends -y ca-certificates curl git python3 python3-venv sqlite3 openssh-client
uname -m; free -h; df -h
```

Install Hermes from its **official** instructions: https://github.com/NousResearch/hermes-agent . Verify `hermes --version` and choose a remote provider via `hermes setup`/`hermes model`. Do not execute third-party install scripts blindly. On Atom hardware, ensure compatible OS/CPU and enough space first.

Clone after this PR is merged into `main`:
```sh
git clone --depth 1 https://github.com/zarigata/hermes-fellowship.git
cd hermes-fellowship/growth
```
Until merged, checkout branch `feature/homeschool-growth-agents` on the clone.

## 2. Manager machine ONLY

```sh
hermes profile create schoolbox-manager --no-credentials
mkdir -p ~/.hermes/profiles/schoolbox-manager
cp presets/manager/SOUL.md ~/.hermes/profiles/schoolbox-manager/SOUL.md
python3 ops.py --db ~/.local/share/schoolbox/manager.db init
hermes -p schoolbox-manager chat
```

If your Hermes version lacks a flag, check `hermes profile create --help`, use a plain new profile, and verify it has **not cloned existing secrets**. Configure remote model with the active profile's `hermes -p schoolbox-manager model` if available; otherwise use its interactive setup. Never commit `~/.hermes/**/.env`.

Optional real mail: configure a **dedicated business mailbox**, application-specific credential or OAuth-backed relay supported by provider, SPF/DKIM/DMARC, permitted sender address, and these env vars in the *manager's private shell/service*, not Git:
```
SMTP_HOST=mail.example.com
SMTP_PORT=465
SMTP_USER=marketing@example.org
SMTP_PASSWORD=REDACTED
SMTP_FROM=marketing@example.org
SMTP_POSTAL_ADDRESS=Your real business mailing address
```
A postal address and working opt-out process are mandatory for US commercial mail. Never paste the secret into an agent prompt. The CLI requires explicit approval and `--confirm` per individual message; even then, double-check jurisdiction-specific consent rules.

## 3. Marketing machine ONLY

```sh
hermes profile create schoolbox-marketing --no-credentials
mkdir -p ~/.hermes/profiles/schoolbox-marketing
cp presets/marketing/SOUL.md ~/.hermes/profiles/schoolbox-marketing/SOUL.md
python3 ops.py --db ~/.local/share/schoolbox/marketing.db init
hermes -p schoolbox-marketing chat
```

Don't configure SMTP or an email inbox on the marketing machine. For optional skill files, install only 4–6 reviewed files into the target profile's `skills/` folder, not the entire upstream repo. The `skills/` folder here contains native Hermes procedure cards; their activation should be verified using Hermes's `skills_list` / `skill_view` after copying.

## 4. Secure handoff between machines

Marketing exports only sanitized proposals in JSON or Markdown; Manager reviews them, identifies target organizations from its own private CRM and manually authorizes messages. Transfer files over SSH/SFTP/VPN or reviewed removable storage. No public HTTP listener. No shared passwords, client tokens, family names, student data, email lists, or unredacted screenshots. Keep the manager DB private to its own OS account (`chmod 700 ~/.local/share/schoolbox`).

## 5. Schedule AFTER validation

Start with a human-run daily brief, then use **Hermes cron** for **draft-only** daily research and weekly performance summaries. Don't schedule unattended email sends or automatic cross-posting. A scheduled job must enforce a max token budget/time budget and no simultaneous heavy jobs. Read https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/cron.md .

## 6. Verification

```sh
python3 -m unittest discover -s tests -v
python3 ops.py --db ./private/smoke.db init
python3 ops.py --db ./private/smoke.db stats
free -m; df -h; du -sh ~/.hermes
```

Use a test address you own for one approved send only after SMTP is configured. Make an offline backup to the encrypted USB and restore into a disposable path. Measure full Hermes idle and peak RSS after deployment. If it swaps constantly, disable gateway extras, reduce skills, schedule sequentially and consider 4 GB RAM instead.
