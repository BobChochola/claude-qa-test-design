---
name: "qa-test-design"
description: "Design QA test cases from requirements: read every tab in the Chrome tab group (Jira, Notion, Google Sheets) and every requirement image, reading Jira, Notion, and Sheets through a connector first and the browser as fallback, clarify all questions at once, then write test cases in a spreadsheet. Use when requirements are open in Claude's Chrome tab group or the user asks to design, review, or run test cases. Replies in the user's language."
compatibility: "Requires read-only access to the relevant browser tabs; use approved Jira, Notion, or Google Sheets connectors when available."
---

# Requirements → QA Test Cases

Use this when QA receives one or more requirement documents and needs to design test cases or get ready to test. Sources may be Jira tickets, Notion pages, Google Sheets, or any mix of them.

## Hard rules (never skip)

1. **Read every tab in the same tab group first.** Before any analysis, call `tabs_context_mcp` to list all tabs in Claude's tab group, and read every one of them regardless of source. The tab group is the primary reading scope. If a document the user mentions, or a spec page or ticket that Jira / Notion text only refers to, is not in the group, do not search for it outside the group; ask the user in Step 4 to drag that tab into the group. Never answer only from text pasted into the chat.
2. **Connector first, browser as fallback.** For Jira, Notion, and Google Sheets, read text through a connector when one is available; use the browser only when there is no connector or the connector call fails. Images are always viewed in the browser.
3. **Read every image.** Attachments, inline screenshots, sequence diagrams, flowcharts, design mockups, and images inside spreadsheet cells must all actually be viewed. Key information (repro steps, root cause, log query conditions, UI specs) often exists only in images.
4. **Read every attachment in full.** Every Jira and Notion attachment (CSV, xlsx, PDF, docx, images, zip, etc.) must be opened and its content understood; a file name is never enough. Open or download it with Playwright MCP first; if Playwright MCP is unavailable, use the connector's attachment-content API; only if that also fails, use Chrome. State which method read each attachment. Summarize each one (purpose, format, row count, key fields, fit with the AC) and turn every mismatch into a question or defect (Step 3b). If an attachment contains personal data (names, emails, phone numbers, etc.), warn the user and cite only aggregate numbers; never reproduce raw personal data in any output.
5. **Ask all clarifying questions at once, only after reading every document.** While reading, only record questions; do not ask mid-way. After everything is read, ask them all with `AskUserQuestion`. If the answers raise new questions, ask another round. Repeat until no open questions remain, and only then write test cases or start testing.
6. **Re-inventory when the user adds tabs or asks to re-check.** When the user says a tab has been added to the group or asks you to check again, immediately call `tabs_context_mcp` again and compare with the previous inventory (see "Re-inventory trigger").
7. **Reply in the user's language.** Use the language the user writes in for every reply, every `AskUserQuestion` question, and all test case output (sheet names, column headers, status labels). Keep technical terms, ticket keys, API names and log strings in their original form.

## Workflow

### Step 1: Inventory the tabs
- Use `tabs_context_mcp` to get every tab in the group; classify each by URL (Jira / Notion / Google Sheets / other).
- List each tab's source, title, role (main requirement, related requirement, spec or data sheet, environment under test), and how you will read it (connector or browser; see Step 2).
- Read multiple tabs in one `browser_batch` call to save time.
- Keep this inventory (title + URL per tab); the re-inventory trigger compares against it.

### Step 2: Read content by source

**Connector first, browser as fallback.** The Chrome tab group decides *what* to read; the connector decides *how* to read text.

- For every Jira, Notion, and Google Sheets tab, first check whether a connector for that source is available. If it is, read the text through the connector. Browser reading misses content that is collapsed, paginated, or lazy-loaded (folded comments, nested toggles, "Load more" rows, unrendered canvas cells); a connector reads by structure and does not depend on what is expanded on screen.
- Use the browser only when no connector exists or a connector call fails (no permission, not found, missing fields). State which source fell back to the browser and why.
- Images are the exception: connectors usually return only file names or captions, so always view images in the browser (Step 3).
- After a connector read, still check the result: if a toggle, heading, or field came back with only a title and no content, open it in the browser and expand it.

#### Jira
- **With a Jira connector:** take the issue key from the URL (e.g. `PROJ-123`) and fetch the issue with the connector (e.g. `getJiraIssue`). Make sure the result includes description, all comments, issue links, subtasks, attachments, status, Fix version, priority, and any custom fields your project uses for risk or scope; request missing fields explicitly.
- **Without a connector:** `get_page_text` for the full text. Comments and linked work items are often collapsed or paged on the page: click every "show more" / expand control first, then re-read the text.
- **Read the description and every comment in full.** Extract Problem / Goal, Acceptance Criteria, Discussion, and comments. Decisions by PM or RD in comments are implicit spec: adopt them as requirements when writing test cases, and cite the comment as the source.
- Record status, Fix version, priority, any risk or scope fields, and any QA subtask.
- **Read every Linked work item, including BE / FE / DevOps subtasks.** Open each one and read its description and comments, not just its title. They often reveal scope the AC does not state, e.g.:
  - affected channels or platforms
  - feature flags (test flag on, flag off, and switching between them)
  - preconditions, dedup mechanisms and TTLs
  - unfinished cleanup tickets (meaning an old code path still exists and needs regression testing)
- If an important linked ticket is not in the group and cannot be read through the connector, note it and ask in Step 4 whether to add it.
- A spec page or ticket that is only mentioned in description or comment text (not a linked work item) and is not in the group: do not search for it; record it and ask in Step 4 for the user to drag that tab into the group.
- Read every attachment by following Step 3b.

#### Notion
- **With a Notion connector:** take the page ID from the URL and fetch the spec page with the connector (e.g. `notion-fetch`). Read page comments with the connector too.
  - **Check the result:** if any toggle or collapsed heading came back with only its title and no content, open that page in the browser and expand those blocks (next bullet).
- **Without a connector:** start with `get_page_text`, then **expand every collapsed block.** Content under toggles and collapsed headings does not appear in page text. Use `find` to locate every toggle, click each open, then re-read the full text. Toggles can be nested: repeat until no collapsed block is left.
- **Sub-pages and links:** if sub-pages, backlinks, or linked database rows are relevant, read them (with the connector if available; otherwise navigate in the same tab and come back, or open a new tab and tell the user its title).
- **Database table views:** watch for filters, hidden properties, and paginated loading ("Load more"); confirm you read the complete data.
- Read page comments and discussion threads. Decisions by PM or RD in Notion comments are implicit spec, the same as in Jira.
- A page or ticket that the Notion text only mentions and that is not in the group: do not search for it; record it and ask in Step 4 for the user to drag that tab into the group.
- Read every attachment and embedded file by following Step 3b.

#### Google Sheets
- Sheets render on canvas, so `get_page_text` often misses cell content. Try in order:
  1. If a Google Drive connector is available, take the file ID from the URL and read the full content with `read_file_content`.
  2. Otherwise try `get_page_text`; if incomplete, read by scrolling and taking screenshots region by region (use `zoom` when needed).
- **Read every sheet tab**: click through each sheet tab at the bottom, not just the first.
- Watch for hidden rows/columns, filter views, cell notes and comments (cells with a corner marker), and hyperlinks.
- A sheet may be a requirement spec, an existing test case sheet, or a parameter table; identify its role first.

#### Other sources
- Try `get_page_text` first; if content is incomplete (dynamic loading, canvas, iframes), read via screenshots.

### Step 3: Read images (all sources)
- Use `find` to locate each image element, `scroll_to` it, then take a screenshot.
- If a thumbnail is unreadable, open the full-size preview and screenshot it (use `zoom` if needed); press Escape to close the preview afterwards.
- Embedded external content (Figma, Miro, video thumbnails) must also be screenshotted; if unreadable, add it to the question list.
- Write a one-line summary per image: what it tells us. Convert sequence diagrams and flowcharts into executable repro steps.
- Self-check before moving on: does the number of images read equal the number of images on each tab?

### Step 3b: Read attachments (Jira and Notion)
- List every attachment on each Jira issue, linked work item, and Notion page you read (CSV, xlsx, PDF, docx, images, zip, etc.).
- Open each one, in this order:
  1. **Playwright MCP:** open or download the attachment (e.g. navigate to the attachment URL), then read the downloaded file in full: parse CSV/xlsx, extract PDF/docx text, list zip contents and read each relevant file inside.
  2. **Connector attachment-content API:** if Playwright MCP is unavailable or cannot reach the file (no tool, not logged in, download blocked).
  3. **Chrome:** only if both of the above fail.
  State which method was used for each attachment.
- For each attachment, summarize:
  - **Purpose:** what it is for (test data, import sample, spec, log, mockup, etc.).
  - **Format:** header row or not, delimiter, encoding / BOM, sheet names for xlsx.
  - **Row count**.
  - **Key fields:** e.g. the number of distinct ID values (customer IDs, account IDs).
  - **Fit with the AC / spec:** e.g. can it be imported as-is, does it exceed a stated limit, does the format match what the spec requires.
- Every mismatch with the AC or spec becomes a question (Step 4, recorded in Open Questions) or a defect (Defects & Findings).
- If an attachment is used as test data, record it in the Test Data sheet.
- **Personal data:** if an attachment contains names, emails, phone numbers, or other personal data, warn the user, cite only aggregate numbers (counts, distinct counts), and never reproduce the raw values in chat, test cases, or the spreadsheet.
- Self-check before moving on: does the number of attachments read equal the number of attachments listed?

### Step 4: Consolidate questions and ask once
- Cross-check sources first: do numbers, scope, and terminology match across Jira AC, comments, linked work items, Notion specs, and Sheets parameters? Any mismatch becomes a question.
- Group questions: spec gaps, conflicts between sources, unclear expected behavior, test environment or tool needs, items needing RD support, deliverable format.
- Include requests for the user to drag into the group any spec page or ticket that was only mentioned in text and is not in the group.
- Ask them all with `AskUserQuestion` (max 4 per call; split into rounds if more).
- Repeat until nothing is unresolved. Then explicitly tell the user that all questions are resolved and you are starting on the test cases (e.g. "All questions are resolved. Starting on the test cases." / 「問題已釐清，開始寫測試案例」).

### Re-inventory trigger
Run this whenever the user says tabs have been added to the group or asks you to check again, at any point in the workflow. Trigger phrases include (not limited to):
- 中文：「我有幫你加進 group」「已加到 tab group」「加進群組了」「已經拖進來了」「分頁加好了」「請再確認」「再確認一次」「重新讀一下分頁」「再 survey 一次」「重新盤點」「看一下新加的 tab」
- English: "added to the group", "added the tab", "tab is in the group now", "check again", "re-check the tabs", "re-scan the tab group", "survey the tabs again"

Steps:
1. Immediately call `tabs_context_mcp` again.
2. Compare with the previous inventory and tell the user which tabs were added and which were removed.
3. Apply the full reading rules to every added tab: connector first, all comments, linked work items, images (Step 3), attachments (Step 3b).
4. Update the question list: close questions the new tabs answer, add new ones.
5. If there are new questions, ask another round with `AskUserQuestion`; when all are resolved, tell the user that all questions are resolved and you are starting on the test cases (or continue the current step).
6. Replace the previous inventory with the new one.

### Step 5: Write test cases
Group cases by AC or spec section. Cover:
- **Preconditions:** test accounts, channels, control group, baseline screenshots of current behavior.
- **Regression cases:** for bugs this requirement fixes, reconstruct precise repro steps from images or logs. For timing/race-condition bugs, state the number of repetitions (recommend ≥10).
- **Transitional behavior:** which expected results will change when a related requirement ships.
- **Not verifiable by black-box alone:** items needing RD to provide logs, API replays, or fault injection; mark them Needs Review or Blocked and record them in Open Questions.

### Step 6: Deliver as a spreadsheet
Deliver the result as a spreadsheet (.xlsx) with these five sheets, in this order. Name the sheets, columns and status labels in the user's language; the English and Traditional Chinese names are:

| Sheet | 中文 | Columns |
|---|---|---|
| Summary | 摘要 | Counts by result: Pass / Fail / Needs Review (待確認) / Blocked / Not Run, plus the total |
| Test Cases | 測試案例 | ID, Area (區塊), Source (來源), Preconditions (前置條件), Scenario (情境), Steps (步驟), Expected (預期結果), Actual (實際結果), Result (結果), Defect / Question (缺陷／問題) |
| Defects & Findings | 缺陷與發現 | ID, Severity (嚴重度), Title (標題), Related Case (對應測項), Actual (實際), Expected / Basis (預期／依據), Notes (備註) |
| Open Questions | 待確認問題 | ID, Topic (主題), Description (說明), Status (狀態) |
| Test Data | 測試資料 | File (檔案), Content (內容), Purpose (用途) |

- Area is the AC or spec section the case belongs to; Source names the document and section, comment, or linked ticket the case is based on.
- Result is one of Pass / Fail / Needs Review / Blocked / Not Run.
- Defect / Question references IDs from Defects & Findings or Open Questions.

When only designing test cases, leave Actual empty and set Result to Not Run. **If the user asks you to actually run the tests,** execute them, fill in Actual and Result for each case, record every defect in Defects & Findings with its linked case ID, and update the counts in Summary.

## Output principles
- Every inference must trace back to text or an image in a specific document. Never present unread content as fact; label it explicitly as an assumption.
- If a document cannot be read (permissions, not logged in, format issues), say which one; never silently skip it.
- Write test methods according to the tools the user actually has (black-box through the admin UI, log platform, API or mock, DB queries); confirm this in Step 4.
- Read-only: never modify Jira, Notion, or Sheets content unless the user asks.
- All replies are in the user's language.
- Before any test step that writes data in the environment under test (submitting a form, issuing coupons, sending messages), list the exact parameters and wait for the user's explicit confirmation.
