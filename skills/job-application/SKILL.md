---
name: job-application
description: Use when the user says "next application" or asks to find a job and apply. Runs one honest, tailored application per conversation with the honest-apply kit (fact bank, honesty check, answer bank, tracker), and stops before the final Submit.
---

# Next application - one honest application per conversation

Goal: take ONE job from search to a filled-in, checked application, then hand
it to the user to submit. Never hand back a half-filled form. Keep tool output
small and batch shell work.

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
2. Resume bullets are picked from the fact bank (by index or close match).
   Do not reword bullets to mirror the posting; `apply.py check` blocks it.
3. Every package must pass `python apply.py check` before it is used.
4. Job-board autofill is untrusted. Boards pre-fill answers and cover-letter
   boxes from earlier applications. Read every field on every page and correct
   it against `answers.md` before pressing Continue.
5. Degree/diploma questions get exactly the answer in `answers.md`.
6. Criminal-record, background, medical and legal questions are answered by the
   user. Fill everything else first, then name the remaining questions and stop.
7. Never solve CAPTCHAs or bot checks, never type passwords or one-time codes,
   never create accounts. Ask the user to do those, then continue.
8. Never press the final Submit / Send button. The user does.
9. Never click "Apply anyway" past a qualification warning without the user's yes.
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

## Step 4 - fill the application (optional: browser automation)
> WARNING. Some job boards' terms prohibit automated filling of their apply
> forms (for example, Indeed's terms prohibit automating Indeed Apply outside
> its official tools). Using this step can get the user's account restricted.
> Tell the user this once and only do it if they choose to. The alternative is
> to give them the PDF, the letter text and a list of answers to paste.

If the user wants it:
1. Open the application form. If a sign-in page, CAPTCHA or bot check appears, stop and ask the user.
2. Resume step: upload `out/<short>/<short>_Resume.pdf` via the file input; confirm the filename shows.
3. Every questions page: (a) list each field's current value, (b) correct all of
   them from `answers.md`, including pre-filled ones, (c) list again, then Continue.
4. Cover letter: clear the box completely (it may hold an old letter), paste
   `out/<short>/letter.txt`, confirm the character count and that no other
   company name remains.
5. Review page: read every answer once more. Do not press Submit.

## Step 5 - hand off
Tell the user: company, title, pay, location, what was filled, any corrections
made to autofill, honest gaps, and which questions (if any) they must answer.
Ask them to submit and reply "done".

## Step 6 - after "done"
Confirm the confirmation page if you can see it (never guess). Then
`python apply.py done "<Company>" "<Title>" --source <board> --category <role type>`
and remove the job from `QUEUE.md`.

## Weekly
- `python apply.py stats` - response rate by category and source; put effort where replies come from.
- Record replies with `python apply.py outcome "<Company>" interview|rejected|offer|no_response`.
- Send a thank-you within 24 hours of every interview, and follow up on interviews with no news after a week.
