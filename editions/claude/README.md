# Honest Apply — Claude parallel

A separate candidate-side career exploration and application-preparation skill. The original repository and existing Hermes/Claude workflows are untouched. This edition starts empty and never assumes the author's identity, career history or preferences.

## What works
- Guided intake and evidence-grounded role discovery instructions for Claude.
- Offline Python validation and fit matrix: supported, gap and unknown stay distinct.
- User-selected, exact-confirmed-fact application drafts, cover-letter starters and provenance manifest.
- No external accounts, networking, submission or hidden model calls.

See SKILL.md and references/workflow.md. Python 3.10+; no packages to install. Run tests with `python -m unittest discover -s tests -v` from this directory. Tests use synthetic nonpersonal statements only, never an actual candidate profile.

## Limits
The helper cannot verify truth or authenticate approval flags, automatically discover someone's ideal career, fetch job ads, or certify eligibility. Claude orchestrates those review stages with the person. Draft HTML/text is not a fully formatted PDF/DOCX résumé. Native Claude runtime and Agensi delivery need separate end-to-end acceptance testing before selling with compatibility guarantees. No listing or installation has been performed.

## Provenance
Workflow adapted from the publicly available honest-apply project at https://github.com/kingsheva2699/honest-apply, inspected at commit fa5f2eacc9e79837ecbd65d844085b0971d255db on November 17, 2026. The original MIT license and required copyright attribution are retained in LICENSE. Public author attribution is not a candidate identity. The helper is a new stricter parallel implementation, not a copy of the original fuzzy checker or its fictional profile fallback. No original example profiles, application records, private facts or local configuration are included.

## Subscription-oriented setup
The first run can export a user-owned editable career setup document and JSON data companion with `setup-doc`. The separate workflow skill can support monthly ongoing usage, but pricing and billing are not implemented, and instructions cannot be guaranteed secret. Cancellation must not remove the user's exported data or earlier application outputs. See references/subscription-boundary.md.
