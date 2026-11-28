"""Make Claude rewrite a reply to the owner in Japanese when it slipped into English.

pre-tool  PreToolUse on chat-posting MCP tools: deny the post, Claude resends.
stop      Stop hook for terminal sessions: block the stop, Claude rewrites.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

MIN_LATIN = 40
RATIO = 3
POSTING_TOOL = re.compile(r"__(?:post_message|edit_message)$")
NOISE = re.compile(
    r"```.*?(?:```|\Z)"
    r"|`[^`\n]*`"
    r"|\]\([^)\s]*\)"
    r"|https?://\S+"
    r"|\S*[/\\]\S*"
    r"|\S+\.(?:py|md|json|toml|sh|ts|js|yml|yaml)\b",
    re.DOTALL,
)
LATIN = re.compile(r"[A-Za-z]")
KANA = re.compile(r"[぀-ヿｦ-ﾟ]")
KANJI = re.compile(r"[㐀-䶿一-鿿]")
REASON = (
    "This reply to the owner is in English, but the owner reads Japanese. "
    "Rewrite it in Japanese and send it again. Code, commands, paths and "
    "product names stay as they are. If the owner asked for English text, "
    "put that text in a code block and write the rest in Japanese."
)


def is_english(text: str) -> bool:
    prose = NOISE.sub(" ", text)
    latin = len(LATIN.findall(prose))
    kana = len(KANA.findall(prose))
    japanese = kana + len(KANJI.findall(prose)) if kana else 0
    return latin >= MIN_LATIN and latin > RATIO * japanese


def transcript_entries(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    entries: list[dict[str, Any]] = []
    for line in lines:
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        message = obj.get("message") if isinstance(obj, dict) else None
        if isinstance(message, dict):
            entries.append(message)
    return entries


def contents(entries: list[dict[str, Any]]) -> list[tuple[str, dict[str, Any]]]:
    return [
        (str(message.get("role", "")), item)
        for message in entries
        if isinstance(message.get("content"), list)
        for item in message["content"]
        if isinstance(item, dict)
    ]


def replied_via_tool(entries: list[dict[str, Any]]) -> bool:
    return any(
        item.get("type") == "tool_use"
        and bool(POSTING_TOOL.search(str(item.get("name", ""))))
        for _, item in contents(entries)
    )


def last_reply(entries: list[dict[str, Any]]) -> str:
    texts = [
        str(item.get("text", ""))
        for role, item in contents(entries)
        if role == "assistant" and item.get("type") == "text"
    ]
    return texts[-1] if texts else ""


def pre_tool(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input") or {}
    text = tool_input.get("text") if isinstance(tool_input, dict) else None
    if not isinstance(text, str) or not is_english(text):
        return ""
    decision = {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": REASON,
    }
    return json.dumps({"hookSpecificOutput": decision})


def stop(payload: dict[str, Any]) -> str:
    if payload.get("stop_hook_active"):
        return ""
    entries = transcript_entries(Path(str(payload.get("transcript_path", ""))))
    if replied_via_tool(entries):
        return ""
    text = payload.get("last_assistant_message")
    if not isinstance(text, str):
        text = last_reply(entries)
    if not is_english(text):
        return ""
    return json.dumps({"decision": "block", "reason": REASON})


def main(argv: list[str]) -> int:
    modes = {"pre-tool": pre_tool, "stop": stop}
    mode = modes.get(argv[1] if len(argv) > 1 else "")
    if mode is None:
        print("usage: reply_language.py pre-tool|stop", file=sys.stderr)
        return 2
    try:
        output = mode(json.loads(sys.stdin.read()))
        if output:
            print(output)
    except Exception as exc:  # noqa: BLE001
        print(f"reply_language: {exc!r}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
