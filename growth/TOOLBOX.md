# 30 curated marketing tools and skillsets — install selectively

This is a **source-verified menu** of 30 capabilities, not a promise that 30 services run together or that they integrate automatically with Hermes. Rows 1–24 come from the MIT-licensed text-first [Corey Haines marketing skills](https://github.com/coreyhaines31/marketingskills), whose skills are designed for the Agent Skills standard. Read every upstream SKILL.md before installing, adapt to Hermes, pin the reviewed commit. The local machine can load a skill on demand, but model inference is remote. No automatic integrations or account permissions are bundled.

| # | Skill | Why SchoolBox needs it | Agent | Stage |
|---:|---|---|---|---|
| 1 | [product-marketing](https://github.com/coreyhaines31/marketingskills/tree/main/skills/product-marketing) | Source of truth, claims, audience | Both | NOW |
| 2 | [customer-research](https://github.com/coreyhaines31/marketingskills/tree/main/skills/customer-research) | Pilot parent interviews | Manager | NOW |
| 3 | [prospecting](https://github.com/coreyhaines31/marketingskills/tree/main/skills/prospecting) | Public organizational opportunities | Manager | NOW |
| 4 | [cold-email](https://github.com/coreyhaines31/marketingskills/tree/main/skills/cold-email) | Relevant permission-conscious B2B email | Manager | NOW |
| 5 | [emails](https://github.com/coreyhaines31/marketingskills/tree/main/skills/emails) | Opt-in onboarding | Manager | NOW |
| 6 | [community-marketing](https://github.com/coreyhaines31/marketingskills/tree/main/skills/community-marketing) | Authentic community contributions | Marketing | NOW |
| 7 | [social](https://github.com/coreyhaines31/marketingskills/tree/main/skills/social) | Instagram educational posts | Marketing | NOW |
| 8 | [copywriting](https://github.com/coreyhaines31/marketingskills/tree/main/skills/copywriting) | Landing page value prop | Marketing | NOW |
| 9 | [copy-editing](https://github.com/coreyhaines31/marketingskills/tree/main/skills/copy-editing) | Remove AI-sounding copy | Marketing | NOW |
| 10 | [seo-audit](https://github.com/coreyhaines31/marketingskills/tree/main/skills/seo-audit) | Titles, sitemap, technical SEO | Marketing | NOW |
| 11 | [content-strategy](https://github.com/coreyhaines31/marketingskills/tree/main/skills/content-strategy) | Keyword-driven editorial calendar | Marketing | NOW |
| 12 | [video](https://github.com/coreyhaines31/marketingskills/tree/main/skills/video) | Storyboards & shot lists; not on-box generation | Marketing | NOW |
| 13 | [image](https://github.com/coreyhaines31/marketingskills/tree/main/skills/image) | Creative planning, alt text | Marketing | LATER |
| 14 | [schema](https://github.com/coreyhaines31/marketingskills/tree/main/skills/schema) | Organization/software JSON-LD | Marketing | LATER |
| 15 | [ai-seo](https://github.com/coreyhaines31/marketingskills/tree/main/skills/ai-seo) | AI answer visibility | Marketing | LATER |
| 16 | [site-architecture](https://github.com/coreyhaines31/marketingskills/tree/main/skills/site-architecture) | EN/PT program pages | Marketing | NOW |
| 17 | [cro](https://github.com/coreyhaines31/marketingskills/tree/main/skills/cro) | Demo-request conversions | Marketing | NOW |
| 18 | [signup](https://github.com/coreyhaines31/marketingskills/tree/main/skills/signup) | Frictionless parent signup | Both | NOW |
| 19 | [onboarding](https://github.com/coreyhaines31/marketingskills/tree/main/skills/onboarding) | First-week activation | Manager | NOW |
| 20 | [pricing](https://github.com/coreyhaines31/marketingskills/tree/main/skills/pricing) | Fair family pricing after pilot | Manager | LATER |
| 21 | [referrals](https://github.com/coreyhaines31/marketingskills/tree/main/skills/referrals) | Parent-to-parent recommendations | Manager | LATER |
| 22 | [co-marketing](https://github.com/coreyhaines31/marketingskills/tree/main/skills/co-marketing) | Parent groups & educator partnerships | Manager | NOW |
| 23 | [analytics](https://github.com/coreyhaines31/marketingskills/tree/main/skills/analytics) | Opt-in funnels and activation | Manager | NOW |
| 24 | [churn-prevention](https://github.com/coreyhaines31/marketingskills/tree/main/skills/churn-prevention) | Track failed onboarding, dropoff | Manager | LATER |

Additional real projects to evaluate **off-box or as on-demand clients**, not 6 more always-on daemons:

| # | Project | Why useful | Hardware fit |
|---:|---|---|---|
| 25 | [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) | Profiles, cron, remote models, skills | **Base runtime**; test on Atom |
| 26 | [AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo) | Deep audits; optional scripts and subagents | **Use selected text procedures only** |
| 27 | [knadh/listmonk](https://github.com/knadh/listmonk) | Opt-in newsletter tool; requires PostgreSQL | **Not for 2GB pilot**; later VPS |
| 28 | [FFmpeg/FFmpeg](https://github.com/FFmpeg/FFmpeg) | Render simple captions/slides/short clips | **Optional short overnight renders** |
| 29 | [caronc/apprise](https://github.com/caronc/apprise) | One-way alerting for lead replies/approvals | **Optional** lightweight notifications |
| 30 | [AnswerDotAI/llms-txt](https://github.com/AnswerDotAI/llms-txt) | Proposed machine-readable website guide | **Optional**; not substitute for SEO |

**Not recommended for these Atom machines:** self-hosted Postiz (multiple services), n8n full workflow runtime, video diffusion, browsers running continuously, large RAG embeddings, scraping botnets or unofficial Instagram credential automators. For Instagram publishing use Meta's official Graph API with approved Professional account permissions. For Reddit, API restrictions changed in 2026; prefer **manual contributions** or a fully authorized developer integration, never a promotional posting swarm.

A toolkit's open-source license does not grant permission to automate third-party accounts. Review licenses, dependencies, API and platform terms before activating anything.
