# honest-apply

A small, human-in-the-loop job application kit for people who use an AI agent
(such as Claude) to help them apply for jobs, **without the agent making
things up.**

Most auto-apply tools optimize for volume. This one optimizes for applications
you'd be comfortable defending in an interview:

- **Locked fact bank.** Resume bullets can only come from `profile/facts.yaml`,
  your own list of true statements. Rewording a bullet into a new claim is blocked.
- **Honesty check before anything is built.** `apply.py check` blocks packages
  that claim things on your `never_claim` list (a degree, a tool you've never
  used, a title you didn't hold), unless the sentence is a negation such as
  *"I don't have a degree."* It also catches **stale cover letters** that still
  name a company from an earlier application.
- **Answer bank for screener questions.** The agent answers from
  `profile/answers.md` word for word, and treats job-board autofill as
  untrusted. Boards often pre-fill answers from your previous applications, and
  sometimes those answers are wrong.
- **You press Submit.** The agent never submits, never solves CAPTCHAs, never
  types passwords, and leaves legal questions (criminal record, etc.) to you.
- **Tracking that teaches you something.** `apply.py stats` shows your interview
  rate by role type and by source, so you can stop spending time where no one replies.

Why this matters: job boards often pre-fill screener answers and cover-letter
boxes from your earlier applications, and an agent moving quickly can pass a
wrong answer (or another company's letter) straight through. The checks here
exist to catch exactly that.

## Quick start

```bash
git clone https://github.com/kingsheva2699/honest-apply && cd honest-apply
pip install -r requirements.txt
playwright install chromium        # PDF rendering (or: pip install weasyprint)

python apply.py check jobs/example_harbourview.json    # try it on the fictional example first
python apply.py init                                   # set up YOUR profile (a short interview)
```

`init` asks about your contact details, education, each job and what you
actually did there, the skills you really use, things you must never claim,
the jobs you want, and your standard screener answers. It writes three files:

| File | What's in it |
|---|---|
| `profile/facts.yaml` | Your true facts: contact, work history as bullets, skills, education, and the `never_claim` list |
| `profile/answers.md` | Your exact answers to common screener questions |
| `profile/targets.md` | Roles you want (in priority order), location, pay floor, deal-breakers |

Prefer to do it with an AI agent? Say *"set me up"*. The agent runs the same
interview in chat, or drafts your profile from your current resume and has you
confirm every line before it's saved.

Your `profile/`, `data/`, `jobs/` and `out/` contents are git-ignored (only the
examples are tracked), so your personal information never ends up in a commit.

## Using it with an AI agent

`skills/job-application/SKILL.md` is a step-by-step workflow an agent follows:
set up your profile the first time → pick one job → screen it → write a job spec → `build` (which runs `check`) →
optionally fill the form in the browser → hand off to you → log it.

- **Claude (desktop or Claude Code):** add the folder as a skill, or point the agent at `SKILL.md`, then say *"next application"*.
- **Other agents:** the workflow is plain Markdown and the tools are a single Python script, so it works anywhere an agent can run shell commands.

One application per conversation keeps the agent focused and cheap.

## Commands

| Command | What it does |
|---|---|
| `python apply.py init` | First-time setup interview; writes your profile files |
| `python apply.py check jobs/x.json` | Honesty check only |
| `python apply.py build jobs/x.json` | Check, then build resume + cover letter (HTML, PDF, plain-text letter) |
| `python apply.py seen "Acme"` | Already applied to or screened out of this company? |
| `python apply.py done "Acme" "Title" --source indeed --category service` | Log a submitted application |
| `python apply.py skip "Acme" "Title" "needs fluent French"` | Log a screened-out job |
| `python apply.py outcome "Acme" interview` | Record a reply: `interview`, `rejected`, `offer`, `no_response`, `withdrawn` |
| `python apply.py stats` | Interview rate overall, by category and by source, plus stale applications to follow up on |

## ⚠️ Important warnings

- **Browser form-filling may break job-board rules.** Some job boards prohibit
  automating their apply flow. Indeed's terms, for example, prohibit automating
  Indeed Apply outside its official tools. If your agent fills those forms, your
  account could be restricted. The form-filling step in `SKILL.md` is optional
  and off unless you choose it. The safer path is to let the agent prepare
  everything, then paste the answers yourself (about 3 minutes).
- **You are responsible for what you submit.** Read the review page before you press Submit.
- **Volume isn't the goal.** Published 2026 data suggests interview rates fall as
  application counts rise (roughly 7% for people sending 21-50 applications vs.
  about 2.6% at 100+), and referrals convert far better than cold applications.
  Use the time this saves for follow-ups and talking to people.
- Not affiliated with, or endorsed by, any job board or AI company.

## Project layout

```
apply.py                      the whole toolkit (check, build, tracking)
profile/facts.example.yaml    example fact bank (fictional person)
profile/answers.example.md    example screener answer bank
jobs/example_harbourview.json a job spec that passes the check
jobs/example_bad.json         a job spec that fails it (on purpose)
skills/job-application/       the agent workflow
tests/                        pytest tests for the honesty check
```

## Contributing

Ideas that would help a lot: more resume layouts, a Gmail/IMAP reply tracker
that feeds `apply.py outcome`, job-fit scoring, `.docx` output, more languages,
and better negation handling in the check. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
