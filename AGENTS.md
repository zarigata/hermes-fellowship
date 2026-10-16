# Repository development

This repository is a Hermes integration starter, not a trained agent or installed production service.
Keep runtime dependencies in the Python standard library. Target Linux/macOS and Windows through WSL.
Read docs/ORCHESTRATION.md before changing delegation or profile selection.
Never invent Hermes CLI flags or claim profiles isolate OS credentials.
Keep task text out of shell expressions; subprocess calls must use argument lists and stdin.
Preserve existing profiles and fail closed on unknown run outcomes.
Run `python3 -m unittest discover -s tests -v` after launcher changes.
Do not commit credentials, runtime transcripts, screenshots, provider settings or personal memories.
