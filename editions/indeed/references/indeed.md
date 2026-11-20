# Indeed-specific prototype

This is a separate product prototype, not a live integration. It preserves the original profile/job/selection schema. It does not access Indeed, install software, send data, upload resumes, fill a browser, or submit applications.

## PDF
`python scripts/career.py resume-pdf --profile profile.json --job job.json --selection selection.json --out resume.pdf`

Requires ReportLab in the execution environment. The original helper's other commands remain standard-library only. Output is a clean text-based resume with category sections containing only selected confirmed statements, with no invented name/contact details. It is an evidence resume, not a full chronology parser. Add explicit candidate identity/contacts in a later reviewed, consented document workflow; do not infer them. Unsupported Unicode fails closed rather than silently corrupting text. ReportLab bundled Vera fonts are embedded; the conservative cp1252 check rejects other scripts. Broader internationalization remains untested. PDF output is local, so Agensi binary-serving restrictions still apply.

## Assisted autofill plan
`python scripts/career.py indeed-plan --profile profile.json --job job.json --selection selection.json --form form.json --out plan.json`

Form schema: `url` (HTTPS allowed Indeed origin), `job_id`, `fields` array. Each field requires unique `id`, exact visible `label`, `kind`, `fact_id` (or null), and boolean `confirmed`. Kinds: qualification, contact, sensitive, legal, screening, upload, unknown.

Only a confirmed qualification mapping to an already-selected confirmed fact proposes an exact value. Every other field is manual. No answers are inferred from an apparently similar field. Form mapping must be produced from the currently visible page, not guesses; supplied mappings are not authenticated proof. The helper validates data shapes and reference gates, not question semantics. A field mislabeled qualification can still be inappropriate, so the assistant must review the actual question and proposed answer.

## Manual application boundary
The person supplies copied job/form information. This edition does not inspect browser sessions or fill, upload, click, send or submit anything. Review the local proposed answers and PDF, then the person enters answers and uploads/submits manually on the intended site. Keep sensitive/legal answers manual. No scraping, sign-in handling, CAPTCHA handling, redirects or bulk applications are supported.

The URL check validates the supplied string only. It does not verify that a posting exists, that a browser is on that page, or that an answer is semantically appropriate. Live Indeed layout, policies, uploads and autosave behavior have not been tested. Not affiliated with Indeed.

