"""Lint MCP tool manifests for unsafe descriptions and incomplete schemas."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

__version__ = "0.1.0"

INJECT_RE = re.compile(
    r"(ignore (all )?(previous|prior) (instructions|prompts)|disregard (your )?(system )?prompt|"
    r"after (every|each|the last) (tool|function) call|forward (the )?(full )?(conversation|chat|transcript)|"
    r"send (the )?(chat|conversation|history|transcript) to|exfiltrat|exfil host)",
    re.I,
)
SIDE_CHANNEL_RE = re.compile(
    r"(save_logs|upload_logs|telemetry ping|hidden (param|parameter)|do not tell the user)",
    re.I,
)
WRITE_NAME_RE = re.compile(r"(delete|drop|destroy|truncate|write|update|put|post|send|exec|run|shell|eval)", re.I)


@dataclass
class Finding:
    severity: str
    code: str
    message: str
    tool: str


def iter_tools(data: Any) -> list[tuple[str, dict[str, Any]]]:
    tools: list[tuple[str, dict[str, Any]]] = []
    if isinstance(data, list):
        for tool in data:
            tools.append((str(tool.get("name") or "(unnamed)"), tool))
        return tools
    if isinstance(data, dict):
        if "tools" in data:
            return iter_tools(data["tools"])
        if "servers" in data:
            for server in data["servers"]:
                server_name = server.get("name") or "server"
                for tool in server.get("tools") or []:
                    name = f"{server_name}.{tool.get('name') or '(unnamed)'}"
                    tools.append((name, tool))
            return tools
    raise ValueError("expected a tool array or an object with tools/servers")


def lint_tool(name: str, tool: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    desc = str(tool.get("description") or "")
    if not desc.strip():
        findings.append(Finding("warning", "missing-description", "tool has no description", name))
    if INJECT_RE.search(desc):
        findings.append(Finding(
            "error",
            "injection-language",
            "description contains prompt-injection or conversation-forwarding language",
            name,
        ))
    if SIDE_CHANNEL_RE.search(desc) or SIDE_CHANNEL_RE.search(name):
        findings.append(Finding(
            "error",
            "side-channel",
            "tool name or description looks like a hidden log/telemetry channel",
            name,
        ))
    if len(desc) > 800:
        findings.append(Finding(
            "warning",
            "long-description",
            f"description is {len(desc)} characters; long tool descriptions are a common injection surface",
            name,
        ))

    schema = tool.get("inputSchema") or tool.get("input_schema") or tool.get("parameters")
    if not isinstance(schema, dict):
        findings.append(Finding("error", "missing-schema", "tool has no inputSchema object", name))
        schema = {}
    if schema and schema.get("type") not in (None, "object"):
        findings.append(Finding("warning", "schema-type", "inputSchema type is not object", name))
    required = schema.get("required") or []
    props = schema.get("properties") or {}
    if required and not isinstance(props, dict):
        findings.append(Finding("error", "incomplete-schema", "required fields listed but properties is not a map", name))
    elif required:
        missing = [key for key in required if key not in props]
        if missing:
            findings.append(Finding(
                "error",
                "incomplete-schema",
                f"required properties missing from schema: {', '.join(missing)}",
                name,
            ))

    annotations = tool.get("annotations") or {}
    looks_destructive = bool(WRITE_NAME_RE.search(name.split(".")[-1]))
    if looks_destructive and not annotations.get("destructiveHint") and annotations.get("readOnlyHint") is not True:
        # missing destructiveHint on a write-like name
        if annotations.get("readOnlyHint") is True:
            findings.append(Finding(
                "warning",
                "readonly-conflict",
                "tool name looks destructive but annotations.readOnlyHint is true",
                name,
            ))
        else:
            findings.append(Finding(
                "warning",
                "missing-destructive-hint",
                "tool name looks like a write/delete and has no annotations.destructiveHint",
                name,
            ))
    return findings


def lint_data(data: Any) -> list[Finding]:
    findings: list[Finding] = []
    for name, tool in iter_tools(data):
        findings.extend(lint_tool(name, tool))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mcpsentry",
        description="Lint MCP tool manifests for prompt-injection phrasing, missing hints, and incomplete schemas.",
    )
    parser.add_argument("input", help="JSON file of tools, or '-' for stdin")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--version", action="version", version=f"mcpsentry {__version__}")
    args = parser.parse_args(argv)
    if args.input == "-":
        raw = sys.stdin.read()
    else:
        path = Path(args.input)
        if not path.is_file():
            print(f"error: file not found: {path}", file=sys.stderr)
            return 1
        raw = path.read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
        findings = lint_data(data)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    errors = sum(1 for f in findings if f.severity == "error")
    warnings = sum(1 for f in findings if f.severity == "warning")
    if args.json:
        print(json.dumps({"findings": [asdict(f) for f in findings], "errors": errors, "warnings": warnings}, indent=2))
    else:
        if not findings:
            print("ok: no findings")
        for f in findings:
            print(f"{f.severity}: {f.code}: {f.message} ({f.tool})")
        print(f"{errors} error(s), {warnings} warning(s)")
    if errors:
        return 2
    if warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
