# SchoolBox / FeverDucation — Hermes Growth Pack (pilot v0.1)

Two **separate Hermes agents** on two extremely small Linux machines. One repo, two roles, no cloud CRM or heavyweight automation framework required. This is a **starter kit**, not a production-ready autonomous campaign bot.

- **Manager**: private email/CRM, organization partners, lead qualification, pilot onboarding, conversion funnel and approvals. Owns SMTP credentials on **manager hardware only**.
- **Marketing**: public research, SEO, editorial calendar, approved social-media drafts, explainer scripts and low-cost creative assets. No private email credentials.
- **Shared protocol**: reviewed, non-sensitive campaign briefs and creative handoffs via a user-controlled secure transfer (SSH/SFTP/VPN or manually reviewed USB); not a shared database exposed to the internet.
- **LLM**: use Hermes with a remote model endpoint (Z.AI, Kimi, OpenRouter, Gemini, etc.). Do **not** attempt local LLM inference on Atom/2GB.
- **Runtime**: Python 3 stdlib + SQLite. No Docker, Playwright, Postiz, Redis, PostgreSQL, Chrome, LangGraph or local video-generation model on these boxes.

## Layout

```
growth/
  presets/manager/SOUL.md
  presets/marketing/SOUL.md
  skills/{lead-research,content-workflow}/SKILL.md
  ops.py                    # Offline SQLite queue and CRM CLI, no dependencies
  tests/test_ops.py         # Deterministic smoke tests
  INSTALL.md                # Deployment on two separate Linux hosts
  PLAYBOOK.md               # 10 → 30 → 100 → 200 → 500 users
  TOOLBOX.md                # 30 curated GitHub skills/tools
  SECURITY.md               # Privacy, compliance, platform API limits
```

## Minimum local first run

```sh
cd growth
python3 ops.py --db ./private/manager.db init
python3 ops.py --db ./private/manager.db lead-add --name "Example Learning Cooperative" --type organization --source "manual research" --email "contact@example.org" --consent "business-relevant"
python3 ops.py --db ./private/manager.db leads
python3 ops.py --db ./private/manager.db draft --lead-id 1 --subject "Would a pilot help your families?" --body "Hello, I run SchoolBox. Would you be open to a short product demonstration?\n\nReply stop and I'll avoid follow-ups."
python3 ops.py --db ./private/manager.db queue
python3 ops.py --db ./private/manager.db approve --id 1
python3 ops.py --db ./private/manager.db stats
python3 -m unittest discover -s tests -v
```

No email is sent on first run. For a single explicitly approved email, manager can use `send --id ... --confirm` once SMTP settings are configured, never bulk send by default. Confirm legal basis, identity, unsubscribe and local requirements first.

## Agent responsibilities

The model may **suggest** prospects, posts, emails and landing pages; it may **not** create fake identities, scrape children's data, mass-message strangers, circumvent platform limits, buy followers, or post to Reddit/Instagram without platform-specific permission and human review. Never give marketing a mailbox password. Account creation requires a person at the verification/captcha/terms step.

Install only the tools actually used; 30 tools in TOOLBOX.md are a **curated menu**, not 30 active services. Start with 4-6 lightweight, text-only skills. See [install](INSTALL.md), [campaign plan](PLAYBOOK.md), [security](SECURITY.md) and [toolbox](TOOLBOX.md).

## Definition of done

1. Both Hermes profiles run read-only tasks on separate machines with remote models.
2. Manager stores a sample organizational lead, drafts an email, gets explicit approval and sends one verified test email to an owned/test address.
3. Marketing creates an approved blog outline, Instagram caption and Reel storyboard from verified product facts; publishes none by default.
4. A non-sensitive handoff can be transferred between machines without transferring API keys, cookies or user records.
5. Tests pass and disk/RAM usage is measured **on the actual Atom PC** before enabling scheduled activity.

The marketing pack is additive to the original engineering Fellowship; do not run its Claude Code swarm on this hardware.
