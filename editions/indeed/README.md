# Honest Apply: Indeed preparation
An offline candidate-side application preparation prototype. It starts with an empty profile and copies only selected confirmed fact statements into drafts. It does not connect to Indeed or submit applications.

## Included
- Reviewed evidence bank, role comparison, HTML/text drafts and portable setup exports.
- Optional local evidence résumé PDF using ReportLab.
- An offline form-answer plan from user-supplied mappings. Only selected confirmed qualification facts receive proposed exact text; other fields stay manual.

## Run and test
Python 3.10+. Core commands need no extra packages. For PDF generation: `python -m pip install -r requirements-pdf.txt`. For the complete tests: `python -m pip install -r requirements-test.txt`, then `python -m unittest discover -s tests -v`.
See SKILL.md and references/workflow.md for schemas; references/indeed.md covers PDF and offline planning. Keep all real inputs and outputs outside this package.

## Limits
No scraping, live browser adapter, login, upload, submission, external sends, billing or autonomous job selection. A confirmation flag is not authenticated consent; the helper does not verify truth, mapping semantics, source freshness or eligibility. PDF output is an evidence draft, not a complete identity/contact/work-chronology résumé. Non-cp1252 text is rejected; native Claude, Indeed and marketplace end-to-end operation have not been certified. The user manually reviews, uploads and submits.

## Provenance and license
A separate strict prototype inspired by the public honest-apply repository, initially inspected at fa5f2eacc9e79837ecbd65d844085b0971d255db on November 17, 2026. It is not a drop-in replacement for the public apply.py schema. MIT attribution is retained in LICENSE. No real candidate facts, credentials, records or private configuration are included. Not affiliated with Indeed or Anthropic.
