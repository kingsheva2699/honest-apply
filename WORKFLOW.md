# Start here: choose the Honest Apply workflow

For an AI assistant using this repository:

1. Determine whether you can run Python in a local checkout. If not, follow [the manual checklist](editions/manual.md). Do not claim that you ran any validator or produced a PDF.
2. Identify the platform from the user's request or the supplied posting URL. If it is not known, omit the platform rather than guessing. Run `python select_workflow.py`, passing `--board indeed` or `--board linkedin` when known. Pass `--host claude` for a known Claude host, or `--model <model-id>` when the host provides a real model ID. Omit unknown values. Do not probe for credentials or contact model providers to identify the host.
3. Read and follow the returned workflow file. If selection fails or the files aren't available, use the manual checklist and say what you couldn't verify.
4. Whatever the edition, prepare and review only. The user fills, uploads to, and submits the live application.
