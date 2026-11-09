# AGENTS.md

Instructions for coding agents (Claude Code, Codex, Cursor, Grok Bot, and similar) working in this repository.

## What this repo is

`mcpsentry` is a small Python 3.10+ command-line tool to lint MCP tool manifests for injection phrasing and incomplete schemas. It has no required runtime dependencies and no API key. Layout:

- `mcpsentry/cli.py` — the implementation and the `main()` entry point (exit code is an `int`)
- `mcpsentry/__main__.py` — `python -m mcpsentry`
- `mcpsentry/__init__.py` — `__version__`
- `tests/test_mcpsentry.py` — pytest suite
- `pyproject.toml` — packaging, the `mcpsentry` script, and the `dev` extra (`pytest`)
- `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `PROOF.md` — human docs

mcpsentry/cli.py lints tool manifests. tests/test_mcpsentry.py covers injection language, incomplete schemas, and the readonly-conflict warning.

## How to run tests

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest -q
mcpsentry --help
mcpsentry --version
```

`pip install .` in a fresh virtualenv must leave `mcpsentry` on `PATH`.

## Conventions

- Keep changes small. Match the existing style: standard library, type hints, `argparse`, exit codes documented in the README.
- If you add behavior, add a test for it. Prefer tests of user-visible behavior over tests of internals.
- Do not add network calls, API keys, or telemetry.
- Do not copy source from other tools. This is a clean-room project.
- If a README, SECURITY.md, or Limits section would become untrue, update it in the same change.
- Do not commit secrets. For `mcpsentry`, also do not commit local store/journal/database files (see `.gitignore`).
- Token estimates in this family of tools, when present, are `ceil(utf-8 bytes / 4)`. Do not describe them as a vendor tokenizer.

## If you are using the tool rather than changing it

Install it from this checkout or from `pip install git+https://github.com/perron/mcpsentry.git`, then follow the 30-second quick start in the README. The README Limits section is the contract for what this release does and does not do.
