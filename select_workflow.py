"""Select a local workflow. Never starts a browser, executes an edition, or sends data."""
import argparse
import json
import re
import sys
from pathlib import Path

MODES = {
    "core": ("skills/job-application/SKILL.md", "apply.py"),
    "claude": ("editions/claude/SKILL.md", "editions/claude/scripts/career.py"),
    "indeed": ("editions/indeed/SKILL.md", "editions/indeed/scripts/career.py"),
    "manual": ("editions/manual.md", None),
}
CLAUDE = re.compile(r"^(?:anthropic[/.:])?claude(?:[- ./]|$)", re.IGNORECASE)


def select(*, host="auto", model="", board="other", runtime=True):
    """Choose on known capabilities first, then board and host/model."""
    if not runtime:
        edition = "manual"
    elif board == "indeed":
        edition = "indeed"
    elif host == "claude" or (host == "auto" and CLAUDE.match(model.strip())):
        edition = "claude"
    else:
        edition = "core"
    workflow, script = MODES[edition]
    return {
        "edition": edition,
        "workflow": workflow,
        "script": script,
        "application": "manual",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=("auto", "claude", "other"), default="auto",
                        help="Pass the known host; otherwise infer from the supplied model ID.")
    parser.add_argument("--model", default="", help="Optional provider/model ID supplied by the host.")
    parser.add_argument("--board", choices=("other", "indeed", "linkedin"), default="other")
    parser.add_argument("--text-only", action="store_true", help="Target host cannot run local Python.")
    args = parser.parse_args()
    result = select(host=args.host, model=args.model, board=args.board, runtime=not args.text_only)
    root = Path(__file__).resolve().parent
    for key in ("workflow", "script"):
        path = result[key]
        if path and not (root / path).is_file():
            print(f"Missing edition file: {path}. Use a complete repository checkout.", file=sys.stderr)
            return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
