# Cross-reference prompts

This folder holds self-contained prompts for evaluation by other
AI platforms. Drop a prompt into a fresh chat and ask for critique,
comparison, extension, or deep research.

All prompts target the repo state at tag `v0.3.0-negative`. If the
repo is updated past that tag, regenerate the prompts by editing
the verdict section.

| file | audience | focus |
|------|----------|-------|
| `THESIS_SUMMARY_PROMPT.md` | theory-oriented models | claim, evidence, prior art, verdict |
| `CODE_COMPARISON_PROMPT.md` | code-oriented models | implementation quality, ISA design, bugs |
| `DEEP_RESEARCH_PROMPT.md` | web-research-capable models | prior art survey, missing citations, related work |

The prompts are designed to be **standalone**: they don't require
the responder to fetch the repo, though pointers are included for
readers who want to dig deeper.
