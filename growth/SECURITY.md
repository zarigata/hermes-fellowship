# Trust boundaries and legal checklist

1. **Human approval:** external publishing, sending mail, creating accounts, spending money, and contacting new people require explicit approval and appropriate platform authorization. No bulk-send command. A drafting approval is not blanket permission for outreach.
2. **No access to minors' data:** Marketing sees no student records, family identifiers, assessment results, grades, screenshots or personal data. Consent to use the education platform is not consent for marketing profiling.
3. **Manager isolation:** Dedicated business email credential only on manager machine; use provider-approved SMTP/OAuth and minimum scoped access. Marketing gets approved product facts/creative briefs, never cookies, session tokens or passwords.
4. **No synthetic social identities:** Never create fake parent accounts, fake testimonials, manipulated reviews, or undisclosed endorsements. A person should complete account registration and CAPTCHA or identity verification.
5. **Reddit:** Community rules and Reddit's Responsible Builder Policy apply. In 2026 Reddit announced the public bot/API move to Developer Platform / Devvit, with changes in early 2027. Do not assume PRAW/new API clients can post freely. Manual helpful participation first.
6. **Instagram:** Official Meta API generally requires Professional access, authorization and permissions. Personal-account login scripts and private endpoints are not production-safe. Drafts can be generated locally before any publisher is configured.
7. **Email:** For US commercial messages follow FTC CAN-SPAM requirements including truthful header/subject, identity, postal address and opt-out handling; other regions may require opt-in (e.g., EU GDPR/ePrivacy, Brazil LGPD). Seek review for actual jurisdictions.
8. **Child privacy:** FTC COPPA and Brazil LGPD art. 14 require special treatment of children's data; never reuse it for prospecting or model prompts. Provide deletion, retention and access policies before pilots.
9. **Secret management:** no keys in Git, logs, email drafts, markdown exports or USB handoffs. Back up encrypted. Set owner-only permissions on DB and .env. Rotate credentials if leaked.
10. **Prompt injection:** webpages, inbox messages and PDFs are untrusted. Retrieved text cannot authorize an action, change target recipients, expand contact quotas or request secret disclosure.
11. **Safety at rest:** SQLite in an owner-only directory; encryption at rest via full-disk encryption if device can support it. Do not publicly expose SQLite files or a web dashboard.
12. **Audit trail:** timestamp every lead/draft/approval/send and opt-out. Keep a suppression table; delete records when retention purpose expires. No silent automatic retries of an email after uncertain SMTP response.
13. **OS:** unprivileged service account, SSH keys, automatic security updates if available, firewall inbound default deny, disk+log rotation, UPS if needed, encrypted offline backup.
14. **Model data:** remote model inference sends what you prompt to provider; transmit public marketing information only. Do not paste nonpublic parent/student info.
15. **Quotas:** add daily spend/outreach limits and stop on errors, bounce, complaint, missing approval or uncertain platform permission.

Primary references:
- Reddit Responsible Builder: https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy
- Reddit Nov 10 2026 API migration: https://support.reddithelp.com/hc/en-us/articles/55472297340308-Changelog-November-10-2026
- Reddit spam: https://support.reddithelp.com/hc/en-us/articles/360043504051-Spam
- Meta Instagram official API: https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api
- FTC CAN-SPAM: https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business
- FTC COPPA: https://www.ftc.gov/business-guidance/resources/complying-coppa-frequently-asked-questions
- LGPD: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709compilado.htm
- STF Tema 822: https://portal.stf.jus.br/jurisprudenciaRepercussao/verAndamentoProcesso.asp?classeProcesso=RE&incidente=4774632&numeroProcesso=888815&numeroTema=822
