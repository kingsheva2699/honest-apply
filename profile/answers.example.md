# Screener answer bank (example: fictional person)

Copy to `profile/answers.md` (git-ignored), or run `python apply.py init`, and
fill in YOUR answers. The agent uses these word for word and never improvises
an answer that isn't here. When a new kind of question appears, it asks you
once and adds your answer.

## Standard answers
- Authorized to work in Canada: Yes. Needs sponsorship: No.
- Driver's licence: No.
- Start date: Two weeks' notice.
- Salary (numeric fields, digits only): 46000. Range text: "$44,000-$48,000".
- Evenings: Yes, until 8 pm. Weekends: No.
- Know anyone at the company: No.

## Education and qualifications
- Highest education: Diploma in Office Administration (2019).
- Any "Do you have a university degree" question: **No**.
- Any certification question (dental assisting, first aid, etc.): **No**, unless listed here.

## Experience numbers (exact)
- Medical/dental reception: 3 years.
- Customer service total: 6 years (3 dental + 3 retail).
- Typing speed: 55 wpm.
- Languages: English (fluent). French: basic only.

## Questions the human always answers
- Criminal record, background-check consent, medical, disability, or anything legal.
  The agent fills everything else first, then names these questions and stops.

## Autofill rules (job boards remember old answers)
- Treat every pre-filled field as untrusted. Read each one and correct it to
  match this file before pressing Continue.
- The cover-letter box often still holds the previous job's letter. Clear it
  completely before entering the new one.
