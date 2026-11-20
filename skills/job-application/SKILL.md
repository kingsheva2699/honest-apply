---
name: job-application
description: Use when the user says "next application" or asks to find a job and apply. Runs one honest, tailored application per conversation with the honest-apply kit (fact bank, honesty check, answer bank, tracker), and stops before the final Submit.
---

# Next application - one honest application per conversation

Goal: prepare ONE checked application package and hand it to the user to fill and submit. Do not operate live application forms.

## Files (paths relative to the kit folder)
- `profile/facts.yaml` - the user's only source of truth for resume content.
- `profile/answers.md` - screener answers, used word for word.
- `profile/targets.md` (optional) - target roles in priority order, location, pay floor, deal-breakers.
- `data/QUEUE.md`, `data/applied.csv`, `data/screened_out.csv`, `data/LOG.md`.
- `jobs/<short>.json` - one spec per job. `out/<short>/` - built resume, letter, PDFs.

## Hard rules (never break these)
1. Facts only from `facts.yaml`, `answers.md`, or what the user says in this chat.
   Never invent a degree, licence, tool, title, number or duty. If a posting
   wants something the user lacks, say so honestly in the letter.
2. Resume bullets are picked from the fact bank (by zero-based integer index or exact text within that experience).
   Do not reword bullets to mirror the posting; `apply.py check` blocks it.
3. Every package must pass `python apply.py check` before it is used.
4. Remind the user to compare any job-board prefilled answers with the reviewed answer list.
5. Degree/diploma questions get exactly the answer in `answers.md`.
6. The user answers criminal-record, background, medical and legal questions themselves. Do not guess or collect those answers.
7. Never solve CAPTCHAs or bot checks, never type passwords or one-time codes,
   never create accounts. Ask the user to do those, then continue.
8. The user fills, uploads files to, and submits the live application themselves.
9. Flag qualification warnings without advancing the application.
10. New facts the user states go into `facts.yaml` or `answers.md` (ask first).

## Step 0 - first-time setup (only if `profile/facts.yaml` does not exist)
Do not search or apply until the profile exists. Interview the user in chat,
a few questions at a time, and write only what they tell you:
1. Offer a shortcut: "If you have a current resume, share it and I'll draft your
   profile from it." If they share one, extract each job and bullet, then show
   the list and ask them to confirm, fix or delete each line. A resume they
   wrote can still contain stretches; only confirmed lines go in.
2. Otherwise ask, in this order: name and contact details (city, phone, email,
   optional link); work authorization; education (and plainly: "Do you have a
   college diploma or degree?"); each job (company, title, dates, what they
   actually did); skills and tools they really use.
3. Build `never_claim` together: suggest common ones (degree, diploma,
   certifications, licences, languages, software they haven't used,
   supervisor/managed a team) and keep every one they don't truly have. Add anything they mention.
4. Targets: roles in priority order, location/commute, pay floor, deal-breakers.
5. Standard screener answers: work authorization, sponsorship, driver's licence,
   vehicle, start date, salary (digits and range), weekends, and exact numbers
   they're comfortable stating (years with Excel, etc.).
6. Write `profile/facts.yaml` (same structure as `facts.example.yaml`),
   `profile/answers.md` and `profile/targets.md`, show a short summary, and ask
   them to confirm before the first application.
Users without an agent can run `python apply.py init`, which asks the same questions.

## Step 1 - read state (1 shell call)
`cat data/QUEUE.md; tail -5 data/LOG.md; cat profile/answers.md; cat profile/targets.md 2>/dev/null`

## Step 2 - pick the job
- Employer invitations to apply (e.g. job-board "invited to apply" notifications) go first.
- Else the top line of `QUEUE.md`.
- Else search (job-board connector or browser), 3-5 queries from `targets.md`,
  postings from the last ~14 days. Run `python apply.py seen "<Company>"` and
  skip anything not NEW. Read at most 3 postings in full.
- Screen out hard requirements the user lacks (required degree, licence,
  vehicle, language, N years in a field they don't have, pay under the floor,
  sign-up-only application sites). "Preferred"/"asset" is fine.
- Record fits in `QUEUE.md`; record screen-outs with `python apply.py skip "<Company>" "<Title>" "<reason>"`.

## Step 3 - build the package
Write `jobs/<short>.json`:
```json
{"company": "...", "title": "...", "short": "Acme",
 "headline": "...", "profile": "2-3 sentences, facts only",
 "bullets": {"<experience id>": [1, 0, 3]},
 "skills": "optional override",
 "letter": ["why this role", "evidence from the fact bank", "honest gaps + close"]}
```
Then `python apply.py build jobs/<short>.json`. Expect `OK <short> ... resume_pages=1`.
If it prints BLOCK lines, fix the spec (never use `--force` without the user's yes).
Invalid bullet selections cannot be overridden with `--force`; confirm any genuine new fact with the user and update the fact bank first.

## Steps 4–5 - human handoff
Give the user the résumé, cover-letter text, and a list of answers they approved.
Note missing facts, unresolved questions, and any employer or qualification
warnings. Do not interact with live application forms, including LinkedIn or
Indeed. The user opens, fills, reviews, and submits the application themselves.
Ask them to reply "done" after submitting.

## Step 6 - after "done"
Use the user’s confirmation or a receipt they supply; never assume submission. Then
`python apply.py done "<Company>" "<Title>" --source <board> --category <role type>`
and remove the job from `QUEUE.md`.

## Weekly
- `python apply.py stats` - response rate by category and source; put effort where replies come from.
- Record replies with `python apply.py outcome "<Company>" interview|rejected|offer|no_response`.
- Suggest a thank-you or follow-up draft when helpful. Do not send it.

