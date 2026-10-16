# Practical workflows

## Entrepreneur / vibe coding

Ask GANDALF: "Help me ship a small booking MVP. First validate the customer problem, define the smallest paid experiment, then implement only the accepted scope." ELROND clarifies assumptions and acceptance; ARAGORN inspects architecture; DRAGONBORN implements; GALADRIEL verifies. Keep a short `PROJECT_BRIEF.md` and `DECISIONS.md` in your application. Measure adoption and failure rates, not just lines of code.

## Day-to-day

SAMWISE drafts a daily brief, organizes tasks and summarizes documents using your configured Hermes integrations. Connect mail/calendar separately with scoped credentials. Drafting a message is not authorization to send it. No accounts or recurring personal automation are installed by this repository.

## Coding

GANDALF produces one bounded brief. Claude Code inspects the actual project and uses a specialist only when useful. Run tests with explicit gates. Example: unit suite, typecheck, lint, one browser acceptance path. Do not use the kit's own tests as proof that your app works.

## DevOps

SAURON collects read-only evidence. GIMLI proposes a diff/plan, test and rollback. BOROMIR reviews the trust boundary; GALADRIEL checks regressions. Deployment is separate and needs the authorized environment and action. Add project-specific gates for Terraform/OpenTofu validate, container scans, policy tests and staging health. Never execute a generated apply plan without checking resources and blast radius.

## Continuous upkeep

The repository's GitHub Actions workflow runs tests on each push/PR and weekly. A weekly job runs `python3 fellowship.py audit-updates`, comparing source HEADs with the pinned catalog. This reports candidate updates; it does not replace pins or execute new upstream code. GitHub Actions must be enabled on the repository. Dependabot raises workflow dependency PRs when available. Review candidates, update the SHA in a branch, run the complete kit tests, install the candidate in a disposable target project and run representative model/tool smoke tests before merging.

For an app, invoke `fellowship.py check --workspace /absolute/app --gates /absolute/gates.json` from its existing CI. Exit nonzero blocks promotion. Test commands are executable instructions: review unfamiliar gate files and use disposable environments for untrusted repositories. Avoid endless Ralph loops; set a hard iteration budget and stop on a repeated failing state.
