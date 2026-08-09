# Cross-reference prompts

This folder holds self-contained prompts that package the BT-IS
thesis for evaluation by other AI platforms. Drop a prompt into a
fresh chat and ask for critique, comparison, or extension.

Both prompts target the repo state at tag `v0.2.0-niche`. If the
repo is updated past that tag, regenerate the prompts by editing
the dates and the verdict section in
`THESIS_SUMMARY_PROMPT.md`.

| file | audience | focus |
|------|----------|-------|
| `THESIS_SUMMARY_PROMPT.md` | theory-oriented models | claim, evidence, prior art, verdict |
| `CODE_COMPARISON_PROMPT.md` | code-oriented models | implementation quality, ISA design, bugs |

The prompts are designed to be **standalone**: they don't require
the responder to fetch the repo, though pointers are included for
readers who want to dig deeper.
