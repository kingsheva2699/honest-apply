# Honest Apply

Prepare tailored résumés and cover letters from experience you can back up. Honest Apply is an open-source Python toolkit and AI-agent workflow. It helps you start from a fact bank you confirm, catch common errors, and keep track of applications. **You review the package and submit it yourself.**

## What it does

- **Reuse your experience.** Keep confirmed work history, skills, and education in `profile/facts.yaml`. Select existing résumé bullets by zero-based integer index or exact text under the same experience ID. Changed wording or quantities are rejected, even with `build --force`.
- **Check a draft before building.** `apply.py check` flags some prohibited terms, unmatched bullets, leftover placeholders, and references to other companies in your application log. It warns if a nonempty letter appears not to mention the current company.
- **Build application files.** `apply.py build` generates résumé and cover-letter HTML plus a plain-text cover letter. It also generates PDFs when a supported renderer is available.
- **Keep answers and outcomes organized.** Store approved screener answers separately and log applications and outcomes manually. `apply.py stats` summarizes current recorded outcomes by role category and source. It does not read your inbox or preserve a separate history of status changes.

## What the checks can miss

**A passing check does not mean every claim is true.** Free-text résumé sections and letters get keyword and pattern checks, not verification against your experience. Selected bullets must match the fact bank exactly; for example, changing “60 appointments” to “600 appointments” is rejected. This checks consistency with your saved facts, not whether those facts are true. The old `bullet_match_threshold` setting is ignored. The letter check can also miss an incorrect company if that name is not in your application log.

Use bullet indices where possible. Before sending anything, compare facts, numbers, dates, employer names, and screener answers with your original information.

## Quick start

```bash
git clone https://github.com/kingsheva2699/honest-apply
cd honest-apply
python -m pip install -r requirements.txt

# On a fresh checkout, these use the fictional example profile.
python apply.py check jobs/example_harbourview.json
python apply.py check jobs/example_bad.json  # Expected to fail

# Set up your own profile before preparing real applications.
python apply.py init
```

For PDF output, run `python -m playwright install chromium` or set up WeasyPrint as an alternative. Review the rendered résumé and cover letter before using them.

`init` writes three local files:

| File | Contents |
|---|---|
| `profile/facts.yaml` | Your contact details, experience, skills, education, and terms to watch for |
| `profile/answers.md` | Your answers to common screening questions |
| `profile/targets.md` | Target roles, location, minimum pay, and deal-breakers |

Personal working files in the default profile, data, jobs, and output folders are ignored by Git, with the fictional examples tracked. Check what is staged before committing. Sharing files with an AI agent or another service is a separate choice; Git exclusions do not control its access or retention.

## Editions and automatic selection

| Edition | When it is selected |
|---|---|
| [Core toolkit](skills/job-application/SKILL.md) | Python available, default workflow for OpenAI, other, and unknown model families |
| [Claude](editions/claude/README.md) | Python available and a Claude host or model is identified, unless Indeed is selected |
| [Indeed preparation](editions/indeed/README.md) | Python available and the application is for Indeed, regardless of model |
| [Manual checklist](editions/manual.md) | The AI host cannot run Python |

Give your agent [the start workflow](WORKFLOW.md) to route automatically. If you are using the command line yourself, for example:

```bash
python select_workflow.py --model claude-sonnet-4-5
python select_workflow.py --model gpt-5 --board indeed
python select_workflow.py --model gpt-5 --board linkedin
```

Use `--host claude` or `--host other` if the host is known, or open the manual checklist directly in a text-only chat. The selector only reports which local files to use. It doesn't launch an agent or infer hidden model identities. Keep each edition's local data separate; profiles are not interchangeable. Use these editions for preparation only; LinkedIn and Indeed applications are filled and submitted by you.

## Using it with an AI agent

For the core edition, give a shell-capable agent the [job application workflow](skills/job-application/SKILL.md) and work on one application at a time. Review any facts it extracts from an existing résumé before saving them to your profile. The Python toolkit prepares files and tracks outcomes; it does not browse job boards, fill forms, or submit applications. Agent support depends on the tools and permissions available in that agent.

The safest path is to use the toolkit to prepare the files, then fill and review the application yourself. None of the included workflows automates a job board’s live application form. Verify any prefilled answers, handle sensitive or legal questions yourself, and press **Submit** only after your own review. This project is not affiliated with or endorsed by any job board or AI provider.

## Commands

| Command | What it does |
|---|---|
| `python apply.py init` | Set up your profile |
| `python apply.py check jobs/x.json` | Check a job spec without building files |
| `python apply.py build jobs/x.json` | Check and build a résumé and cover letter |
| `python apply.py seen "Acme"` | Check whether a company is in your application or screening log |
| `python apply.py done "Acme" "Title" --source indeed --category service` | Log an application you submitted |
| `python apply.py skip "Acme" "Title" "needs fluent French"` | Log a job you screened out |
| `python apply.py outcome "Acme" interview` | Update a recorded outcome |
| `python apply.py stats` | Summarize current application outcomes |

See [Contributing](CONTRIBUTING.md) and the [MIT license](LICENSE).

