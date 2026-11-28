import io
import json
import sys
from pathlib import Path
from typing import Any

import pytest
import reply_language

ENGLISH = "I opened the pull request and the tests pass. Please review it when free."
JAPANESE = "PR を作りました。テストは通っています。時間のあるときに見てください。"
TECHNICAL_JA = (
    "Claude Code 2.1.332 の PreSkillShellCommand フックと skill_audit.py を"
    "組み合わせると、読み込み時にも止められます。"
)
CODE_HEAVY = (
    "直しました。\n```python\ndef handler(event, context):\n"
    "    return {'statusCode': 200, 'body': 'hello world from lambda'}\n```\n"
    "詳細は https://docs.example.com/very/long/english/path/here を見てください。"
)
CHINESE = (
    "我已经打开了拉取请求，测试都通过了。"
    + " Please review the pull request soon, the tests all pass now."
)


@pytest.mark.parametrize(
    ("text", "english"),
    [
        (ENGLISH, True),
        (JAPANESE, False),
        (TECHNICAL_JA, False),
        (CODE_HEAVY, False),
        (CHINESE, True),
        ("Done.", False),
    ],
)
def test_is_english(text: str, english: bool) -> None:
    assert reply_language.is_english(text) is english


def pre(text: str) -> str:
    payload = {
        "tool_name": "mcp__hearthbot__post_message",
        "tool_input": {"text": text},
    }
    return reply_language.pre_tool(payload)


def test_pre_tool_denies_english_post_and_allows_japanese() -> None:
    out = json.loads(pre(ENGLISH))["hookSpecificOutput"]
    assert out["permissionDecision"] == "deny"
    assert "Japanese" in out["permissionDecisionReason"]
    assert pre(JAPANESE) == ""


def write(path: Path, messages: list[dict[str, Any]]) -> None:
    path.write_text("\n".join(json.dumps({"message": m}) for m in messages))


def said(text: str) -> dict[str, Any]:
    return {"role": "assistant", "content": [{"type": "text", "text": text}]}


def posted() -> dict[str, Any]:
    tool = {"type": "tool_use", "name": "mcp__hearthbot__post_message", "input": {}}
    return {"role": "assistant", "content": [tool]}


def stop(path: Path, **extra: Any) -> str:
    return reply_language.stop({"transcript_path": str(path), **extra})


def test_stop_blocks_english_final_reply(tmp_path: Path) -> None:
    t = tmp_path / "t.jsonl"
    write(t, [said(JAPANESE), said(ENGLISH)])
    assert json.loads(stop(t))["decision"] == "block"
    assert stop(t, stop_hook_active=True) == ""
    write(t, [said(ENGLISH), said(JAPANESE)])
    assert stop(t) == ""


def test_stop_prefers_last_assistant_message(tmp_path: Path) -> None:
    t = tmp_path / "t.jsonl"
    write(t, [said(JAPANESE)])
    assert json.loads(stop(t, last_assistant_message=ENGLISH))["decision"] == "block"


def test_stop_skips_sessions_that_reply_through_a_tool(tmp_path: Path) -> None:
    t = tmp_path / "t.jsonl"
    write(t, [posted(), said(ENGLISH)])
    assert stop(t) == ""


def test_hook_never_fails(capsys: pytest.CaptureFixture[str]) -> None:
    sys.stdin = io.StringIO("not json")
    assert reply_language.main(["x", "stop"]) == 0
    assert "reply_language" in capsys.readouterr().err
