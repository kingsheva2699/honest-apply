# Contributing to honest-apply

Thanks for helping! The project has one rule above all others:

> **The tool must never make a job seeker look more qualified than they are.**

Every feature should make applications faster *or* more accurate, never less honest.

## Good first contributions
- New resume layouts (keep them ATS-friendly: real text, no tables for layout, one column).
- A reply tracker (Gmail API or IMAP) that classifies employer emails and calls `apply.py outcome`.
- Job-fit scoring against `facts.yaml` and a targets file.
- `.docx` output.
- Better negation detection in `check_spec` (with tests for false positives and false negatives).
- Translations of the example profile and the agent workflow.

## How to contribute
1. Fork and create a branch.
2. `pip install -r requirements.txt pytest` and run `pytest`.
3. Add tests for any change to the honesty check.
4. **Never commit real personal data.** Use the fictional example person.
5. Open a pull request describing what changed and why.

## Reporting problems
Open an issue. If the check let a false claim through, that's a high-priority bug,
so please include the (anonymized) spec that slipped past it.
