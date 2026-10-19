#!/usr/bin/env python3
"""honest-apply: a small, human-in-the-loop job application kit.

Every resume line comes from YOUR fact bank. Every package is checked for
claims you can't back up before it leaves your machine. You press Submit.

Commands
  python apply.py init                       first-time setup: answers a short interview, writes your profile
  python apply.py build  jobs/acme.json     build resume + cover letter (HTML/PDF) from a job spec
  python apply.py check  jobs/acme.json      honesty check only (no files written)
  python apply.py seen   "Acme"              already applied to / screened out of this company?
  python apply.py done   "Acme" "Title" [--source indeed] [--category service] [--note "..."]
  python apply.py skip   "Acme" "Title" "reason"            record a screened-out job
  python apply.py outcome "Acme" interview|rejected|offer|no_response [--note "..."]
  python apply.py stats                      response rates overall, by category and by source
  python apply.py queue                      show QUEUE.md

Paths can be changed with environment variables:
  HA_PROFILE (default: profile/facts.yaml, falls back to profile/facts.example.yaml)
  HA_DATA    (default: data/)   HA_OUT (default: out/)
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import difflib
import html
import json
import os
import re
import sys
from pathlib import Path

try:
    import yaml  # PyYAML
except ImportError:  # pragma: no cover
    sys.exit("Missing dependency: pip install pyyaml")

ROOT = Path(__file__).resolve().parent
TODAY = dt.date.today().isoformat()


def _profile_path() -> Path:
    if os.environ.get("HA_PROFILE"):
        return Path(os.environ["HA_PROFILE"])
    real = ROOT / "profile" / "facts.yaml"
    return real if real.exists() else ROOT / "profile" / "facts.example.yaml"


DATA = Path(os.environ.get("HA_DATA", ROOT / "data"))
OUT = Path(os.environ.get("HA_OUT", ROOT / "out"))
APPLIED = DATA / "applied.csv"
SCREENED = DATA / "screened_out.csv"
LOG = DATA / "LOG.md"
QUEUE = DATA / "QUEUE.md"
APPLIED_COLS = ["date", "company", "title", "source", "category", "status", "status_date", "note"]

NEGATIONS = re.compile(
    r"\b(no|not|never|without|don't|do not|haven't|have not|hasn't|lack|lacking|none|isn't|aren't|wasn't)\b",
    re.I,
)


# --------------------------------------------------------------------------- facts
def load_facts() -> dict:
    p = _profile_path()
    facts = yaml.safe_load(p.read_text(encoding="utf-8"))
    facts["_path"] = str(p)
    return facts


def bullet_bank(facts: dict) -> dict[str, list[str]]:
    return {e["id"]: list(e.get("bullets", [])) for e in facts.get("experience", [])}


# --------------------------------------------------------------------------- honesty check
def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]


def check_spec(spec: dict, facts: dict) -> tuple[list[str], list[str]]:
    """Return (errors, warnings). Errors block the build."""
    errors: list[str] = []
    warnings: list[str] = []
    banned = [b.lower() for b in facts.get("never_claim", [])]
    bank = bullet_bank(facts)
    threshold = float(facts.get("bullet_match_threshold", 0.85))

    # 1. Free text (headline, profile, skills, letter): banned claims outside a negation.
    free = {
        "headline": spec.get("headline", ""),
        "profile": spec.get("profile", ""),
        "skills": spec.get("skills", ""),
        "letter": "\n".join(spec.get("letter", [])),
    }
    for field, text in free.items():
        for sent in _sentences(text):
            low = sent.lower()
            for term in banned:
                if re.search(r"\b" + re.escape(term) + r"\b", low) and not NEGATIONS.search(low):
                    errors.append(f'{field}: claims "{term}" -> "{sent[:120]}"')

    # 2. Resume bullets must come from the fact bank (exact id or close match).
    for exp_id, bullets in (spec.get("bullets") or {}).items():
        if exp_id not in bank:
            errors.append(f'bullets: unknown experience id "{exp_id}" (not in facts)')
            continue
        for b in bullets:
            if isinstance(b, int):
                if not 0 <= b < len(bank[exp_id]):
                    errors.append(f"bullets.{exp_id}: index {b} out of range")
                continue
            best = max((difflib.SequenceMatcher(None, b.lower(), f.lower()).ratio() for f in bank[exp_id]), default=0)
            if best < threshold:
                errors.append(
                    f'bullets.{exp_id}: not in your fact bank (best match {best:.0%}) -> "{b[:100]}". '
                    "Add it to facts.yaml if it is true, or pick an existing bullet."
                )
            for term in banned:
                if re.search(r"\b" + re.escape(term) + r"\b", b.lower()) and not NEGATIONS.search(b.lower()):
                    errors.append(f'bullets.{exp_id}: claims "{term}" -> "{b[:100]}"')

    # 3. The letter must name this company and must not name a company you applied to before.
    letter = free["letter"]
    company = spec.get("company", "")
    if letter and company and company.split()[0].lower() not in letter.lower():
        warnings.append(f'letter: does not mention "{company}" - is it the right letter?')
    for prev in _previous_companies():
        if prev and prev.lower() != company.lower() and len(prev) > 3 and re.search(
            r"\b" + re.escape(prev) + r"\b", letter, re.I
        ):
            errors.append(f'letter: mentions "{prev}", a company from an earlier application (stale letter?)')

    # 4. Leftover placeholders.
    for field, text in free.items():
        if re.search(r"\[[A-Z _]+\]|<[a-z_ ]+>|TODO|XXX", text):
            errors.append(f"{field}: contains a placeholder")
    return errors, warnings


def _previous_companies() -> list[str]:
    if not APPLIED.exists():
        return []
    with APPLIED.open(encoding="utf-8") as f:
        return [r["company"] for r in csv.DictReader(f)]


# --------------------------------------------------------------------------- rendering
CSS = """
@page { size: Letter; margin: 0.55in 0.6in; }
body { font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 10.3pt; color: #111; line-height: 1.32; }
h1 { font-size: 19pt; margin: 0; letter-spacing: .3px; }
.contact { color: #444; margin: 2px 0 8px; }
.headline { font-weight: 700; text-transform: uppercase; font-size: 9.5pt; letter-spacing: .8px; color: #1f4e79; margin-top: 4px; }
h2 { font-size: 10pt; text-transform: uppercase; letter-spacing: 1px; border-bottom: 1px solid #999; margin: 11px 0 4px; padding-bottom: 1px; color: #1f4e79; }
.role { display: flex; justify-content: space-between; font-weight: 700; margin-top: 5px; }
.role span:last-child { font-weight: 400; color: #444; }
ul { margin: 2px 0 2px 16px; padding: 0; } li { margin: 1px 0; }
p { margin: 0 0 9px; }
"""


def _esc(s: str) -> str:
    return html.escape(s or "")


def resume_html(spec: dict, facts: dict) -> str:
    bank = bullet_bank(facts)
    chosen = spec.get("bullets") or {}
    c = facts.get("contact", {})
    contact = " | ".join(x for x in [c.get("city"), c.get("phone"), c.get("email"), c.get("link")] if x)
    parts = [f"<h1>{_esc(facts['name'])}</h1><div class='contact'>{_esc(contact)}</div>"]
    parts.append(f"<div class='headline'>{_esc(spec.get('headline') or facts.get('headline', ''))}</div>")
    parts.append(f"<p>{_esc(spec.get('profile') or facts.get('summary', ''))}</p>")
    parts.append("<h2>Experience</h2>")
    for e in facts.get("experience", []):
        items = chosen.get(e["id"])
        if items is None:
            items = e.get("bullets", [])[: int(facts.get("default_bullets", 3))]
        lines = [bank[e["id"]][i] if isinstance(i, int) else i for i in items]
        parts.append(
            f"<div class='role'><span>{_esc(e['company'])} | {_esc(e['title'])}</span><span>{_esc(e.get('dates', ''))}</span></div>"
        )
        if lines:
            parts.append("<ul>" + "".join(f"<li>{_esc(x)}</li>" for x in lines) + "</ul>")
    skills = spec.get("skills") or facts.get("skills", "")
    if skills:
        parts.append(f"<h2>Skills</h2><p>{_esc(skills)}</p>")
    edu = facts.get("education", [])
    if edu or facts.get("work_authorization"):
        parts.append("<h2>Education and work authorization</h2><p>")
        parts.append("<br>".join(_esc(x) for x in edu + ([facts["work_authorization"]] if facts.get("work_authorization") else [])))
        parts.append("</p>")
    return f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{''.join(parts)}</body></html>"


def letter_text(spec: dict, facts: dict) -> str:
    greet = spec.get("greeting", "Dear Hiring Team,")
    sign = facts.get("letter_signoff", "Sincerely,")
    return greet + "\n\n" + "\n\n".join(spec.get("letter", [])) + f"\n\n{sign}\n{facts['name']}"


def letter_html(spec: dict, facts: dict) -> str:
    body = "".join(f"<p>{_esc(p)}</p>" for p in letter_text(spec, facts).split("\n\n"))
    c = facts.get("contact", {})
    head = f"<h1>{_esc(facts['name'])}</h1><div class='contact'>{_esc(' | '.join(x for x in [c.get('city'), c.get('phone'), c.get('email')] if x))}</div><br>"
    return f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{head}{body.replace(chr(10), '<br>')}</body></html>"


def to_pdf(html_path: Path, pdf_path: Path) -> str:
    """Render HTML to PDF with whichever engine is installed. Returns engine name or ''."""
    try:
        from weasyprint import HTML  # type: ignore

        HTML(filename=str(html_path)).write_pdf(str(pdf_path))
        return "weasyprint"
    except ImportError:
        pass
    try:
        from playwright.sync_api import sync_playwright  # type: ignore

        with sync_playwright() as p:
            exe = os.environ.get("HA_CHROMIUM")
            b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
            pg = b.new_page()
            pg.goto(html_path.resolve().as_uri())
            pg.pdf(path=str(pdf_path), format="Letter", prefer_css_page_size=True, print_background=True)
            b.close()
        return "playwright"
    except Exception as exc:  # noqa: BLE001
        print(f"  (no PDF engine: {exc.__class__.__name__}; HTML written - print it to PDF from a browser)")
        return ""


def pdf_pages(pdf_path: Path) -> int | None:
    try:
        from pypdf import PdfReader  # type: ignore

        return len(PdfReader(str(pdf_path)).pages)
    except Exception:  # noqa: BLE001
        return None


# --------------------------------------------------------------------------- commands
def cmd_check(args) -> int:
    facts = load_facts()
    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    errors, warnings = check_spec(spec, facts)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("BLOCK", e)
    print("PASS" if not errors else f"FAIL ({len(errors)} problem(s))")
    return 1 if errors else 0


def cmd_build(args) -> int:
    facts = load_facts()
    rc = 0
    for sp in args.spec:
        spec = json.loads(Path(sp).read_text(encoding="utf-8"))
        errors, warnings = check_spec(spec, facts)
        for w in warnings:
            print("WARN ", w)
        if errors and not args.force:
            for e in errors:
                print("BLOCK", e)
            print(f"NOT BUILT {sp}: fix the problems above (or --force if you are sure they are true)")
            rc = 1
            continue
        short = spec.get("short") or re.sub(r"\W+", "", spec["company"])[:24]
        d = OUT / short
        d.mkdir(parents=True, exist_ok=True)
        (d / "resume.html").write_text(resume_html(spec, facts), encoding="utf-8")
        (d / "letter.html").write_text(letter_html(spec, facts), encoding="utf-8")
        (d / "letter.txt").write_text(letter_text(spec, facts), encoding="utf-8")
        engine = to_pdf(d / "resume.html", d / f"{short}_Resume.pdf")
        pages = pdf_pages(d / f"{short}_Resume.pdf") if engine else None
        if engine:
            to_pdf(d / "letter.html", d / f"{short}_Cover_Letter.pdf")
        status = "OK" if pages in (1, None) else "CHECK"
        print(f"{status} {short}: {d} resume_pages={pages} letter_chars={len((d / 'letter.txt').read_text(encoding='utf-8'))}")
    return rc


def _rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_rows(path: Path, rows: list[dict], cols: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def _log(text: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"- {TODAY}: {text}\n")


def cmd_seen(args) -> int:
    for q in args.company:
        hits = []
        for name, path in (("applied", APPLIED), ("screened_out", SCREENED)):
            for r in _rows(path):
                if q.lower() in r.get("company", "").lower():
                    hits.append(f"{name}: " + " | ".join(v for v in r.values() if v))
        print(f"{q} -> " + ("\n  ".join(hits) if hits else "NEW"))
    return 0


def cmd_done(args) -> int:
    rows = _rows(APPLIED)
    rows.append(dict(date=TODAY, company=args.company, title=args.title, source=args.source or "",
                     category=args.category or "", status="applied", status_date=TODAY, note=args.note or ""))
    _write_rows(APPLIED, rows, APPLIED_COLS)
    _log(f"APPLIED {args.company} - {args.title}. {args.note or ''}".strip())
    print("logged")
    return 0


def cmd_skip(args) -> int:
    rows = _rows(SCREENED)
    rows.append(dict(date=TODAY, company=args.company, title=args.title, reason=args.reason))
    _write_rows(SCREENED, rows, ["date", "company", "title", "reason"])
    print("logged")
    return 0


def cmd_outcome(args) -> int:
    rows = _rows(APPLIED)
    match = [r for r in rows if args.company.lower() in r["company"].lower()]
    if not match:
        print("no application found for", args.company)
        return 1
    r = match[-1]
    r.update(status=args.status, status_date=TODAY, note=(r.get("note", "") + f" | {args.note}" if args.note else r.get("note", "")))
    _write_rows(APPLIED, rows, APPLIED_COLS)
    _log(f"OUTCOME {r['company']} - {r['title']}: {args.status}")
    print(f"{r['company']} -> {args.status}")
    return 0


def cmd_stats(_args) -> int:
    rows = _rows(APPLIED)
    if not rows:
        print("no applications logged yet")
        return 0

    def line(label: str, rs: list[dict]) -> str:
        n = len(rs)
        iv = sum(r["status"] in ("interview", "offer") for r in rs)
        rej = sum(r["status"] == "rejected" for r in rs)
        return f"{label:<28} {n:>4} applied  {iv:>3} interviews ({iv / n:.1%})  {rej:>3} rejected"

    print(line("ALL", rows))
    for key in ("category", "source"):
        groups: dict[str, list[dict]] = {}
        for r in rows:
            groups.setdefault(r.get(key) or "(none)", []).append(r)
        print(f"\nby {key}:")
        for k, rs in sorted(groups.items(), key=lambda kv: -len(kv[1])):
            print("  " + line(k, rs))
    stale = [r for r in rows if r["status"] == "applied" and (dt.date.today() - dt.date.fromisoformat(r["date"])).days >= 14]
    if stale:
        print(f"\n{len(stale)} application(s) with no reply after 14+ days: consider a follow-up or mark no_response.")
    return 0


# --------------------------------------------------------------------------- setup interview
def _ask(prompt: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    val = input(f"{prompt}{hint}: ").strip()
    return val or default


def _ask_list(prompt: str) -> list[str]:
    print(f"{prompt} (one per line, empty line to finish)")
    out = []
    while True:
        line = input("  - ").strip()
        if not line:
            return out
        out.append(line)


def _yes(prompt: str, default: str = "n") -> bool:
    return _ask(prompt + " (y/n)", default).lower().startswith("y")


SUGGESTED_NEVER = ["bachelor", "degree", "college diploma", "master's", "certified", "licensed", "registered",
                   "bilingual", "fluent french", "team lead", "supervisor", "managed a team"]


def cmd_init(args) -> int:
    """Interview the user and write profile/facts.yaml, answers.md and targets.md."""
    prof = ROOT / "profile"
    files = [prof / "facts.yaml", prof / "answers.md", prof / "targets.md"]
    if any(f.exists() for f in files) and not args.force:
        print("Profile files already exist. Edit them directly, or run `init --force` to start over.")
        return 1
    print("\nhonest-apply setup. Only enter things that are TRUE; everything here can end up on a resume.\n")

    print("== About you")
    facts: dict = {"name": _ask("Full name")}
    facts["contact"] = {k: v for k, v in {
        "city": _ask("City, province/state (as it should appear on a resume)"),
        "phone": _ask("Phone"), "email": _ask("Email"), "link": _ask("LinkedIn or portfolio link (optional)"),
    }.items() if v}
    facts["work_authorization"] = _ask("Work authorization line, e.g. 'Authorized to work in Canada'")

    print("\n== Education (highest first). Leave blank when done.")
    facts["education"] = _ask_list("Each credential, e.g. 'Diploma in Office Administration, 2019'")
    has_degree = _yes("Do you have a college diploma or university degree?")

    print("\n== Work history, most recent first. You'll write bullets in your own words; only true ones.")
    facts["experience"] = []
    while True:
        company = _ask("Company (blank to finish)")
        if not company:
            break
        title = _ask("  Your job title")
        dates = _ask("  Dates (e.g. Mar 2023 - Aug 2025)")
        bullets = _ask_list("  What you actually did there")
        eid = re.sub(r"\W+", "", company.lower())[:12] or f"job{len(facts['experience'])+1}"
        facts["experience"].append({"id": eid, "company": company, "title": title, "dates": dates, "bullets": bullets})

    print("\n== Summary")
    facts["headline"] = _ask("Short headline for your resume, e.g. 'Patient Scheduling and Front Desk'")
    facts["summary"] = _ask("2-3 sentence summary (facts only)")
    facts["skills"] = _ask("Skills and tools you really use, separated by ' | '")

    print("\n== Things you must never claim")
    print("Suggestions: " + ", ".join(SUGGESTED_NEVER))
    never = [] if has_degree else ["bachelor", "degree", "college diploma"]
    for s in SUGGESTED_NEVER:
        if s not in never and s not in ("bachelor", "degree", "college diploma") and _yes(f"  Never claim '{s}'?", "y"):
            never.append(s)
    never += [x.lower() for x in _ask_list("Anything else you must never claim (tools, licences, titles)")]
    facts["never_claim"] = never
    facts.update(bullet_match_threshold=0.85, default_bullets=3, letter_signoff="Sincerely,")

    print("\n== Jobs you want")
    roles = _ask_list("Target roles, highest priority first")
    where = _ask("Where (e.g. 'within 30 minutes of downtown, or remote')")
    pay = _ask("Lowest pay you'll accept (e.g. $22/hr or $46,000)")
    breakers = _ask_list("Deal-breakers (e.g. commission only, overnight shifts)")

    print("\n== Standard screener answers")
    a = {
        "Authorized to work": _ask("Legally allowed to work in the country? (Yes/No)", "Yes"),
        "Needs sponsorship": _ask("Need visa sponsorship? (Yes/No)", "No"),
        "Driver's licence": _ask("Driver's licence (e.g. 'Yes, G' or 'No')"),
        "Own vehicle": _ask("Own vehicle for work? (Yes/No)"),
        "Start date": _ask("Earliest start", "Immediately"),
        "Salary (digits only)": _ask("Expected salary, digits only (e.g. 55000)"),
        "Salary range text": _ask("Salary range text (e.g. $44,000-$48,000)"),
        "Weekends": _ask("Weekend work OK? (Yes/No)"),
    }
    extra = _ask_list("Other exact facts for screeners, e.g. 'Typing speed: 55 wpm'")

    prof.mkdir(exist_ok=True)
    (prof / "facts.yaml").write_text(yaml.safe_dump(facts, sort_keys=False, allow_unicode=True, width=100), encoding="utf-8")
    lines = ["# Screener answer bank", "", "## Standard answers"] + [f"- {k}: {v}" for k, v in a.items() if v]
    lines += ["", "## Education and qualifications",
              f"- Any degree / diploma question: **{'see education list' if has_degree else 'No'}**."]
    lines += ["", "## Exact facts"] + [f"- {x}" for x in extra]
    lines += ["", "## Questions the human always answers",
              "- Criminal record, background-check consent, medical, disability, legal questions.",
              "", "## Autofill rules",
              "- Treat every pre-filled field as untrusted; correct it to match this file.",
              "- Clear the cover-letter box completely before entering a new letter."]
    (prof / "answers.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    t = ["# Targets", "", "## Roles (priority order)"] + [f"{i+1}. {r}" for i, r in enumerate(roles)]
    t += ["", f"## Location\n{where}", "", f"## Pay floor\n{pay}", "", "## Deal-breakers"] + [f"- {b}" for b in breakers]
    (prof / "targets.md").write_text("\n".join(t) + "\n", encoding="utf-8")
    print(f"\nSaved {', '.join(str(f.relative_to(ROOT)) for f in files)}. Read them once and fix anything that isn't exactly right.")
    return 0


def cmd_queue(_args) -> int:
    print(QUEUE.read_text(encoding="utf-8") if QUEUE.exists() else "(queue empty)")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="apply.py", description="honest-apply job application kit")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("build"); p.add_argument("spec", nargs="+"); p.add_argument("--force", action="store_true"); p.set_defaults(fn=cmd_build)
    p = sub.add_parser("check"); p.add_argument("spec"); p.set_defaults(fn=cmd_check)
    p = sub.add_parser("seen"); p.add_argument("company", nargs="+"); p.set_defaults(fn=cmd_seen)
    p = sub.add_parser("done"); p.add_argument("company"); p.add_argument("title")
    p.add_argument("--source"); p.add_argument("--category"); p.add_argument("--note"); p.set_defaults(fn=cmd_done)
    p = sub.add_parser("skip"); p.add_argument("company"); p.add_argument("title"); p.add_argument("reason"); p.set_defaults(fn=cmd_skip)
    p = sub.add_parser("outcome"); p.add_argument("company")
    p.add_argument("status", choices=["interview", "rejected", "offer", "no_response", "withdrawn"]); p.add_argument("--note"); p.set_defaults(fn=cmd_outcome)
    sub.add_parser("stats").set_defaults(fn=cmd_stats)
    sub.add_parser("queue").set_defaults(fn=cmd_queue)
    p = sub.add_parser("init"); p.add_argument("--force", action="store_true"); p.set_defaults(fn=cmd_init)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
