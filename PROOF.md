# mcpsentry proof

Captured 2026-11-09 13:26 PST.

Fresh-venv install: `pip install .` succeeded and `mcpsentry --version` printed `mcpsentry 0.1.1`.

Tests: 16 passed in 0.03s

```
error: injection-language: description contains prompt-injection or conversation-forwarding language (save_logs)
error: side-channel: tool name or description looks like a hidden log/telemetry channel (save_logs)
error: incomplete-schema: required properties missing from schema: transcript (save_logs)
3 error(s), 0 warning(s)
exit: 2
```
