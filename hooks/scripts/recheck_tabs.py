#!/usr/bin/env python3
"""UserPromptSubmit hook for qa-test-design.

When the user says they added a tab to the Chrome tab group or asks for a
re-check, inject a reminder to re-inventory the tabs. Prints nothing
otherwise. Always exits 0 so the user's message is never blocked.
"""
import json
import re
import sys

ZH_PHRASES = [
    "加進group", "加到tabgroup", "加進群組", "加到群組", "拖進來了", "分頁加好了",
    "請再確認", "再確認一次", "重新讀一下分頁", "再survey一次", "重新盤點", "新加的tab",
]
EN_PATTERNS = [
    r"\badded (it |the tabs? |them )?to the (tab )?group\b",
    r"\badded the tabs?\b",
    r"\btabs? (is|are) in the group now\b",
    r"\bcheck again\b",
    r"\bre-?check the tabs\b",
    r"\bre-?scan the (tab )?group\b",
    r"\bsurvey the tabs again\b",
]

REMINDER = (
    "If this conversation is using the qa-test-design skill: the user has added "
    "tabs or asked for a re-check. Call tabs_context_mcp again now, compare with "
    "the previous tab inventory, tell the user which tabs were added or removed, "
    "read every added tab with the full rules (connector first, all comments, "
    "linked work items, images, attachments), update the question list, and ask "
    "another AskUserQuestion round if new questions came up."
)


def matches(prompt: str) -> bool:
    compact = re.sub(r"\s+", "", prompt).lower()
    if any(p.lower() in compact for p in ZH_PHRASES):
        return True
    lowered = prompt.lower()
    return any(re.search(p, lowered) for p in EN_PATTERNS)


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    if matches(data.get("prompt", "")):
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": REMINDER,
            }
        }))
    sys.exit(0)


if __name__ == "__main__":
    main()
