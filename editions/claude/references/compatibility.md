# Compatibility and distribution

Native Claude Code: place the complete `honest-apply-claude` directory under the project's `.claude/skills/` directory, or direct Claude to its SKILL.md. This package is not installed automatically. Runtime needs Python 3.10+ and approved local file access. The script has no third-party dependencies. Other Claude surfaces can use the instructions but file/shell capabilities differ; don't promise execution there.

Agensi: its published documentation says SKILL.md and an index are served first; text scripts are fetched individually, may be written temporarily and then removed. Binary templates are not served. `career.py` is self-contained: it imports only the standard library and reads no sibling package resources. Inputs/outputs belong in explicit private working paths, not the temporary script directory. Fetch reference text separately as needed. No bundled binary template is required. Outputs are local HTML/text/JSON.

Agensi remote-connector authentication, listing validation, temporary-script execution and marketplace end-to-end delivery have NOT been tested. Only one connected agent per Agensi account is currently documented. Do not install connectors, sign in, upload or accept marketplace terms from these instructions alone.

Primary references consulted November 17, 2026:
- https://www.agensi.io/docs/how-agents-load-skills
- https://www.agensi.io/docs/mcp-server
- https://www.agensi.io/docs/packaging

Privacy: no user-specific data is shipped. Actual input to a Claude session is processed under that service's settings/terms; this is not a claim of zero cloud processing. Keep generated private working files outside version control and outside any marketplace ZIP. No telemetry exists in the helper. The user controls any subsequent sharing.
