# Local workflow and schema

Create a private working folder outside the distributable skill. No default candidate data, example qualifications, credentials or outbound network operations are included. The helper does not read the original honest-apply profile or environment variables.

```
python /path/to/honest-apply-claude/scripts/career.py init /private/work/profile.json
python /path/to/honest-apply-claude/scripts/career.py assess --profile /private/work/profile.json --job /private/work/job.json --out /private/work/fit.json
python /path/to/honest-apply-claude/scripts/career.py prepare --profile /private/work/profile.json --job /private/work/job.json --selection /private/work/selection.json --out /private/work/draft-v1
```

Each command refuses to overwrite an existing output. `init` writes only empty arrays. Use new versioned output names when inputs change. Preparation reads the current profile/job and recomputes fit; stale reports are not reused. The helper has no browser, mail, API, account, upload, purchase or submit command.

## Profile
Root: `schema_version` must be 1, `facts` and `preferences` arrays. No name or demographic fields are permitted in this assessment schema. Any personal data voluntarily entered into free text is still personal data: exclude it from distributable packages and unnecessary analysis.

Fact fields (all required):
- `id`: unique stable string.
- `statement`: exact candidate-confirmed assertion; never manufacture it.
- `source`: origin such as a user statement or reviewed résumé passage. Avoid storing unnecessary document contents or private URLs.
- `confirmed`: boolean; false until the person actually confirms.
- `category`: experience, skill, education, credential or project.

Preference fields: `id`, `statement`, `source`, `confirmed`. No default salary, commute, location, mobility, work arrangement, authorization or credentials. Ask whether relevant preferences are hard constraints or flexible; preserve their wording.

## Job
Required root fields: `id`, `company`, `title`, `source`, `checked_at`, `requirements`, `preference_matches`. `checked_at` is the observed check timestamp; the script does not fetch or verify the posting. At least one requirement must be reviewed. Sources may be a posting URL or a clearly labelled user-provided document; the helper never opens them.

Each requirement: `id`, `text` (posting criterion), `kind` (required/preferred), `status` (supported/gap/unknown), `fact_ids` (array), `rationale` (why evidence does or doesn't establish it), `reviewed` (boolean). Supported and gap both require evidence IDs. Unreviewed or unconfirmed mappings become unknown. The software checks structure/reference integrity, not whether a fact semantically proves a requirement. Human review is essential.

Preference matches: `preference_id`, `status` (match/conflict/unknown), `posting_quote`, `reviewed`. A known match/conflict requires a source quote. Unassessed preferences are explicitly returned and never treated as a match.

## Selection
Fields: `job_id`, `user_selected` (true only after actual choice), `reviewed_issues` (IDs of required gaps/unknowns or preference conflicts the user discussed), `resume_fact_ids`, `letter_fact_ids`. Both fact arrays must be nonempty and reference confirmed facts. Reviewing an issue is not claiming the requirement is met. The helper can prepare a stretch-role draft after review; no automatic rejection or false success is implied.

Output: application-draft.html, cover-letter-starter.txt, fit-review.json, review-manifest.json. The manifest hashes input content to identify which version was used; it is not a signature, consent system or delivery receipt. Fit details are separate private review material, not meant to be sent to an employer. A final letter can be refined by Claude under the skill's confirmation requirements.

## End-to-end orchestration
Claude conducts intake, proposes role hypotheses, researches postings when authorized, constructs evidence mappings for user review, runs deterministic assessment, records selection and generates drafts. This is a full staged workflow, not a magical standalone script that deduces a career from nothing. It intentionally stops for missing evidence, human choices and final submission. No paid AI API is required by the helper.
