<!-- .github/copilot-instructions.md - guidance for automated coding agents -->
# Quick instructions for AI coding agents

This repository currently contains a minimal layout (no source code yet). The goal of these instructions is to help an AI agent become productive quickly and avoid guesswork.

## Snapshot (discoverable)
- Files present: `LICENSE` (MIT), `.vscode/settings.json`, Git metadata (`.git/`).
- No `README.md`, no language manifests (`package.json`, `pyproject.toml`, `requirements.txt`, etc.), and no `src/` or `tests/` directories were detected.

## Immediate priorities for an agent
1. Confirm intent before scaffolding. Prompt the human for the target language, framework and high-level purpose (CLI tool, web app, library, etc.). Example question: "Do you want this to be a Python library, a Node app, or something else? Any preferred test framework?"
2. If the user confirms to scaffold, create minimal, discoverable artifacts: `README.md`, a small `src/` layout, a `tests/` directory, and a manifest (`pyproject.toml` or `package.json`). Keep changes minimal and ask before adding CI.
3. Respect workspace Python settings: `.vscode/settings.json` sets `python-envs.defaultEnvManager` to `ms-python.python:system`. Prefer system Python when creating examples or instructions unless the user asks for a venv/virtual environment.

## When editing or adding code
- Keep changes small and self-contained. Create a top-level `README.md` documenting how to run, test and the project purpose.
- Add one focused unit test for every new feature or module you add. Put tests under `tests/` and use a standard runner (`pytest` for Python, `npm test` for Node).
- Include a short usage example in `README.md` and add runnable commands in the repo's root (examples should work on a default Ubuntu environment).

## Repository-specific patterns to follow
- License: project uses MIT (`LICENSE`) — include license header in new top-level files if the user requests it.
- VS Code settings exist but are minimal. Do not overwrite `.vscode/settings.json` without asking; instead add new editorconfig or workspace files only if requested.
- Branching: default branch is `main`. Open small feature branches and reference `main` when creating PRs.

## Integration points & unknowns
- No external integrations were found in the repository. Ask the user for details (databases, cloud providers, package registries, or existing APIs) before adding credentials or network calls.

## Helpful file references (if/when present)
- `README.md` — should contain purpose, run/test commands and a short example.
- `pyproject.toml` / `requirements.txt` — Python project metadata and dependencies.
- `package.json` — Node project metadata and scripts.
- `src/`, `lib/` — primary implementation code.
- `tests/` — unit/integration tests.

## Example scaffolding commands (ask permission before running)
```bash
# Python scaffold (suggested minimal):
mkdir -p src tests
echo "# Project README" > README.md
printf "[tool.poetry]\nname = \"project\"\nversion = \"0.1.0\"\n" > pyproject.toml
```

## Final notes
- Be explicit in PR descriptions about why files were created. If the user hasn't provided a project goal, stop and ask rather than guessing large architectural decisions.
- After making changes, list created files and one-line purpose for each in the PR body.

If any of the above assumptions are wrong (for example, this repo already contains code on another branch or the user has platform constraints), ask the user for clarifying information before proceeding.
