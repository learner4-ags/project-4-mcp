# Mini-project 4 — MCP Prompts + Resources for API Contract Migration

**Duration:** ~3 h 40 min  **Level:** intermediate  **Tools:** VS Code, GitHub Copilot (agent mode), Python 3.11+, Node 18+

> **Spotlight:** In this lab the MCP server exposes **no action tools**. It offers only two of the three MCP primitives:
> - **Resources** — read-only, versioned context the *application* (or you) attaches to the conversation.
> - **Prompts** — reusable, parameterised instructions the *user* invokes as a slash command.
>
> The point: you can make an AI assistant dramatically more reliable by controlling *what it knows* and *how it is asked*, without giving it any new powers.

---

## Table of contents

1. [Why this lab matters (value propositions)](#1-why-this-lab-matters)
2. [Tools vs Resources vs Prompts](#2-tools-vs-resources-vs-prompts)
3. [What is in the starter project](#3-whats-in-the-starter-project)
4. [Part A — Common setup (first 15 min)](#4-part-a--common-setup-first-15-minutes)
5. [Part B — Establish the BEFORE baseline](#5-part-b--establish-the-before-baseline-do-this-first)
6. [Part C — Configure the hpe-contracts MCP server](#6-part-c--configure-the-hpe-contracts-mcp-server-015040)
7. [Part D — Browse and attach the resource](#7-part-d--browse-and-attach-the-resource-040100)
8. [Part E — Invoke the prompt](#8-part-e--invoke-the-prompt-100115)
9. [Part F — Let Copilot migrate API + UI + tests](#9-part-f--let-copilot-migrate-api--ui--tests-115220)
10. [Part G — Verify with pytest and Playwright](#10-part-g--verify-with-pytest-and-playwright-220250)
11. [Part H — The control experiment (AFTER vs. "no MCP")](#11-part-h--the-control-experiment-optional-but-recommended)
12. [Part I — Prepare the PR and record provenance](#12-part-i--prepare-the-pr-and-record-provenance-250320)
13. [Part J — Debrief](#13-part-j--debrief-320340)
14. [Troubleshooting](#14-troubleshooting)
15. [Appendix — Evidence checklist](#15-appendix--evidence-checklist)

---

## 1. Why this lab matters

### The problem
AI coding assistants are strong at writing code but weak at knowing **your organisation's current truth**. When asked to "migrate the thermal API to v2", an assistant without access to the contract will:

- **Guess** field names (`temperature`, `TempCelsius`, `Reading`…).
- **Invent** health thresholds (is 75 °C OK or Warning?).
- **Miss** compatibility rules (e.g., "`TempC` must no longer be emitted").
- **Vary** run to run, person to person — one engineer's prompt is not another's.

Each of these produces a plausible-looking diff that fails at integration time or, worse, passes review.

### What MCP prompts + resources give you

| Capability | What it is in this lab | Value proposition |
|---|---|---|
| **Resource** `contract://thermal/v2` | A read-only JSON contract: field names, types, health rules, deprecation note | **Single source of truth.** The assistant reads the authoritative spec instead of guessing. When the contract changes, every consumer picks it up on next attach — no copy-paste, no stale wiki pages. |
| **Resource** `standard://api-errors` | A markdown org standard for error payloads | **Standards travel with the work.** Cross-cutting rules (error shape, no stack traces) can be attached on demand without bloating every prompt. |
| **Prompt** `implement_thermal_v2` | A parameterised slash command with vetted wording | **Repeatable, reviewable instructions.** The team's best prompt is versioned in code, reviewed like code, and gives the same instructions to everyone. Encodes *process* (inspect first, minimal change, add Playwright test, summarise compatibility impact). |
| **No action tools** | Server cannot write files, call APIs, or run commands | **Least privilege.** Nothing in this server can change anything. Security teams can approve it quickly; the blast radius is zero. |
| **User-controlled invocation** | You pick the resource and the slash command | **Human stays in the loop.** Unlike tools (model-decided), you decide what context and instruction go in. |

### Business outcomes
- **Fewer review cycles** — the diff matches the contract the first time.
- **Consistency across teams** — same prompt, same contract, comparable output.
- **Auditability** — the PR can state exactly which contract version and prompt produced the change.
- **Fast onboarding** — new engineers get the team's best practice by typing `/`.

---

## 2. Tools vs Resources vs Prompts

Keep this table in mind; you will be asked to fill it in from experience during the debrief.

| | **Tools** | **Resources** | **Prompts** |
|---|---|---|---|
| Who decides to use it? | The **model** | The **application / user** | The **user** |
| What does it do? | Performs an action or computation (side effects possible) | Supplies read-only data/context | Supplies a templated instruction |
| Typical examples | `create_ticket`, `run_query`, `restart_server` | Contract JSON, runbook, schema, log excerpt | `/implement_thermal_v2`, `/write-release-notes` |
| Risk profile | Highest — can change the world | Low — read-only | Low — just text |
| Identified by | name + JSON schema | URI (`contract://thermal/v2`) | name + arguments |
| Appears in VS Code as | Tools picker, model-invoked | *MCP: Browse Resources*, **Add Context → MCP Resources** | Slash command in chat |
| **Used in this lab** | ❌ none | ✅ 2 | ✅ 1 |

**Rule of thumb:** *Need the model to know something?* → resource. *Need everyone to ask the same way?* → prompt. *Need something to happen?* → tool.

---

## 3. What's in the starter project

| Path | Purpose |
|---|---|
| `app/main.py` | FastAPI app. `GET /api/thermal` returns the **legacy v1** shape `{"Sensor":"CPU1","TempC":72.0}`. `GET /` serves an HTML page with an *Unknown* grey health badge. |
| `tests/test_api.py` | Unit test asserting the **legacy** v1 shape. |
| `tests/ui/smoke.spec.ts` | Playwright smoke test asserting heading + reading `72`. |
| `mcp_server/server.py` | The **hpe-contracts** MCP server (2 resources, 1 prompt, 0 tools). |
| `mcp_server/data/thermal_v2.json` | The v2 contract. |
| `mcp_server/data/api_error_standard.md` | Org error-payload standard. |
| `lab-assets/mcp.windows.json` | Template for the VS Code MCP config. |
| `work-items/MP4.md` | The work item (read this before prompting). |
| `.github/copilot-instructions.md` | Guard-rails Copilot follows: inspect first, minimal change, never weaken tests, report files/tests/assumptions/risks. |

### The v2 contract at a glance

```json
{
  "name": "ThermalReadingV2",
  "fields": { "Sensor": "string", "ReadingCelsius": "number", "Health": "OK|Warning|Critical" },
  "health_rules": { "OK": "<75", "Warning": "75-84.9", "Critical": ">=85" },
  "compatibility_note": "TempC is deprecated and should not be emitted by v2."
}
```

> ⚠️ **Note the boundary:** the contract says OK is **`<75`**. The starter reading is **72 °C → `OK`**. A guessed rule such as "OK up to 80" would still pass that one sample but be wrong elsewhere — which is why boundary tests matter (Part G).

---

## 4. Part A — Common setup (first 15 minutes)

Every team starts here.

1. Go to **https://github.com/new** and create a new **private** repository. **Do not** initialise it with a README.
2. Unzip this starter project locally and open a terminal in the project folder.
3. Push the starter to your new repo:

   ```bash
   git init
   git add .
   git commit -m "lab: starter application"
   git branch -M main
   git remote add origin <YOUR-NEW-REPO-URL>
   git push -u origin main
   ```

4. Open the folder in VS Code and sign in to GitHub Copilot (bottom-left account icon → *Sign in to use Copilot*).
5. Create the Python environment (PowerShell):

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

   > If activation is blocked: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then re-run.

6. Install UI test dependencies:

   ```bash
   npm install
   npx playwright install chromium
   ```

7. Run `pytest -q` — confirm the starter is **green** (1 passed).
8. Read `work-items/MP4.md` **before** asking Copilot to change anything.
9. Create a working branch so the PR in Part I is clean:

   ```bash
   git checkout -b feature/thermal-v2
   ```

✅ **Checkpoint:** `pytest -q` passes; `git status` is clean; you are on `feature/thermal-v2`.

---

## 5. Part B — Establish the BEFORE baseline (do this first)

You can only appreciate the value of MCP context if you have seen the starting point **and** what an assistant does without it. Capture these now; you will compare in Part G/H.

### B1. See the legacy behaviour

Start the app in a second terminal:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Then:

```powershell
curl http://127.0.0.1:8000/api/thermal
```

Open http://127.0.0.1:8000 in a browser.

**Record your BEFORE observations:**

| Item | BEFORE (starter) |
|---|---|
| JSON from `/api/thermal` | `{"Sensor":"CPU1","TempC":72.0}` |
| Field for temperature | `TempC` |
| `Health` field present? | ❌ No |
| UI badge text | `Unknown` (grey, never updates) |
| Unit test asserts | `TempC == 72.0` |
| UI test asserts | reading text is `72` (badge never checked) |

Take a screenshot of the browser — you will want it for the PR.

### B2. (Recommended) See what Copilot does *without* MCP

This is the "control". **Do not configure MCP yet.**

1. Open a **new** Copilot chat in **Agent** mode.
2. Paste exactly:

   > Migrate the thermal API and UI to the new v2 format. Add a health indicator.

3. **Do not accept/apply the changes.** Read the plan or proposed diff, then note:

   | Question | Copilot's answer without MCP |
   |---|---|
   | What did it name the temperature field? | _e.g._ `Temperature`, `TempCelsius`, kept `TempC` … |
   | What thresholds did it invent for health? | _e.g._ OK ≤ 70? Warning ≤ 90? |
   | What values did it use for `Health`? | _e.g._ `"normal"`, `"hot"`, `"ok"` … |
   | Did it keep `TempC`? | _yes/no_ |
   | Did it ask where the spec is? | _yes/no_ |

4. **Discard** the proposed changes (`git restore .` / *Undo* in the chat panel) so you start Part C from a clean tree.

> 💡 **Why this matters:** the answers above are the assistant's *best guess*. They may look reasonable — and be wrong. You have no way to know from the diff alone because the real spec isn't in the context.

✅ **Checkpoint:** a filled-in BEFORE table, a browser screenshot, a clean `git status`. Stop the app (Ctrl+C) when finished.

---

## 6. Part C — Configure the hpe-contracts MCP server (0:15–0:40)

### What you are doing
Telling VS Code how to launch the MCP server as a child process (**stdio** transport) so Copilot can ask it for resources and prompts.

### Steps

1. Look at `mcp_server/server.py`. Before running anything, answer for yourself:
   - How many `@mcp.resource` declarations? **2** (`contract://thermal/v2`, `standard://api-errors`)
   - How many `@mcp.prompt`? **1** (`implement_thermal_v2`)
   - How many `@mcp.tool`? **0** → this server cannot *do* anything.

2. In the project root create the folder `.vscode` and a file `.vscode/mcp.json`. Copy the content of `lab-assets/mcp.windows.json` and replace **both** `<ABSOLUTE_PATH_TO_REPO>` placeholders with your repo's absolute path (use double backslashes in JSON). Example:

   ```json
   {
     "servers": {
       "hpe-contracts": {
         "type": "stdio",
         "command": "C:\\Users\\you\\labs\\thermal\\.venv\\Scripts\\python.exe",
         "args": ["C:\\Users\\you\\labs\\thermal\\mcp_server\\server.py"]
       }
     }
   }
   ```

   > Use the **venv's** `python.exe`, not system Python — only the venv has the `mcp` package installed.

3. VS Code shows small **Start | Stop | Restart | More…** CodeLens actions above the `"hpe-contracts"` entry. Click **Start**.
4. Click **More… → Show Output** (or **View → Output → MCP: hpe-contracts**) and confirm there are no import or path errors.
5. Open the Command Palette (`Ctrl+Shift+P`) → **MCP: List Servers** → select `hpe-contracts` → confirm status **Running**.
6. (Optional) Inspect with the MCP developer CLI to see exactly what the server advertises:

   ```powershell
   mcp dev mcp_server/server.py
   ```
   Check the **Resources** and **Prompts** tabs; the **Tools** tab should be empty.

### Expected result
Server **Running**; output log shows initialisation with no traceback.

### 🔎 Value highlight — zero-power server
Open the **Tools** list in the Copilot chat tools picker (the 🛠 icon). `hpe-contracts` contributes **no tools**. That means you can safely hand this server to any engineer: it cannot write, delete, call out, or execute. Compare this with a typical "give the agent a shell/DB tool" setup, where every capability must be reviewed and trusted.

✅ **Checkpoint:** `hpe-contracts` is Running and the tools picker shows no tools from it.

---

## 7. Part D — Browse and attach the resource (0:40–1:00)

### What you are doing
Using a **resource** — the read-only, URI-addressed context primitive — and putting it into the chat deliberately.

### Steps

1. Command Palette → **MCP: Browse Resources…** → choose `hpe-contracts`.
2. You should see two entries:
   - `contract://thermal/v2` (application/json)
   - `standard://api-errors` (text/markdown)
3. Select **`contract://thermal/v2`**. VS Code opens it in an editor tab. Read it and confirm it matches section 3 of this guide.
4. Open Copilot chat (Agent mode) → click **Add Context…** (paperclip / `+`) → **MCP Resources** → pick `contract://thermal/v2`. A chip for the resource appears in the chat input.

   > If you cannot find it: Add Context → *Tools…* is not the right place; resources live under **MCP Resources**. Update VS Code if the entry is missing.

5. Test that the contract is truly in context. Ask (and send **only** this question — do not ask for code yet):

   > Using only the attached resource, list the v2 field names, the Health values, and the exact threshold for each Health value. What happens to `TempC`?

   Expected answer: `Sensor`, `ReadingCelsius`, `Health`; OK `<75`, Warning `75–84.9`, Critical `>=85`; `TempC` is deprecated and must not be emitted.

6. Try the second resource: ask Copilot to attach `standard://api-errors` and summarise it in one sentence. (You will not need it for the happy path, but note how the *same mechanism* delivers any org standard.)

### BEFORE → AFTER (context)

| | BEFORE (Part B2, no MCP) | AFTER (resource attached) |
|---|---|---|
| Where do field names come from? | Model's guess | `contract://thermal/v2` |
| Where do thresholds come from? | Model's guess | `health_rules` in the contract |
| Is `TempC` handled correctly? | Unknown / varies | Explicitly deprecated |
| Can a reviewer see the source? | No | Yes — a named, versioned URI |
| If the contract changes tomorrow | Everyone's prompts silently stale | Re-attach → new truth |

### 🔎 Value highlight — resources are user-controlled and read-only
You chose to attach this. The model did not fetch it autonomously, and it cannot modify it. You get grounding **without** giving up control.

✅ **Checkpoint:** Copilot correctly recites the contract from the attached resource.

---

## 8. Part E — Invoke the prompt (1:00–1:15)

### What you are doing
Using an MCP **prompt** — a user-invoked, parameterised instruction template — instead of writing your own ad-hoc request.

### Steps

1. In the Copilot chat input, type `/` and look for the MCP prompt. In VS Code, MCP prompts are namespaced as **`/mcp.<server>.<prompt>`**, so look for:

   ```
   /mcp.hpe-contracts.implement_thermal_v2
   ```
   (The lab text may call this `/hpe-contracts.implement_thermal_v2` — if the exact name differs, type `/hpe` or `/implement` and use the completion list.)

2. Select it. VS Code prompts you for the `component` argument (default **`API and UI`**). Press Enter to accept the default.
3. **Before you send**, read the text that was inserted. It should be:

   > Implement ThermalReadingV2 for API and UI. First attach/read resource contract://thermal/v2. Update API, UI, and tests consistently. Create a Playwright UI acceptance test that verifies the Health badge. Keep the change minimal and summarize compatibility impact before editing.

4. Notice what this one command encodes:

   | Instruction in the prompt | Why it is there |
   |---|---|
   | "First attach/read resource `contract://thermal/v2`" | Forces grounding before coding |
   | "Update API, UI, and tests **consistently**" | Prevents half-migrations (API changed, UI/tests stale) |
   | "Create a Playwright UI acceptance test that verifies the Health badge" | Bakes in test-first acceptance evidence |
   | "Keep the change minimal" | Limits scope creep |
   | "Summarize compatibility impact **before editing**" | Gives you a checkpoint to catch breaking changes |

5. Make sure the `contract://thermal/v2` chip is still attached, then **Send**.

### BEFORE → AFTER (instructions)

| | BEFORE (hand-written ask) | AFTER (MCP prompt) |
|---|---|---|
| Wording | "Migrate to v2 and add health" | Vetted, process-aware template |
| Mentions the contract? | No | Yes, by URI |
| Requires UI acceptance test? | Only if you remember | Always |
| Asks for impact summary first? | Rarely | Always |
| Same across teammates? | No | Yes — versioned in `server.py` |
| How is it improved? | Everyone re-learns | Edit once, everyone gets it |

### 🔎 Value highlight — prompts as shared team playbooks
The prompt is **code in the repo** (`mcp_server/server.py`). It can be code-reviewed, versioned, tested, and parameterised. It turns tribal knowledge ("always ask for a Playwright test") into a one-keystroke default.

✅ **Checkpoint:** Copilot responds first with a **compatibility-impact summary** (not edits) that references the contract.

---

## 9. Part F — Let Copilot migrate API + UI + tests (1:15–2:20)

### What you are doing
Supervising an agent that is now properly grounded (resource) and properly instructed (prompt). Your job is review, not authoring.

### Steps

1. **Read the impact summary.** Check that it says:
   - `TempC` will be removed from the response (breaking for v1 consumers).
   - New fields: `Sensor`, `ReadingCelsius`, `Health`.
   - UI will read `ReadingCelsius` and render `Health`.
   - Existing legacy tests will be *replaced by v2 equivalents* (not deleted to force green — see `.github/copilot-instructions.md`).
   If it proposes keeping `TempC` or inventing thresholds, reply: *"Re-read contract://thermal/v2 — TempC must not be emitted and thresholds are exactly as specified."*
2. Approve it to proceed. Watch for tool calls (file edits, terminal) and approve each deliberately.
3. When Copilot finishes, **review the diff** (Source Control panel). Use this checklist:

   **`app/main.py`**
   - [ ] Response keys are exactly `Sensor`, `ReadingCelsius`, `Health`.
   - [ ] `TempC` is **not** emitted.
   - [ ] `Health` logic: `<75` → `OK`; `75 ≤ x < 85` → `Warning`; `≥85` → `Critical`. Boundaries `75` and `85` land in the upper bucket.
   - [ ] 72.0 → `"OK"`.
   - [ ] HTML/JS reads `x.ReadingCelsius` (not `x.TempC`) and sets `#health` text (and ideally a class/colour per state).

   **`tests/test_api.py`**
   - [ ] Legacy `TempC` assertion replaced (not just deleted) with v2 assertions.
   - [ ] Ideally a parametrised boundary test: 74.9→OK, 75→Warning, 84.9→Warning, 85→Critical.

   **`tests/ui/`**
   - [ ] A new/updated Playwright test checks `#health` shows `OK` for the 72 °C sample.

4. If something is off, **correct via chat** (keep the resource attached); don't hand-edit unless necessary. Note each correction — they are good debrief material.

### Expected result (target behaviour)

```json
{"Sensor":"CPU1","ReadingCelsius":72.0,"Health":"OK"}
```

### BEFORE → AFTER (code behaviour)

| Aspect | BEFORE | AFTER |
|---|---|---|
| `/api/thermal` JSON | `{"Sensor":"CPU1","TempC":72.0}` | `{"Sensor":"CPU1","ReadingCelsius":72.0,"Health":"OK"}` |
| Temperature field | `TempC` | `ReadingCelsius` |
| Health in API | none | `OK` / `Warning` / `Critical` per contract |
| UI badge | `Unknown` (static grey) | `OK` (reflects API) |
| Unit tests | assert `TempC == 72.0` | assert v2 shape + health rules |
| UI test | heading + reading text only | + `#health` badge assertion |
| Spec traceability | none | contract URI cited in PR |

✅ **Checkpoint:** diff reviewed against the checklist; all corrections noted.

---

## 10. Part G — Verify with pytest and Playwright (2:20–2:50)

### Steps

1. Targeted verifier first, then full suite:

   ```powershell
   pytest -q tests/test_api.py
   pytest -q
   ```

2. Run the UI tests (Playwright starts uvicorn for you through `playwright.config.ts`):

   ```powershell
   npm run test:ui
   ```
   Watch it in a real browser if you like:
   ```powershell
   npm run test:ui:headed
   ```

3. Manually confirm:

   ```powershell
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   curl http://127.0.0.1:8000/api/thermal
   ```
   Open http://127.0.0.1:8000 — the badge should read **OK**. Screenshot it next to your BEFORE screenshot.

4. **Boundary spot-check (independent of Copilot).** Temporarily change `SAMPLE`'s reading to each value below, reload, and confirm the badge. Revert afterwards (`git diff` must not show this change).

   | Reading (°C) | Expected `Health` |
   |---|---|
   | 74.9 | OK |
   | 75.0 | Warning |
   | 84.9 | Warning |
   | 85.0 | Critical |

   If your boundaries disagree, the code (not the contract) is wrong — ask Copilot to fix and add a test.

5. **Mutation check (proves the new test is real).** Temporarily make the UI set the badge text to a wrong value (or comment out the `#health` update). Re-run `npm run test:ui`. The Playwright test **must fail**. Revert. A test that cannot fail is not evidence.

### Expected result
All unit tests and Playwright tests pass; the mutation makes the new Playwright test fail; boundaries behave per contract.

✅ **Checkpoint:** screenshots of green test output + AFTER browser view.

---

## 11. Part H — The control experiment (optional but recommended)

Goal: prove to yourself that the *MCP context*, not luck, caused the correct result.

1. Stash or commit your work, then create a throw-away branch from the starter commit:
   ```bash
   git stash -u            # or commit on feature branch
   git checkout -b experiment/no-mcp main
   ```
2. In VS Code, **Stop** the `hpe-contracts` server (MCP: List Servers → Stop) and start a **new** chat with no resource attached.
3. Ask the hand-written request from B2 plus: *"Add a Playwright test for the badge."*
4. Compare the output to your MCP-driven branch:

   | | No MCP | With MCP resource + prompt |
   |---|---|---|
   | Field names match contract? | | |
   | Thresholds match contract? | | |
   | `TempC` removed? | | |
   | Boundary tests present? | | |
   | Impact summary given first? | | |
   | Edits you had to correct | | |

5. Clean up: discard the experiment branch and return to `feature/thermal-v2` (`git checkout feature/thermal-v2`; `git stash pop` if used). Restart the MCP server.

> 📌 Variation is expected: some runs will happen to guess right. The value of MCP is not that the unguided run *always* fails — it is that the guided run *cannot silently drift* from the contract, and you can **prove** where its requirements came from.

---

## 12. Part I — Prepare the PR and record provenance (2:50–3:20)

### Steps

1. Review your final diff once more: `git diff main --stat` and read it fully.
2. Commit and push:

   ```bash
   git add -A
   git commit -m "feat: migrate thermal API + UI to ThermalReadingV2"
   git push -u origin feature/thermal-v2
   ```
3. Open a Pull Request on GitHub. Use this template — the **MCP provenance** section is mandatory for the lab:

   ```markdown
   ## Summary
   Migrates the thermal API and UI from legacy v1 (`TempC`) to ThermalReadingV2.

   ## MCP provenance
   - **MCP server:** hpe-contracts (stdio, no action tools)
   - **Resource used:** `contract://thermal/v2` (attached as chat context)
   - **Other resources consulted:** `standard://api-errors` (optional)
   - **Prompt used:** `implement_thermal_v2` (argument: component = "API and UI")

   ## Behaviour change (BEFORE → AFTER)
   | | Before | After |
   |---|---|---|
   | `/api/thermal` | `{"Sensor":"CPU1","TempC":72.0}` | `{"Sensor":"CPU1","ReadingCelsius":72.0,"Health":"OK"}` |
   | UI badge | Unknown | OK |

   ## Compatibility impact
   `TempC` is no longer emitted (breaking for v1 consumers, per contract compatibility_note).

   ## Health rule verification
   OK <75, Warning 75–84.9, Critical >=85; boundary values tested: 74.9 / 75 / 84.9 / 85.

   ## Tests run
   - pytest -q → N passed
   - npm run test:ui → N passed
   - Mutation check: new UI test fails when badge is broken ✔

   ## Files changed
   (list)

   ## Assumptions & risks
   (list — e.g. no v1 compatibility shim; consumers must migrate)

   ## Human review
   Not merged until a reviewer has read the diff and test evidence.
   ```
4. Attach your BEFORE and AFTER screenshots to the PR.
5. **Stop before merging.** Per `.github/copilot-instructions.md`, a human reviews the diff and evidence.

✅ **Checkpoint:** PR open, MCP provenance filled in, no merge.

---

## 13. Part J — Debrief (3:20–3:40)

Discuss in your team, then share with the room.

1. **Tools vs resources vs prompts.** Without looking at section 2, say which primitive you would use for each, and who controls it:
   - "Attach the current Redfish schema to the chat." → *resource (user/app)*
   - "Open a Jira ticket for this finding." → *tool (model)*
   - "Everyone should request release notes in the same format." → *prompt (user)*
   - "Restart the BMC simulator." → *tool*
2. **What changed between your B2 run and your final run?** Which of the five differences in the table in Part H mattered most?
3. **Where did the assistant need correction even with MCP?** What does that say about the need for tests and human review?
4. **Security.** Why is a resources+prompts-only server easier to approve than one with tools? What would change if we added a `deploy` tool?
5. **Governance.** If the contract changes to v3, what is the update process? (Edit `thermal_v3.json`/resource → review → merge; no engineer needs to retrain or re-prompt.) What would you add to `server.py` next — resource versions? a `/review_against_contract` prompt?
6. **Where in your own work** is there a document everyone pastes into prompts today? That is your first candidate MCP resource. What is the prompt everyone rewrites? That is your first MCP prompt.

### Key takeaways

- **Resources ground the model** in authoritative, versioned, read-only facts — and are chosen by you.
- **Prompts standardise the ask** — shared, reviewable, parameterised playbooks that encode your process.
- **No tools = least privilege** — real value with a near-zero security footprint.
- **Provenance** — the PR can say exactly which contract and prompt produced the change.
- **Tests and review remain essential** — MCP raises first-pass quality; it does not replace verification.

---

## 14. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Server won't start; `ModuleNotFoundError: mcp` | `mcp.json` points to system Python | Use `.venv\Scripts\python.exe` and re-run `pip install -r requirements.txt` in the venv |
| `ImportError: cannot import name 'MCPServer'` | `mcp` version mismatch | `pip install "mcp[cli]>=2,<3"`; check `pip show mcp` |
| JSON error in `mcp.json` | Single backslashes in paths | Use `\\` in JSON strings |
| *MCP: Browse Resources* shows nothing | Server not running | MCP: List Servers → Start; check Output log |
| No MCP resource under Add Context | Old VS Code / Copilot | Update VS Code and Copilot extensions; enable MCP in settings (organisation policy may disable it) |
| Prompt not under `/` | Naming differs | Type `/mcp.` or `/hpe`; restart the server; reload window |
| Copilot ignores the contract | Resource chip not attached after clicking the prompt | Re-attach `contract://thermal/v2`, resend |
| Playwright can't start server | Port 8000 busy or Python not on PATH | Stop other uvicorn; activate the venv before `npm run test:ui` |
| Playwright browser missing | Skipped install | `npx playwright install chromium` |
| `pytest` fails after migration on `TempC` | Legacy test still present | Replace with v2 assertions — don't weaken or delete the check without replacement |

---

## 15. Appendix — Evidence checklist

Collect before leaving the lab:

- [ ] BEFORE table (Part B1) and screenshot
- [ ] B2 "no-MCP" observations table
- [ ] `hpe-contracts` shown Running with **no tools**
- [ ] Screenshot of `contract://thermal/v2` attached as chat context
- [ ] Screenshot of the prompt invoked via slash command
- [ ] Copilot's compatibility-impact summary
- [ ] Final diff reviewed against the Part F checklist
- [ ] `pytest -q` and `npm run test:ui` green
- [ ] Boundary spot-check and mutation check done
- [ ] AFTER screenshot (badge = OK)
- [ ] PR with MCP provenance section filled in, **not merged**
- [ ] Debrief answers
