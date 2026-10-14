# claude-qa-test-design

**Hand Claude a Jira ticket and get back a test plan your team can run. It reads the requirements the way a careful QA engineer does: every comment, every linked ticket, every attachment.**

`qa-test-design` is a Claude skill for QA engineers, packaged as a plugin. Open the ticket, the spec and the test environment in one Chrome tab group, then type one line. Claude reads all of it, asks you its questions in one round, and gives you a spreadsheet of test cases. If you ask it to, it also runs the tests in your environment and fills in the results.

```
/qa-test-design Read https://your-company.atlassian.net/browse/SHOP-142 and test it
```

> **In one line:** put the ticket, the spec and the test environment in one Chrome tab group, run `/qa-test-design` with the ticket URL, answer its questions, and get a spreadsheet back.

---

## Why I built this

Most missed bugs I've seen came from requirements, not from test steps. A few examples:

- The AC stated one row limit. Three comments down, the RD and PM had agreed on a lower one.
- The real scope was in a BE subtask that nobody on QA opened.
- The sample file attached to the ticket couldn't be imported by the new feature at all.
- The rule that mattered most was in a screenshot.

Generic "write test cases for this ticket" prompts skip all of that. They read the description and stop. This skill is built around the reading.

## What it does differently

| Most AI test generators | qa-test-design |
|---|---|
| Read the ticket description | Reads the description, **every comment**, and **every linked ticket** (BE / FE / DevOps), and treats PM/RD decisions in comments as spec |
| Ignore attachments or read the file name | **Opens every attachment** (CSV, xlsx, PDF, docx, zip) and checks it against the AC: headers, row counts, limits |
| Skip images | **Looks at every image**: screenshots, flowcharts, sequence diagrams |
| Ask questions as they go, or never | **Reads everything first, then asks all its questions in one round**, and doesn't write a case until they're answered |
| Hand back a wall of text | Gives you a **spreadsheet**: summary, cases, defects, open questions, test data |
| Stop at design | Can **run the tests** in your environment and fill in actual results, after you confirm anything that writes data |

## How a session goes

```
┌───────────────────────────────┐
│ 1. Inventory the tab group    │  Jira, Notion, Sheets, test environment
└───────────────┬───────────────┘
                ▼
┌───────────────────────────────┐
│ 2. Read everything            │  description, comments, linked tickets,
│                               │  spec pages, images, attachments
└───────────────┬───────────────┘
                ▼
┌───────────────────────────────┐
│ 3. Ask all questions at once  │  multiple choice, up to 4 per round
└───────────────┬───────────────┘
                ▼
┌───────────────────────────────┐
│ 4. Write test cases           │
└───────────────┬───────────────┘
                ▼
┌───────────────────────────────┐
│ 5. (Optional) Run the tests   │  confirms each write step with you first
└───────────────┬───────────────┘
                ▼
           result.xlsx
```

## What you get

A spreadsheet with five sheets. This is a trimmed copy of [`examples/sample-result.xlsx`](examples/sample-result.xlsx), which is based on a fictional ticket (SHOP-142, bulk coupon grant from CSV):

**Summary**

| Pass | Fail | Needs Review | Blocked | Not Run | Total |
|---|---|---|---|---|---|
| 28 | 5 | 8 | 5 | 9 | 55 |

**Test Cases** (one row)

| ID | Area | Source | Expected | Actual | Result | Defect |
|---|---|---|---|---|---|---|
| TC-15 | CSV limit | AC#7; RD comment 2026-09-15 (reject, do not truncate) | Whole file rejected; message shows the limit and the original row count | 3,001-row file accepted; only a hint to "narrow the filter" | **Fail** | F-01 |

Note the source column. The rule that failed came from a comment, not the AC body. A description-only read would have tested the wrong behavior.

- **Defects & Findings**: severity, actual vs. expected, and the basis for each. Ready to paste into a bug ticket.
- **Open Questions**: things the spec doesn't settle, and who needs to answer them.
- **Test Data**: every file it generated (boundary-size CSVs, a missing ID column, header only, BOM + semicolons) so you can rerun the tests.

When you only ask for design, Actual is empty and every Result is `Not Run`.

## Where to run it

The plugin isn't a smarter Claude. It's a way of packaging the same skill: same model, same `SKILL.md`, same reading rules. What changes the result is **what the environment lets Claude reach**: your logged-in Jira, Notion and staging tabs, and the test environment itself.

| Where you run it | Reads your logged-in tabs | Drives the test environment | Re-check hook | Best for |
|---|---|---|---|---|
| **Claude in Chrome side panel** + `.skill` | ✅ Reads the tab group directly | ✅ Clicks and fills forms with your login | ❌ Relies on the rule in `SKILL.md` | The main way to run this workflow |
| **Claude Code / Cowork** + plugin | ⚠️ Only with browser integration (for Claude Code, start it with `claude --chrome`) | ⚠️ With browser integration, same as the side panel. With Playwright instead, login usually needs separate handling | ✅ | Teams that want one version for everyone, the hook, or local files |
| **claude.ai** web or app, `.skill` only | ❌ Without browser integration it can't see your tabs; only what you paste in | ❌ | ❌ | Test design from pasted requirements only |

So the combination that works best is **browser integration + this skill**. Installing it as a plugin adds reliability and version control on top. It doesn't make Claude read better.

### Why not just use Playwright?

Claude Code with Playwright can do this too. The difference is the login.

**Playwright opens a fresh browser every time**, with none of your sessions or cookies. To read Jira, Notion and staging, it first has to get past login:

- **SSO and 2FA** on every run, or a script to handle them.
- **Saved login state** (`storageState`) expires, and it means storing a session for your company's systems in a file. Many security policies don't allow that.
- **Shared test accounts** see a different scope than you do.

**Claude in Chrome uses the Chrome you're already logged into.** It sees what you see, with your permissions and no more. Nothing extra to set up, no tokens stored.

| | Claude in Chrome | Claude Code + Playwright |
|---|---|---|
| Login | Uses your existing session | You handle SSO, 2FA and sessions |
| What it reads | Whatever you drag into the tab group | URLs you give it, or what it finds on its own |
| Visibility | Runs in your browser; you can watch and step in | Usually headless; you see the result afterwards |
| Setup | One line in the side panel | Node, MCP config, a terminal |
| Best for | First-pass test design and exploratory testing on a new ticket | Repeatable regression tests, CI, running at scale |

Two things worth knowing:

1. **They don't compete.** Claude Code started with `--chrome` uses the same browser integration and works the same way. What matters isn't Claude Code vs. the side panel; it's your real browser session vs. a fresh automated one. The skill itself also uses Playwright to download and parse attachments.
2. **For regression automation, Playwright is the better tool.** This skill covers the first pass on a new ticket: read the requirements, design the tests, run them once. Once the feature is stable, turn the key cases into Playwright tests in CI.

## Install

There are two ways to install it. For the Chrome side panel, the main way to run it, upload the `.skill` file (Option B). For a team on Claude Code or Cowork, install the plugin (Option A) to get the hook and one version for everyone.

### Plugin vs `.skill`

| | Plugin | `.skill` upload |
|---|---|---|
| Skill instructions | ✅ | ✅ |
| Re-check hook | ✅ Checks every message you send. When you say *"added to the group"* or *"check again"*, Claude gets a reminder to re-inventory the tabs before it replies | ❌ Depends on Claude remembering a rule from the skill text, deep into a long session |
| Version number | ✅ `plugin.json` carries a version, so you can tell which build each person is on | ❌ No version; it's easy to end up with two copies of `qa-test-design` that compete with each other |
| Team rollout | ✅ One install line, the same build for everyone | ⚠️ Each person uploads and updates the file by hand |
| Where it runs | Claude Code (with `--chrome`), Cowork | claude.ai web, desktop and the Chrome side panel |

The re-check hook matters more than it looks. A typical session is long: reading the ticket, the subtasks, two rounds of questions, then running the tests. By the time you drag in a spec page you forgot, the original instructions are far back in the conversation. The hook doesn't rely on Claude remembering them. It sees the phrase in your message and puts the reminder right next to it.

Without the hook, the re-check rule is still in the skill text, so it still re-inventories when you ask, just less reliably.

### What you need

| Tool | Needed? | Used for | Without it |
|---|---|---|---|
| Claude in Chrome extension | **Required** | Reading your tabs and driving the test environment | Doesn't work |
| Jira connector | Recommended | Full description, all comments, linked tickets, attachments | Reads the page in the browser; collapsed comments can be missed |
| Notion connector | Recommended | Spec pages and page comments | Reads the page in the browser and has to expand every toggle |
| Google Drive connector | Optional | Reading Google Sheets reliably | Reads the sheet from screenshots |
| Playwright MCP | Optional | Opening and parsing attachments | Falls back to the connector, then Chrome |
| `python3` | Plugin only | Running the re-check hook | The hook doesn't run; the skill still works |

When it falls back to the browser, it tells you which sources it read that way.

### Option A: Plugin (Claude Code, Cowork), recommended for teams

In Claude Code (2.1.275 or later):

```
/plugin install qa-test-design --marketplace BobChochola/claude-qa-test-design
```

Then start Claude Code with Chrome enabled: `claude --chrome`.

Or try it from a local clone without installing:

```bash
git clone https://github.com/BobChochola/claude-qa-test-design.git
claude --chrome --plugin-dir ./claude-qa-test-design
```

The layout:

```
claude-qa-test-design/
├── .claude-plugin/
│   ├── plugin.json                # name and version; bump the version on every update
│   └── marketplace.json           # lets people install straight from this repo
├── skills/qa-test-design/SKILL.md
└── hooks/
    ├── hooks.json                 # UserPromptSubmit hook
    └── scripts/recheck_tabs.py    # detects "added to the group" / "check again"
```

To check the hook, start Claude with `--debug`, send *"added to the group"*, and look for the `UserPromptSubmit` hook in the log. The hook only adds a reminder when your message matches a re-check phrase. It never blocks a message and stays silent otherwise.

### Option B: claude.ai (web, desktop, Chrome side panel)

1. Download `qa-test-design.skill` from [`dist/`](dist/) or the latest release.
2. In Claude, go to **Settings → Capabilities → Skills** and upload it.
3. If you already have an older `qa-test-design`, replace it instead of keeping both. Two copies compete for the same trigger.

## Use it

### 1. Open the tabs

Put everything it should read into **one Chrome tab group**:

- the Jira ticket
- the spec pages (Notion, Google Sheets, anything else)
- the test environment, logged in, if you want it to run the tests

It only reads what's in the group. It won't go searching for pages on its own.

### 2. Start it

In Claude Code or the Claude side panel:

```
/qa-test-design Read <ticket URL>
```

- **Design only:** stop there. You get test cases with Result set to `Not Run`.
- **Design and run:** add **"and test it"**. It runs the cases in the test environment and fills in Actual and Result.

### 3. Let it read

Nothing to do here. It will:

1. List every tab in the group and say whether it reads each one through a connector or the browser.
2. Read the Jira description, every comment and every linked ticket, including the description and comments of BE / FE / DevOps subtasks.
3. Read the spec pages and their comments.
4. Look at every image and open every attachment.

Decisions PM or RD made in comments are treated as spec, and the test case cites the comment as its source.

### 4. Answer its questions

It asks only after it has read everything: multiple choice, up to four per round, with another round if your answers raise new questions. A typical first round:

> The AC says customers get a loyalty coupon, but BE subtask SHOP-150 switches it to a promo coupon. Which one should the tests expect?
> Can I submit real grants in staging? If so, only to which test accounts?
> Besides the admin UI, what can I use to verify the result?
> What format do you want the test cases in?

When everything is answered, it tells you so and starts writing cases.

### 5. Missing a page?

If the ticket mentions a spec that isn't in the group, it asks you to drag that tab in. Once you have, say one of these and it re-inventories the group, reads the new tabs and asks a follow-up round:

```
added to the group
added the tab
check again
re-check the tabs
我有幫你加進 group
分頁加好了
請再確認
重新盤點
```

The plugin hook matches a fixed list of phrases (see [`recheck_tabs.py`](hooks/scripts/recheck_tabs.py)). If you phrase it differently, the skill rule usually still catches it, but the hook won't add its reminder. Add your team's phrasing to the list if you need to.

## For developers: self-test before handing off

The skill isn't only for QA. A developer can run it on their own ticket before moving it to QA:

1. Open the ticket, its subtasks and spec, and the dev or staging environment in one tab group.
2. Run `/qa-test-design Read <ticket URL> and test it`.
3. Answer its questions. They often surface what the developer assumed but the ticket never said.
4. Fix what fails, then hand the ticket to QA with the spreadsheet attached.

Developers and QA end up working from the same reading of the requirement, including the decisions buried in comments. QA starts from a list of known gaps instead of rediscovering them, and the review conversation moves from "did you consider…" to "here's what's still open".

## Guardrails

- **Writes need your OK.** Before any step that changes data in the environment under test (submitting a form, issuing a coupon, sending a message), it lists the exact parameters and waits for you to confirm.
- **Read-only on your docs.** It never edits Jira, Notion or Sheets unless you ask.
- **Personal data stays out.** If an attachment contains names, emails or phone numbers, it warns you and only reports counts.
- **No silent gaps.** If a page can't be read (no permission, a canvas-rendered prototype, an iframe), the result says so.

## Customize

Everything is in [`skills/qa-test-design/SKILL.md`](skills/qa-test-design/SKILL.md), in plain English. Common changes:

- **Language**: replies follow the language you write in, including sheet names and status labels. Pin a language in the "Reply in the user's language" rule if you need one.
- **Columns**: edit the table in *Step 6: Deliver as a spreadsheet*.
- **Sources**: add your own source types (Confluence, Linear, Figma) under *Step 2*.
- **Jira fields**: Step 2 asks for status, Fix version and priority. Name the custom fields your project uses (risk, platform, team) so it always fetches them.

If you install the plugin, bump the version in `.claude-plugin/plugin.json` after each change so everyone can tell which build they're on.

## Limitations

- It tests what it can see and call. Logs, DB state and fault injection still need someone with access, and it marks those cases `Blocked` or `Needs Review` instead of guessing.
- Results are only as current as the tabs you opened. Re-run after the spec changes.
- Review every `Fail` before filing it. It's usually right about what happened; whether that's a bug is your call.

## Contributing

Issues and PRs are welcome, especially new source types, better attachment handling, and examples from your own domain with real data removed.

## License

[MIT](LICENSE)
