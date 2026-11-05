# Workspace setup: neuro_workspace

> **What this file is.** The full spec for the VS Code workspace I use to own and manage the product-owner-plugin (PO toolkit) as a product. Copy it onto the VDI, open Copilot Chat in agent mode, and give it the bootstrap prompt in §9. **This is the only file the bootstrap needs.** The build guide, open questions and enhancements list are optional: if they aren't in the root, the agent writes placeholders and I bring them in later (§11 task 0). The agent builds the scaffolding, and I do the manual steps in §8. Everything the scaffold leaves as a placeholder for me to fill is listed in **§11 VDI tasks**.
>
> **Status:** last updated 2026-11-04. Setting names and Copilot features change between VS Code versions, so verify each one on the VDI (§10).

---

## 1. Decisions

| # | Decision | Why |
|---|---|---|
| D1 | **Single root.** I open one folder, `neuro_workspace/`, and everything else lives under it as subfolders. | The Copilot agent window only considers the folder that's open. It has to see toolkit-kb, the plugin source and run outputs together. |
| D2 | **Include a workspace file** (`neuro_workspace.code-workspace`) that lists only `"."`, and **always open the workspace through it**, never with File → Open Folder. All workspace settings live in that file. There's no `.vscode/settings.json`. | It holds the settings in one place and keeps the layout single root. VS Code ignores the workspace file's settings when the folder is opened directly. The title bar shows `(Workspace)` when it's opened correctly. |
| D3 | **Put `.github/` at the root** with `copilot-instructions.md`, plus per-folder rules in `.github/instructions/*.instructions.md` using `applyTo`. | Copilot reads instructions from the open root. Per-folder files keep each set of rules short. |
| D4 | **`toolkit-kb/` is its own git repo**, for product knowledge, notes, backlog and decisions. It's named `toolkit-kb` (not `knowledge-base`) so it's never confused with Knowledge Hub, the firm's architecture knowledge base used in real runs. | History of decisions and backlog changes. **Local only, with no remote**: it isn't backed up off the VDI, by choice. |
| D5 | **`plugin-repo/` is a read-only reference clone** of the plugin from Bitbucket. No notes or outputs go inside it. **It is never pushed from here:** its push URL is disabled (§8). I can experiment on local branches. Real changes to the plugin are made in a separate development location outside this workspace (OQ-023). | It's where I read the real source. Since it can't be pushed, nothing from this workspace, including real-run content, can reach Bitbucket through it. |
| D6 | **`runs/` is split into `sandbox/` and `real/`**, and is never in git. | Test runs must not mix with real initiatives. Run outputs contain sensitive initiative content. |
| D7 | **The root folder is not a git repo.** | The two nested repos (D4, D5) show up separately in Source Control. A third repo around them only causes confusion. |
| D8 | **Terminal auto-approve is on for everything except Jira writes, Bitbucket, Working Hub approvals and deletes.** These always ask first: git remote operations (push, pull, fetch, clone), direct API calls that write to Jira (POST/PUT/PATCH/DELETE or a request body), any API call to Bitbucket, **any direct API call that submits a Working Hub approval (`POST …/approvals`)**, and any delete (files, folders, `git reset --hard`, `git clean`, deleting a branch or stash). **Jira reads run without asking**, as do Working Hub commits, reads and status checks, Knowledge Hub and everything else. **No rules for the Jira or Working Hub CLIs:** commands run through common-plugin's or neuro-plugin's CLIs run without asking, and the plugin's own "show the payload and wait for a yes" step and the hard rules are what guard them. | Working Hub's own controls (roles, path areas, separation of duties) cover commits, but separation of duties only stops someone approving their *own* commit. Where I'm the approver (e.g. GW-I2), an approval sent as me is a sign-off in my name, so it must never go through without my click. Jira and Bitbucket don't protect themselves the same way: an unwanted push or Jira write lands straight away. Jira reads change nothing, and asking for each one made scrapes tedious. Deletes can't be undone. |
| D9 | **`Original_Build_Guide.md` is the reference** for how the toolkit is built, until the plugin source has been read. Where the two disagree, the source wins, and the difference gets logged. | One reference point. Differences between the docs and the real build are themselves backlog input. |
| D10 | **`toolkit-kb/product/skill-notes/` holds documentation about each plugin skill** (one file per skill). These aren't agent skills, and no setting points at them. | The agent reads them as documentation. The name `skills/` would be confused with an agent-skills folder. |
| D11 | **Workspace tools are prompt files** in `.github/prompts/`, started explicitly with `/tk-<name>`. **Everything of mine uses the `tk-` prefix** (prompt files and skills), so typing `/tk` lists only my tools, and nothing is confused with neuro-plugin's or the PO plugin's commands. The only exceptions are the skills in D14. | Prompt files only run when called. Self-triggering skills would compete with the installed PO plugin's own skills for the same phrases. |
| D12 | **Never register `plugin-repo/`'s skill folders** in any agent, prompt or skills setting. | It would load the development copy of the plugin's skills next to the installed ones, and which one runs would be unpredictable. |
| D13 | **toolkit-kb is the agent's first stop.** The instructions and every prompt file tell the agent to check `toolkit-kb/` before answering about the product, and then confirm in `plugin-repo/`. | The agent builds on what's already known and recorded, instead of re-deriving it or contradicting earlier decisions. |
| D14 | **Four agent skills in `.github/skills/`: `tk-pdf-scrape-standard`, `tk-pdf-scrape-vision`, `tk-confluence-scrape` and `tk-jira-scrape`.** All are read-only extraction to markdown. There are two PDF skills: `tk-pdf-scrape-standard` is the deterministic default, and `tk-pdf-scrape-vision` reads page images for complex PDFs and is only used when I ask for it or accept it as a fallback. I provide the files (§5B). Everything else stays a prompt file. `tk-jira-scrape` exports issues by key, JQL or filter, and never creates, edits, transitions, comments, scores or analyses. | Extraction is better done by a script than by the model, and a skill can bundle one. Their trigger words ("extract this PDF", "extract this PDF with vision", "scrape this Confluence page", "export these Jira tickets") don't clash with the PO plugin's phrases. `tk-confluence-scrape` is explicitly *not* for publishing, so it doesn't compete with the plugin's Stage 6 "publish to Confluence". `tk-jira-scrape`'s description excludes the PO plugin's Jira work (epic quality, PBR, PI planning, publication). It feeds production tickets into the fix backlog (D15) and Jira issues into a run's sources. Its read calls run without asking (D8). |
| D15 | **Two backlogs:** `product_backlog.md` (`PO-NNN`: improvements, new capabilities, doc gaps, tech debt, ops) and `fix_backlog.md` (`FIX-NNN`: defects and production issues, each linked to its Jira key where there is one). `done.md` is shared. Jira stays the system of record for production tickets. Raw scrapes go into `backlog/jira-intake/`, which is **git-ignored**, and `fix_backlog.md` holds my triage in general terms. | Fixes and improvements are prioritised differently (severity vs value) and move at a different pace. Production tickets can contain real initiative details, which must not land in git. |
| D16 | **This workspace is for GitHub Copilot agent mode only.** The toolkit also runs in Claude Code, but nothing here is set up for it. | One agent, one set of instruction, prompt and skill files to maintain. |

---

## 2. Folder scaffolding

```
neuro_workspace/                          ← open via the .code-workspace file
├── neuro_workspace.code-workspace
├── README.md                                ← short map of the workspace (for humans)
├── .github/
│   ├── copilot-instructions.md              ← workspace-wide agent rules
│   ├── instructions/
│   │   ├── toolkit-kb.instructions.md       ← applyTo: toolkit-kb/**
│   │   ├── plugin-repo.instructions.md      ← applyTo: plugin-repo/**
│   │   └── runs.instructions.md             ← applyTo: runs/**
│   ├── prompts/                             ← my workspace tools, started with /tk-<name>
│   │   ├── tk-backlog-add.prompt.md         ← /tk-backlog-add
│   │   ├── tk-decide.prompt.md              ← /tk-decide
│   │   ├── tk-skill-note.prompt.md       ← /tk-skill-note
│   │   ├── tk-fix-triage.prompt.md          ← /tk-fix-triage
│   │   └── tk-note.prompt.md                ← /tk-note
│   └── skills/                              ← ONLY these four (D14); load automatically when relevant
│       ├── tk-pdf-scrape-standard/          ← SKILL.md + scripts: provided by me (placeholder)
│       ├── tk-pdf-scrape-vision/            ← SKILL.md + scripts: provided by me (placeholder)
│       ├── tk-confluence-scrape/            ← SKILL.md + scripts: provided by me (placeholder)
│       └── tk-jira-scrape/                  ← SKILL.md + scripts: provided by me (placeholder)
│
├── toolkit-kb/                              ← git repo (mine): toolkit notes. NOT Knowledge Hub
│   ├── README.md
│   ├── .gitignore
│   ├── reference/
│   │   ├── original-build-guide.md          ← copy of Original_Build_Guide.md (placeholder until §11 task 0)
│   │   └── confluence/                      ← Confluence pages about the toolkit, saved by tk-confluence-scrape
│   ├── product/
│   │   ├── how-it-works.md                  ← ONE-PAGE overview only: a line or two per stage, linking to stages/
│   │   ├── stages/                          ← the DETAIL, one file per stage (7 files, incl. 4.5):
│   │   │   ├── _template.md                 ← format for a stage file
│   │   │   ├── stage-1-intake.md
│   │   │   ├── stage-2-strategy.md
│   │   │   ├── stage-3-initiation.md
│   │   │   ├── stage-4-refine-design.md
│   │   │   ├── stage-4.5-construct.md
│   │   │   ├── stage-5-pi-planning.md
│   │   │   └── stage-6-communication.md
│   │   ├── skill-notes/                     ← documentation about each plugin skill (NOT agent skills)
│   │   │   └── _template.md                 ← format for a skill note
│   │   └── glossary.md                      ← from the build guide §6 (placeholder until §11 task 0)
│   ├── backlog/
│   │   ├── product_backlog.md               ← PO-NNN: improvements, new capabilities, doc gaps (D15)
│   │   ├── fix_backlog.md                   ← FIX-NNN: defects and production issues, linked to Jira (D15)
│   │   ├── done.md                          ← closed PO and FIX items, moved here when shipped or dropped
│   │   ├── jira-sources.md                  ← where the toolkit's tickets live, and the deliverables/epics to scan
│   │   └── jira-intake/                     ← raw Jira scrapes, by date. GIT-IGNORED
│   ├── decisions/
│   │   └── decision-log.md                  ← PRODUCT decisions only (DEC-NNN). Workspace decisions stay in §1 (D-NNN)
│   ├── open_questions.md                    ← open questions (OQ-NNN), grouped by area (placeholder until §11 task 0)
│   ├── notes/                               ← general notes: YYYY-MM-DD-topic.md (saved by /tk-note)
│   │   └── meetings/                        ← meeting notes: YYYY-MM-DD-topic.md (saved by /tk-note)
│   └── workspace/
│       └── workspace_setup.md               ← this file, moved here after setup
│
├── plugin-repo/                             ← read-only reference clone from Bitbucket; push disabled (D5)
│
└── runs/                                    ← NOT in git
    ├── sandbox/                             ← LOCAL_PROJECT_ROOT for test runs
    │   ├── sources/
    │   ├── Intake/
    │   ├── Strategy/
    │   ├── WorkingHub/
    │   ├── PIPlanning/
    │   └── Communications/
    └── real/                                ← one subfolder per real initiative (until OQ-024 is answered)
        └── <initiative>/                    ← LOCAL_PROJECT_ROOT while working on that initiative
            ├── sources/
            ├── Intake/
            ├── Strategy/
            ├── WorkingHub/
            ├── PIPlanning/
            └── Communications/
```

**About `runs/`.** The subfolders inside `sandbox/` and `real/` follow the guide (Getting Started, Step 3). The guide also writes to `project-planning\`, `Research\` and `Outputs\Session_Records\`, which aren't in that structure. Let the plugin create those, and note where files actually land (in the stage file under `toolkit-kb/product/stages/`, or as a doc-gap item).

**About `LOCAL_PROJECT_ROOT`.** SETUP.md holds one value. Switching between sandbox and real means changing it, so the current value must always be visible (see the rule in §4).

**One folder per real initiative.** The guide doesn't say whether the toolkit keeps each initiative's `sources/` and
`SOURCES.md` apart (OQ-024). If it doesn't, two initiatives under one `LOCAL_PROJECT_ROOT` would share one sources
catalogue, and documents from one could be used to pre-fill the other. To be safe, each real initiative gets its own
folder, `runs/real/<initiative>/`, and `LOCAL_PROJECT_ROOT` is pointed at that folder while working on it. Switching
initiatives means changing `LOCAL_PROJECT_ROOT`. Sandbox stays as one flat folder. Revisit once OQ-024 is answered.

---

## 3. Workspace file

`neuro_workspace/neuro_workspace.code-workspace`

```jsonc
{
  "folders": [
    { "path": "." }
  ],
  "settings": {
    // --- Git: detect the two nested repos (toolkit-kb, plugin-repo) ---
    "git.autoRepositoryDetection": true,
    "git.repositoryScanMaxDepth": 2,
    "git.openRepositoryInParentFolders": "never",

    // --- Search: keep run outputs out of search so the agent doesn't
    //     treat old drafts as context. Remove if runs should be searchable. ---
    "search.exclude": {
      "runs/**": true
    },

    // --- Copilot instructions ---
    "github.copilot.chat.codeGeneration.useInstructionFiles": true,
    "chat.instructionsFilesLocations": {
      ".github/instructions": true
    },

    // --- Prompt files: my workspace tools (/tk-backlog-add, /tk-decide, ...) ---
    // Only .github/prompts. Never add plugin-repo/ paths here or to any
    // skills setting (D12).
    "chat.promptFiles": true,
    "chat.promptFilesLocations": {
      ".github/prompts": true
    },

    // --- Agent skills: only tk-pdf-scrape-standard, tk-pdf-scrape-vision, tk-confluence-scrape and tk-jira-scrape (D14) ---
    // Only .github/skills. Never add plugin-repo/ paths (D12).
    "chat.useAgentSkills": true,
    "chat.agentSkillsLocations": {
      ".github/skills": true
    },

    // --- Terminal auto-approve (D8): everything runs without asking,
    //     EXCEPT Jira writes, Bitbucket, Working Hub approvals and deletes. `false` = always ask; it overrides the
    //     catch-all `true`. Each part of a chained command is checked. ---
    "chat.tools.terminal.autoApprove": {
      // Everything else: auto-approved
      "/.*/": true,

      // Bitbucket: any git operation that talks to the remote
      "/^git\\s+(push|pull|fetch|clone)\\b/": false,

      // Jira writes via direct API calls: a write method or a request body. GET calls run without asking.
      "/^(?=.*\\b(curl|wget|Invoke-RestMethod|Invoke-WebRequest|irm|iwr)\\b)(?=.*jira)(?=.*(-X\\s*(POST|PUT|PATCH|DELETE)|-Method\\s+(Post|Put|Patch|Delete)|--data|--json|\\s-d\\s|-Body)).*/i": false,

      // Bitbucket: any direct API call, read or write
      "/\\b(curl|wget|Invoke-RestMethod|Invoke-WebRequest|irm|iwr)\\b.*bitbucket/i": false,

      // Working Hub approvals: a sign-off in my name (D8). Commits, reads and status checks run without asking.
      // Direct API calls only: a write method or request body to an .../approvals endpoint:
      "/^(?=.*\\b(curl|wget|Invoke-RestMethod|Invoke-WebRequest|irm|iwr)\\b)(?=.*\\/approvals\\b)(?=.*(-X\\s*POST|-Method\\s+Post|--data|--json|\\s-d\\s|-Body)).*/i": false,

      // Deletes: anything that removes files/folders or throws away git changes
      "/^(Remove-Item|rm|del|erase|rmdir|rd|ri)\\b/i": false,
      "/^git\\s+(reset\\s+--hard|clean|rm|branch\\s+-D|stash\\s+(drop|clear))\\b/": false,

      // Re-enabling push on plugin-repo (D5)
      "/^git\\s+remote\\s+set-url\\b.*--push/": false
    },

    // --- Terminal: the plugin docs assume PowerShell ---
    "terminal.integrated.defaultProfile.windows": "PowerShell",

    // --- Markdown-heavy workspace ---
    "files.trimTrailingWhitespace": true,
    "files.insertFinalNewline": true,
    "[markdown]": {
      "editor.wordWrap": "on"
    }
  }
}
```

---

## 4. `.github/copilot-instructions.md`

````markdown
# Workspace instructions: neuro_workspace

I am the product owner of **product-owner-plugin** (the PO toolkit), a VS Code / Claude Code skill package
that runs the JPMC PO workflow (6 stages, Working Hub gates GW-I1 → GW-I2 → GW-RD1 → GW-RD2 → GW-B1).
This workspace is where I **manage the product**: understand it, keep its backlog, read its source, and test it.
I also run it for real initiatives here, in `runs/real/`, but only in run mode.

## Folder map

| Folder | What it is | Default stance |
|---|---|---|
| `toolkit-kb/` | My git repo: product knowledge, backlog, decisions, notes | Read and write freely, following its rules |
| `toolkit-kb/reference/original-build-guide.md` | Transcription of the plugin's Confluence docs | The reference until the source has been read |
| `plugin-repo/` | Read-only reference clone of the plugin source. Never pushed (D5) | Read freely. Experiment only when I ask, on a local branch |
| `runs/sandbox/` | LOCAL_PROJECT_ROOT for test runs of the installed plugin | Use for testing |
| `runs/real/<initiative>/` | One folder per real initiative. LOCAL_PROJECT_ROOT points at the one I'm working on | Sensitive. Read only when I point you at it |

**toolkit-kb is not Knowledge Hub.** `toolkit-kb/` is my local notes about the toolkit as a product. Knowledge Hub is
the firm's remote architecture knowledge base, which the plugin queries in real runs (Stage 3 ACD). If I say
"knowledge base" and it's unclear which I mean, ask.

## Two modes. Know which one you are in.

1. **Product-management mode (the default).** I'm asking about the toolkit itself: how it works, what to
   change, the backlog, the source. In this mode:
   - Do **not** start running PO plugin skills (intake, ideation, project-initiation, epic-quality, …), even
     if my words match their trigger phrases ("phase gate", "check epic quality", "po plugin").
     Explain or analyse the skill instead.
   - Do **not** call Working Hub, Jira or Confluence write APIs.
2. **Run mode.** Only when I say so explicitly. Then the installed plugin's rules apply, and the `runs/` instructions
   apply.

**Switching modes:**
- **Into run mode:** I say `run mode: sandbox`, or `run mode: real <initiative>`. Reply with one line confirming the
  mode, the initiative (for real), and the LOCAL_PROJECT_ROOT that SETUP.md points at. If it doesn't match, stop and
  tell me before doing anything else.
- **Back to product-management mode:** I say `exit run mode` (or `product mode`). Confirm in one line.
- **A new chat always starts in product-management mode.** Prefer one chat per run, and a fresh chat for product work
  afterwards, so real-run content doesn't carry over into product work.
- While in run mode, start each reply with `[run: sandbox]` or `[run: real <initiative>]` so I can always see it.

If you're unsure which mode I mean, ask.

## Where to look first

Before answering anything about the toolkit, check toolkit-kb in this order. Then confirm in the source.

1. `toolkit-kb/product/skill-notes/<skill>.md`: what we already know about a specific skill
2. `toolkit-kb/product/stages/` and `how-it-works.md`: how the stages connect
3. `toolkit-kb/decisions/decision-log.md`: don't contradict a decision. If one looks wrong, say so.
4. `toolkit-kb/backlog/fix_backlog.md` and `product_backlog.md`: is this already a known defect or idea?
   Reference its FIX-NNN or PO-NNN.
5. `toolkit-kb/open_questions.md`: is this already an open question? Reference its OQ-NNN, and fill in the
   Answer when you find one.
6. `toolkit-kb/reference/original-build-guide.md`: the documented design
7. `plugin-repo/`: the actual source, which wins over everything above

If toolkit-kb is missing something or out of date, say so and offer to update it
(e.g. with `/tk-skill-note`). Don't silently work around it.

## My workspace tools (prompt files)

| Command | Use |
|---|---|
| `/tk-backlog-add` | Add an item: defects go to the fix backlog (FIX-NNN), everything else to the product backlog (PO-NNN) |
| `/tk-fix-triage` | Triage Jira tickets into the backlogs: scan a deliverable or epic's open items, or give specific keys |
| `/tk-decide` | Log a DEC-NNN decision |
| `/tk-skill-note` | Write or refresh the note for one plugin skill, from the source |
| `/tk-note` | Save a general note or meeting note, tidied up, as a dated file in `notes/` or `notes/meetings/` |

When something I say fits one of these, suggest the command. Don't do the work silently in a different format.

## Spotting decisions

Watch for two things in our chats and notes, and say so in one line. Don't log anything without me.
- **A decision was made** ("let's go with…", "we agreed…", "drop that"): suggest "That sounds like a decision. Log it
  with `/tk-decide`?"
- **A decision is needed but hasn't been made** (two options on the table, an open question that can only be closed by
  choosing, a backlog item blocked on a choice): say "This needs a decision: <the choice>." Give the options and your
  recommendation, and offer to log it as `proposed` with `/tk-decide`.

Use this test. It's worth logging if the answer to "why is it like this?" would otherwise only exist in a chat, a
meeting or my head, **and** at least one of these is true:
- it's hard or costly to reverse
- it affects other people (POs, architects, approvers, the Working Hub team)
- it changes a rule, threshold or standard
- it picks between real alternatives, or says no to something
- it reverses or changes an earlier decision
- it settles a disagreement, or closes an open question by choosing an option
- it accepts a known risk

Don't suggest one for things that are easy to undo and only affect me, facts (those are open-question answers), work
to do (backlog items), or anything an existing decision already covers. Workspace-setup choices go in
`workspace_setup.md` §1, not the decision log.

## My workspace skills (load automatically)

| Skill | Use |
|---|---|
| `tk-pdf-scrape-standard` | **Default for PDFs.** Deterministic extraction of text and tables into markdown |
| `tk-pdf-scrape-vision` | Vision-mode extraction for complex PDFs (scans, diagrams, complex layouts). Only when I ask, or when I accept it after `tk-pdf-scrape-standard` reports it couldn't extract well |
| `tk-confluence-scrape` | Read a Confluence page (read-only) and save it as markdown |
| `tk-jira-scrape` | Export Jira issues (read-only) to markdown, one file per issue |

- These are the only workspace skills. They extract. They don't summarise, interpret or publish.
- For a PDF, always start with `tk-pdf-scrape-standard`. Use `tk-pdf-scrape-vision` only when I ask for it, or offer it
  when the standard scrape reports it couldn't extract well, and wait for my yes.
- `tk-confluence-scrape` never creates, updates or publishes Confluence pages. Publishing is the PO plugin's Stage 6,
  and only happens in run mode.
- `tk-jira-scrape` never creates, edits, transitions or comments on Jira issues, and doesn't score them. Epic quality,
  PBR and PI analysis are PO plugin skills (run mode).
- Where the output goes:
  - Material about the toolkit itself goes to `toolkit-kb/reference/`.
  - Production tickets about the toolkit go to `toolkit-kb/backlog/jira-intake/<date>/` (git-ignored).
  - Material for a run goes to `runs/sandbox/sources/_extracted/`, or `runs/real/<initiative>/sources/_extracted/`.
  - If it's unclear, ask.
- Content from `runs/real/` never goes into `toolkit-kb/`.

## Hard rules (always)

- Never approve a Working Hub gate or submit an approval on anyone's behalf.
- Never commit to Working Hub, create or update Jira issues, or publish to Confluence without showing me the
  exact payload and getting an explicit "yes" for that call.
- Never push from `plugin-repo/`: it's a reference clone with pushing disabled (D5). Never commit to `main`/`master`
  there. Experiments go on a local branch.
- Never copy content from `runs/real/` into `toolkit-kb/` or `plugin-repo/`. Summarise in general terms
  if needed, with no initiative names, figures, SIDs or architecture details.
- Before any run, state which LOCAL_PROJECT_ROOT the installed plugin's SETUP.md points at. If it isn't
  the folder I asked for, stop and tell me.
- **Jira writes depend on the mode.** In product-management mode, never create, edit, transition or comment on Jira
  issues: draft the text for me to post myself. In run mode, the PO plugin may write to Jira as part of its process,
  after showing me the exact payload and getting my explicit yes for each call.
- Never delete a file, or replace a file's whole contents, using edit tools. Use the terminal for deletes, so it
  asks me first (D8). This matters most for `.github/` and `runs/`, which have no git history.
- Never add `plugin-repo/` paths to any prompt-file, instructions or skills setting. The plugin's skills
  under `plugin-repo/` are source to read, not tools to load.

## Where things go

- A defect or production issue → `toolkit-kb/backlog/fix_backlog.md` (FIX-NNN).
- An improvement, new capability, doc gap, tech debt or ops item → `toolkit-kb/backlog/product_backlog.md` (PO-NNN).
- Formats for both are in the toolkit-kb instructions file. Jira ticket details stay in Jira and `jira-intake/`.
  Backlog items describe them in general terms (no initiative names, figures, SIDs or architecture details).
- A general note or meeting note → `/tk-note`: `toolkit-kb/notes/` or `toolkit-kb/notes/meetings/`.
- Something we don't know yet → `toolkit-kb/open_questions.md`: next free OQ-NNN, under its area, plus an index
  row. When it's answered, fill in Answer with evidence, set ✅, and raise a backlog item if it shows a problem.
- Something learned about how the toolkit works → `toolkit-kb/product/`. Detail about a stage goes in
  `stages/stage-<n>-*.md`. Detail about one skill goes in `skill-notes/`. `how-it-works.md` stays a one-page
  overview: update its line for that stage only if the summary changes. Never write the same detail in two places.
- A decision about the toolkit as a product → `decision-log.md` (DEC-NNN). A decision about how this workspace is set
  up → `toolkit-kb/workspace/workspace_setup.md` §1 (D-NNN). Never record the same decision in both.
- A problem found in a run → a backlog item via `/tk-backlog-add` (FIX if broken, PO if friction), in general terms for real runs.
- Where the docs and the real source disagree → backlog item with type `doc-gap`, citing both.

## How to answer me

- I'm learning this product. Explain in small parts and check in before going further.
- When explaining how something works, cite where it comes from: `plugin-repo/<path>` or the build guide
  section. Say clearly when something is inferred rather than found.
- Be candid. If an idea of mine is weak, say so and say why.
````

---

## 5. Per-folder instruction files

### 5.1 `.github/instructions/toolkit-kb.instructions.md`

````markdown
---
applyTo: "toolkit-kb/**"
---

# toolkit-kb rules

- This is a git repo. After meaningful changes, offer to commit with a short message. It has no remote (D4): don't
  add one, and don't push.
- Plain markdown. One topic per file. Dates as YYYY-MM-DD.
- Use the reference copy of the build guide and the plugin source as evidence. Cite the file or section.

## Two backlogs (D15)

| File | IDs | Holds |
|---|---|---|
| `backlog/product_backlog.md` | `PO-NNN` | Improvements, new capabilities, doc gaps, tech debt, ops |
| `backlog/fix_backlog.md` | `FIX-NNN` | Defects and production issues: from Jira tickets, sandbox runs or reading the source |
| `backlog/done.md` | both | Closed items from either backlog (shipped, released, dropped, won't-fix, duplicate) |

Routing: if something is **broken** (it doesn't do what it's documented or designed to do), it's a FIX. If it works
as designed but should work **better or differently**, it's a PO. If unsure, ask. A Jira ticket that's really a
feature request becomes a PO item that cites the Jira key.

IDs are sequential per prefix and never reused (check both the backlog and `done.md`).

## backlog/product_backlog.md format

Top of file: a summary table, highest priority first.

| ID | Title | Type | Area | Priority | Status |
|---|---|---|---|---|---|

- **Type:** `improvement` · `new-capability` · `doc-gap` · `tech-debt` · `ops` (release, support, access)
- **Area:** a stage (`stage-1` … `stage-6`, `stage-4.5`), or `platform` (setup, install, SETUP.md), `scoring`, `working-hub`, `jira`, `docs`
- **Priority:** P1 (high value / unblocks many POs) · P2 (significant improvement) · P3 (nice to have)
- **Status:** `new` · `confirm` (needs checking in source/VDI) · `ready` · `in-progress` · `done` · `dropped`

Below the table, one section per item:

```
### PO-NNN. <title>
- Added: YYYY-MM-DD · Type · Area · Priority · Status
- Jira: <keys, if raised from a ticket> or none
- Problem: what's wrong, for whom, evidence (cite file/section/sandbox test/OQ-NNN)
- Proposed change: what to do
- How to confirm / test: steps, sandbox only
- Acceptance: how we know it's done
- Open questions:
```

## backlog/fix_backlog.md format

Top of file: a summary table, highest severity first.

| ID | Title | Severity | Area | Jira | Status |
|---|---|---|---|---|---|

- **Severity:** S1 (POs blocked, or wrong governance output committed / gate affected) · S2 (broken, but a workaround
  exists) · S3 (minor or cosmetic)
- **Area:** same values as the product backlog
- **Jira:** key(s), or `none` if found in a sandbox run or in the source
- **Status:** `new` · `triaged` · `confirm` (can't reproduce yet) · `in-progress` · `fixed` (on a branch) ·
  `released` (in a published plugin version) · `closed` · `won't-fix` · `duplicate` (of FIX-NNN)

Below the table, one section per item:

```
### FIX-NNN. <title>
- Added: YYYY-MM-DD · Severity · Area · Status
- Jira: <KEY> (<url>) · reported by N ticket(s) · last checked YYYY-MM-DD
- Symptom: what goes wrong, in general terms (no initiative names, figures, SIDs, architecture details)
- Affected: stage/skill · plugin version(s) · how many POs/tickets
- Workaround: what POs can do meanwhile, or none
- Root cause: once known, cite plugin-repo path; "(inferred)" if not confirmed
- Fix: where it was fixed (a link or reference to the change in the development location, OQ-023) · released in version
- Verified: sandbox test (what was run, and the result)
```

When an item is closed, released, dropped, won't-fix or a duplicate, move its section to `backlog/done.md`, keeping
its ID, and update the table.

## backlog/done.md format

Top of file: a summary table, most recently closed first. Below it, the moved item sections, unchanged.

| ID | Title | Closed | Outcome | Notes |
|---|---|---|---|---|

- **Outcome:** `released` (with version) · `done` · `dropped` · `won't-fix` · `duplicate` (of FIX-NNN/PO-NNN)
- **Notes:** one line, e.g. why it was dropped, or the DEC-NNN that decided it.

## backlog/jira-sources.md format

Where the toolkit's production tickets live, and the parents that `/tk-fix-triage` scans. Fill this in once known
(OQ-022). Keys mode doesn't need this file.

```
- Jira project(s):
- Who raises them / support route:
- How items hang off a deliverable:   (child epics → issues? issue links? which link type?)
- Epic-child query for this Jira:     ("Epic Link" = <KEY> on Server/DC, or parent = <KEY>)

## Parents to scan
| Key | Type (deliverable/epic) | What it covers | Last scanned |
|---|---|---|---|
```

## decisions/decision-log.md format

`DEC-NNN · YYYY-MM-DD · status · decision · why · what it affects`. Newest first. Never delete.
- **Status:** `proposed` (needs deciding: list the options and a recommendation) · `decided` · `superseded by DEC-NNN`.
- Link any OQ-NNN it closes, and the FIX/PO items it affects.

## product/stages/stage-<n>-<name>.md format

One file per toolkit stage (7, including 4.5). Each covers the stage **end to end, across its skills**. It links to
skill notes for a skill's internals, and doesn't repeat them. Follow `stages/_template.md`:

```
# Stage <n>: <name>
- Router letter: · Last checked against source: YYYY-MM-DD @ <plugin-repo commit short sha>
- Sources: build guide §<x>, toolkit-kb/reference/confluence/<page>.md, plugin-repo/<paths>

## Purpose                     (what the stage turns into what)
## How you get in              (router letter, trigger phrases, what must exist first)
## Skills used, in order       (each links to its skill note)
## Steps                       (in order, including where the agent stops for me)
## Inputs                      (sources/, session file, outputs of earlier stages)
## Outputs and where they land (file names; the guide's path AND the actual path once confirmed)
## Gates and checkpoints       (Working Hub gates, who approves, local decision points)
## What can block you          (hard blockers, thresholds, required evidence)
## Working Hub / Jira / Confluence calls (which calls, in what order)
## Guide vs source             (where they disagree; link doc-gap backlog IDs)
## Known issues                (link FIX-NNN and PO-NNN items)
## Open questions              (link OQ-NNN items)
```

Every claim cites a build-guide section, a Confluence page in `reference/confluence/` or a `plugin-repo/` path. Mark
anything inferred *(inferred)*. Leave a heading empty rather than guess.

## product/skill-notes/<skill-name>.md format

File name = the skill's name in the plugin (e.g. `epic-quality.md`). Follow `skill-notes/_template.md`:

```
# <skill-name>
- Stage(s): · Last checked against source: YYYY-MM-DD @ <plugin-repo commit short sha>
- Source files: plugin-repo/<path>/SKILL.md, <other files> (list every file)

## What it does
## When it triggers            (trigger phrases / which stage router option)
## Inputs                      (files, sources/, session fields, Jira/WH data it reads)
## Outputs                     (files it writes, where; API calls it makes)
## Rules it enforces           (blockers, thresholds, scoring; say whether in prompt text or a script)
## Human checkpoints           (where it stops for my review/approval)
## Differs from the build guide (cite guide section; link doc-gap backlog IDs)
## Known issues                (link FIX-NNN and PO-NNN items)
## Open questions
```

Every claim cites a `plugin-repo/` path or a build-guide section. If something is inferred, mark it *(inferred)*.
When the skill's source changes, refresh the note and update "Last checked".
````

### 5.2 `.github/instructions/plugin-repo.instructions.md`

````markdown
---
applyTo: "plugin-repo/**"
---

# plugin-repo rules

- This is the real plugin source, cloned from Bitbucket, kept as a **read-only reference** (D5). Pushing is disabled.
  Real changes to the plugin are made in a separate development location, not here.
- Don't add notes, scratch files or run outputs here. They belong in `toolkit-kb/` or `runs/`.
- Only change files when I ask, as an experiment. Before changing anything: `git status` and
  `git branch --show-current`. If on `main`/`master`, create a local branch `po/<backlog-id>-<short-slug>` first
  (e.g. `po/PO-007-intake-type-letters`), one backlog item per branch, and reference the backlog ID in commit messages.
- Never push, never re-enable the push URL, and never open a PR.
- When explaining a skill, read its actual files (SKILL.md, templates, scripts) and cite paths. Note anything that
  contradicts `toolkit-kb/reference/original-build-guide.md` and offer to log it as a `doc-gap`.
- Do not *execute* skills from here. Reading them is fine. Running them is run mode in `runs/`.
- If this repo has its own `.github/copilot-instructions.md` or AGENTS.md, read it when working here and follow
  it unless it conflicts with the workspace hard rules.
````

### 5.3 `.github/instructions/runs.instructions.md`

````markdown
---
applyTo: "runs/**"
---

# runs rules

- `runs/` is not in git. Never add it to any repo.
- `runs/sandbox/` is for testing the plugin. Use test initiatives / test Jira projects only. If no sandbox Working Hub
  or Jira project is configured, stop before any write call and tell me.
- `runs/real/` holds real initiative work and is sensitive. What you may read depends on the mode:
  - **Product-management mode:** don't read `runs/real/` unless I point you at a specific file.
  - **Run mode (real):** read and write freely inside **the current initiative's folder only**: the one
    LOCAL_PROJECT_ROOT points at. Never open another initiative's folder in the same run.
  - **Either mode:** never copy anything from `runs/real/` into another folder.
- Before any run: confirm mode (sandbox or real), the LOCAL_PROJECT_ROOT in the installed plugin's SETUP.md, and
  the installed plugin version.
- Real runs: each initiative has its own folder, `runs/real/<initiative>/` (OQ-024). Before a real run, check that
  LOCAL_PROJECT_ROOT points at **that initiative's** folder, not `runs/real/` itself or another initiative. If it's a
  new initiative, offer to create its folder with the six subfolders from §2 first.
- Every write call (Working Hub commit, role assignment, Jira create/update, Confluence publish): show the payload,
  wait for my explicit yes. Approvals are never submitted by you.
- After a run, offer backlog items (via `/tk-backlog-add`) for anything that went wrong. Real runs: general terms only.
````

---

## 5A. Prompt files (`.github/prompts/`)

These are my workspace tools. Each one reads toolkit-kb first (D13). They're only used when I type
the command. Check the frontmatter keys on the VDI: newer VS Code versions use `agent:` instead of `mode:`.

### 5A.1 `tk-backlog-add.prompt.md`

````markdown
---
description: Add an item to the PO toolkit fix backlog (defects) or product backlog (everything else)
mode: agent
---

Add a backlog item for the product-owner-plugin.

My input: ${input:item:Describe the problem or idea}

0. Decide which backlog, using the routing rule in `.github/instructions/toolkit-kb.instructions.md`:
   broken → `fix_backlog.md` (FIX-NNN); works but should be better → `product_backlog.md` (PO-NNN). Tell me which
   and why. If unsure, ask.
1. Read that backlog, the other backlog, and `toolkit-kb/backlog/done.md`. If this is already covered,
   show me the existing FIX-NNN or PO-NNN and ask whether to update it instead.
2. Read the relevant `toolkit-kb/product/skill-notes/` and `stages/` files, plus
   `toolkit-kb/decisions/decision-log.md`, so the item uses what we already know and doesn't contradict a decision.
3. Ask me (one question at a time) for anything missing. For a PO item: problem, evidence, type, area, priority.
   For a FIX item: symptom, Jira key (if any), severity, area, affected version, workaround.
   Suggest values; don't invent evidence. If evidence is only inferred, set Status to `confirm`.
4. Assign the next ID for that prefix (highest in the backlog and done.md + 1).
5. Write the item in the format in `.github/instructions/toolkit-kb.instructions.md`, add it to the summary
   table in priority order, and link it from any related skill note's "Known issues".
6. Show me the diff. Offer to commit in `toolkit-kb/` with message `backlog: add <ID> <title>`.
````

### 5A.2 `tk-decide.prompt.md`

````markdown
---
description: Record a product decision in the decision log
mode: agent
---

Record a decision for the product-owner-plugin.

Decision: ${input:decision:What did we decide, or what needs deciding?}

0. **Check it's worth logging**, using the test under "Spotting decisions" in `.github/copilot-instructions.md`.
   If it isn't (easy to undo, a fact, a piece of work, or already covered), say so and suggest where it belongs
   instead (an open-question answer, a backlog item, or the existing DEC-NNN). Log it anyway if I insist.
1. Read `toolkit-kb/decisions/decision-log.md`. If this reverses or overlaps an earlier decision, show it
   and ask whether the new one supersedes it.
2. **Decided or proposed?**
   - Decided: ask me for the "why" and "what it affects" if I didn't say.
   - Not yet decided: list the options, the trade-offs and your recommendation, and log it as `proposed`. When I
     later decide, update the same entry to `decided` with the chosen option. Don't create a new ID.
3. Add the entry at the top in the format in `.github/instructions/toolkit-kb.instructions.md` (next ID, today's
   date). If it supersedes one, mark the old entry `superseded by DEC-NNN`. Never delete.
   If it closes an open question, fill in that OQ's Answer and link the DEC-NNN.
4. If it affects backlog items, list them and offer to update their status.
5. Show the diff and offer to commit: `decision: DEC-NNN <short title>`.
````

### 5A.3 `tk-skill-note.prompt.md`

````markdown
---
description: Write or refresh the toolkit-kb note for one plugin skill, from its source
mode: agent
---

Write or refresh the skill note for: ${input:skill:Skill name, e.g. epic-quality}

Product-management mode. Read only. Do not run the skill.

1. Read the existing `toolkit-kb/product/skill-notes/<skill>.md` if there is one, and `_template.md`.
2. Find the skill in `plugin-repo/`. List every file that belongs to it (SKILL.md, templates, scripts, references)
   and read them all. Record the current `plugin-repo` commit (`git -C plugin-repo rev-parse --short HEAD`).
3. Read what `toolkit-kb/reference/original-build-guide.md` says about this skill (stage sections, §13 inventory,
   any scoring or error tables).
4. Fill in or update every template section. Cite a `plugin-repo/` path or a guide section for each claim.
   Mark anything inferred as *(inferred)*. Say whether each rule is enforced by a script or only by prompt text.
5. List differences between the source and the guide under "Differs from the build guide", and offer to log each
   one with /tk-backlog-add (a `doc-gap` PO item if the docs are wrong, a FIX item if the source is wrong).
6. Show the note (or the diff, if refreshing) and offer to commit: `skill-note: <skill> @ <sha>`.
````

### 5A.4 `tk-fix-triage.prompt.md`

Two ways to use it:
- **Scan a parent:** give a deliverable or epic key. It finds every open item under it and triages them all.
- **Specific tickets:** give one or more Jira keys. It triages just those.

Both modes end in the same triage table and the same approval step.

````markdown
---
description: Triage PO toolkit production tickets from Jira (read-only) into the fix or product backlog, by parent deliverable/epic or by specific keys
mode: agent
---

Triage product-owner-plugin production tickets into the backlogs.

Input: ${input:input:A deliverable or epic key to scan (e.g. "scan ABC-100"), or a list of Jira keys (e.g. "ABC-123, ABC-145")}

Product-management mode. Read-only towards Jira: never create, edit, transition or comment.

1. **Work out the mode.**
   - "scan <KEY>", or one key that turns out to be a deliverable or epic → **scan mode**.
   - One or more keys that are ordinary issues → **keys mode**.
   - If it isn't clear, ask me. Don't guess.
2. **Export from Jira** with the `tk-jira-scrape` skill into `toolkit-kb/backlog/jira-intake/<YYYY-MM-DD>/`
   (git-ignored). Read calls run without asking (D8). Tell me how many calls you expect before starting.
   - Scan mode: read the parent first, then its open children (statusCategory != Done). For an epic, use the epic's
     children. For a deliverable, find how its items hang off it (child epics, then their issues, or issue links) as
     recorded in `jira-sources.md`. If that isn't recorded yet, show me what you found and ask (OQ-022). Tell me the
     total before triaging. If it's over 50, ask whether to continue.
   - Keys mode: export exactly the keys I gave. Report any that don't exist or that I can't access, and carry on with
     the rest.
3. **Check what's already there.** Read `fix_backlog.md`, `product_backlog.md` and `done.md`. A ticket whose key is
   already on an item is **already tracked**. Don't create it again. Just check its status (step 7).
4. **Propose one of these for each ticket:**
   - **link** it to an existing FIX-NNN or PO-NNN (same symptom: say why you think it's the same)
   - **new FIX** (it's broken): suggest the severity and area
   - **new PO** (it's really a feature request or improvement), citing the Jira key
   - **support only** (how-to question or user error). No backlog item, but flag it if the same question keeps
     coming up, because that points to a doc-gap or onboarding PO item.
   - **already tracked** (from step 3)
5. **Show me a triage table and wait** for my decisions before writing anything:
   | Jira | Summary (general terms) | Proposal | Severity | Reason |
   I can approve everything ("go"), or change individual rows.
6. **Write** the approved items in the formats in `.github/instructions/toolkit-kb.instructions.md`. Put the Jira
   key on every item. Use general terms only: no initiative names, figures, SIDs or architecture details from the tickets.
7. **Status check:** list any mismatches between Jira and the backlogs, e.g. a ticket closed while its FIX is still open,
   or a FIX released while the ticket is still open. For each one, draft a short Jira comment for me to post myself.
8. **Update** the "Known issues" section of the affected skill notes.
9. **Show the diff** and offer to commit: `fix-triage: <date> <parent key or "keys"> <n> tickets`. The `jira-intake/`
   folder is git-ignored and stays out of the commit.
````

### 5A.5 `tk-note.prompt.md`

Capture only: it saves the note and nothing else. It doesn't file anything into the backlogs, decisions or open
questions.

````markdown
---
description: Save a general note or a meeting note to toolkit-kb/notes, tidied up and dated
mode: agent
---

Save a note.

Note: ${input:note:Paste or write the note. Say "meeting" if it's from a meeting.}

Product-management mode.

1. **Meeting or general note?**
   - Meeting if I say so ("meeting", "call", "sync", "1:1"), or the note has meeting signs: who was there, "we agreed",
     action items.
   - General note otherwise.
   - If you can't tell, ask me one question: "Is this from a meeting?"
2. **Tidy it up.** You may reword, fix grammar and restructure so it reads clearly. You must not add facts, drop facts,
   or change the meaning, numbers, names or decisions. If something is ambiguous, keep my wording for that part
   and mark it *(unclear)*. Real-initiative details stay as I wrote them: this note is mine, not a backlog item.
3. **Pick a short topic** (3–6 words, kebab-case) from the content, for the file name.
4. **Save it:**
   - Meeting → `toolkit-kb/notes/meetings/YYYY-MM-DD-<topic>.md`:
     ```
     # <Topic>
     - Date: YYYY-MM-DD
     - Who: <attendees, if given>
     ## Notes
     ## Decisions        (only if any were stated)
     ## Action items     (who · what · when, only if any were stated)
     ```
   - General → `toolkit-kb/notes/YYYY-MM-DD-<topic>.md`:
     ```
     # <Topic>
     - Date: YYYY-MM-DD
     <the tidied note>
     ```
   - Use today's date unless I give a different one. If the file name already exists, add `-2`.
5. Show me the saved note. Nothing else: don't create backlog items, decisions or open questions from it.
6. Offer to commit: `note: <topic>`.
````

---

## 5B. Agent skills (`.github/skills/`)

Only these four (D14). **I will provide the `SKILL.md` and script files for all four.** Each skill's folder name and the `name:` in its `SKILL.md` must match, with the `tk-` prefix (D11). This section only
records what each one must do, and where its output goes. Whatever runtime the scripts need (for example Python and
any libraries) is checked when the files arrive (OQ-020 in `open_questions.md`).

**Where the output goes (all four skills):**

| What's being extracted | Destination |
|---|---|
| Material about the toolkit itself (its Confluence docs, design PDFs) | `toolkit-kb/reference/` (Confluence pages under `reference/confluence/`) |
| Production tickets about the toolkit (`tk-jira-scrape`) | `toolkit-kb/backlog/jira-intake/<YYYY-MM-DD>/` (git-ignored) |
| Input for a sandbox run | `runs/sandbox/sources/_extracted/` |
| Input for a real run | `runs/real/<initiative>/sources/_extracted/` (that initiative's folder). Never into `toolkit-kb/` |
| Unclear | Ask |

Extractions go into `_extracted/` so they don't show up as extra uncatalogued sources next to the original. When
cataloguing, treat the original and its extraction as **one** source. Check how the plugin's Rule C scan treats
subfolders (OQ-021 in `open_questions.md`).

### 5B.1 `tk-pdf-scrape-standard/`: placeholder, files provided by user

> **Placeholder.** I will provide `SKILL.md` and the script(s) for this skill. Don't write them from this spec.

**What it is:** the **default** PDF skill. A deterministic scrape: a script pulls the text and tables out of the PDF's
text layer, so the same PDF always gives the same markdown. Fast, and no model interpretation.

**Use it for:** ordinary PDFs with real text, such as briefs, exported docs and reports.

**It must:** never change the original, write to the destination in the table above, and say clearly when it can't
extract well (e.g. a scanned PDF with no text layer, or tables that come out garbled), suggesting
`tk-pdf-scrape-vision` instead of producing an empty or broken file.

### 5B.2 `tk-pdf-scrape-vision/`: placeholder, files provided by user

> **Placeholder.** I will provide `SKILL.md` and the script(s) for this skill. Don't write them from this spec.

**What it is:** vision-mode extraction. It reads each page **as an image**, so it can handle what a text scrape can't:
scanned pages, diagrams, charts, and complex layouts like multi-column pages or merged-cell tables.

**Use it for:** complex PDFs only. **Only** when I ask for it ("extract this PDF with vision"), or when I accept it
after `tk-pdf-scrape-standard` reports it couldn't extract well. It never triggers on a plain "extract this PDF".

**It must:** never change the original, write to the same destinations as the standard skill, and mark anything it
had to interpret (e.g. a diagram described in words, or a number it couldn't read clearly), because unlike the
standard scrape, its output can vary between runs.

### 5B.3 `tk-confluence-scrape/`: placeholder, files provided by user

> **Placeholder.** I will provide `SKILL.md` and the script(s) for this skill. Don't write them from this spec.

What it has to do, whatever the files look like:
- Read a Confluence page (read calls only) and save it as markdown, with its title, source URL and the date it was scraped.
- Never create, update or publish a page. Its description must say so, so it doesn't compete with the PO plugin's
  Stage 6 "publish to Confluence".
- Never ask for or store a token.

**A good first use:** run `tk-confluence-scrape` on the plugin's own Confluence pages (space `<CONFLUENCE_SPACE_KEY>`), including the
Tutorial page, which the screenshots missed. Save them to `toolkit-kb/reference/confluence/`. That gives you a
complete text copy of the docs to set beside the screenshot transcription.

### 5B.4 `tk-jira-scrape/`: placeholder, files provided by user

> **Placeholder.** I will provide `SKILL.md` and the script(s) for this skill. Don't write them from this spec.

What it has to do, whatever the files look like:
- Export Jira issues by key, JQL or filter to markdown: one `<KEY>.md` per issue plus an `_index.md`.
- Read-only: never create, edit, transition or comment on issues, and never score or analyse them. Its description
  must rule out the PO plugin's Jira work (epic quality, PBR, PI planning, publication).
- Production tickets go to `toolkit-kb/backlog/jira-intake/<YYYY-MM-DD>/` (git-ignored, D15).
- Read calls run without asking. Any write would ask (D8), but it should never make one. Never ask for or store a token.

---

## 6. Other files

### 6.1 `neuro_workspace/README.md`

```markdown
# neuro_workspace

Workspace for owning the product-owner-plugin as a product. Open `neuro_workspace.code-workspace`.

- `toolkit-kb/`: product knowledge, backlog, decisions, notes (git)
- `plugin-repo/`: plugin source clone (git, Bitbucket)
- `runs/sandbox/`, `runs/real/`: run outputs from the installed plugin (not in git)
- `.github/`: agent instructions. Start with `copilot-instructions.md`.

Setup spec: `toolkit-kb/workspace/workspace_setup.md`.
```

### 6.2 `toolkit-kb/.gitignore`

```
.DS_Store
Thumbs.db
*.tmp
~$*

# raw Jira scrapes can contain real initiative details (D15)
backlog/jira-intake/
```

### 6.3 Starter content

- `toolkit-kb/README.md`: one paragraph on what the toolkit is, and the folder list from §2.
- `toolkit-kb/backlog/product_backlog.md`: a title plus the empty summary table header from §5.1.
- `toolkit-kb/backlog/fix_backlog.md`: a title plus the empty summary table header from §5.1.
- `toolkit-kb/backlog/done.md`: a title plus the empty summary table header from §5.1.
- `toolkit-kb/backlog/jira-sources.md`: the template from §5.1, with placeholders.
- `toolkit-kb/backlog/jira-intake/`: an empty folder (git-ignored).
- `toolkit-kb/decisions/decision-log.md`: a title and a one-line note: "Product decisions only (DEC-NNN). Workspace decisions are in `workspace/workspace_setup.md` §1." No entries. Do **not** copy the D-decisions in.
- `toolkit-kb/product/how-it-works.md`: a **one-page overview**. A title, plus these headings, each to get a few
  lines (filled in from the walkthrough). Each stage heading links to its `stages/` file, where the detail lives:
  1. What it is and who does what (plugin stack, Working Hub, Knowledge Hub, roles)
  2. Setup
  3. Sources
  4. Sessions
  5. The stage router (A–F)
  6. The stages, one line each: 1 Intake & Ideation · 2 Product Strategy · 3 Project Initiation · 4 Refine & Design ·
     4.5 Construct · 5 PI Planning · 6 Communication
  7. Reference: scoring, errors, skill inventory
- `toolkit-kb/product/glossary.md`: the acronyms table from the build guide, §6. If the guide isn't in the root yet,
  a placeholder (see §9 step 5).
- `toolkit-kb/product/stages/_template.md`: the stage-file format from §5.1.
- `toolkit-kb/product/stages/`: the seven stage files from §2, each with a **title only**. Leave them empty: I populate
  them on the VDI (§11).
- `toolkit-kb/product/skill-notes/_template.md`: the skill-note format from §5.1. Individual notes get created with `/tk-skill-note` after `plugin-repo/` is cloned.
- `toolkit-kb/notes/` and `toolkit-kb/notes/meetings/`: empty folders.

---

## 7. What lives where: quick reference

| I want to… | Go to |
|---|---|
| Understand how a stage or skill works | `toolkit-kb/product/` → then `plugin-repo/` for the truth |
| Document a plugin skill | `/tk-skill-note <skill>` → `toolkit-kb/product/skill-notes/` |
| Log a defect | `/tk-backlog-add` → `toolkit-kb/backlog/fix_backlog.md` (FIX-NNN) |
| Log an idea, improvement or doc gap | `/tk-backlog-add` → `toolkit-kb/backlog/product_backlog.md` (PO-NNN) |
| Triage production tickets from Jira | `/tk-fix-triage scan <deliverable or epic>` or `/tk-fix-triage <KEY>, <KEY>` → `tk-jira-scrape` → fix or product backlog |
| Save Jira issues as markdown | "export these Jira tickets …" → `tk-jira-scrape` skill (read-only) |
| Record a decision | `/tk-decide` → `toolkit-kb/decisions/decision-log.md` |
| Turn a PDF into readable markdown | "extract this PDF …" → `tk-pdf-scrape-standard` |
| Extract a complex PDF (scanned, diagrams, complex layout) | "extract this PDF with vision …" → `tk-pdf-scrape-vision` |
| Save a Confluence page as markdown | "scrape this Confluence page …" → `tk-confluence-scrape` skill (read-only) |
| Change the plugin | in the separate development location (OQ-023). In `plugin-repo/`: local experiments only, on a branch |
| Test a change or a stage | run mode in `runs/sandbox/`, then `/tk-backlog-add` for anything that went wrong |
| Do real PO work | run mode in `runs/real/<initiative>/`, in this same workspace (OQ-016, OQ-024) |

---

## 8. Manual steps (I do these; the agent can't or shouldn't)

The order is: §8 steps 1–6 (set up and bootstrap), then step 7 → §11 VDI tasks (fill in what's missing) → §10 checklist (the last VDI task).

1. **Create the root folder** in a location that survives VDI rebuilds, here `I:\ds\Neuro_Workspace`.
2. **Copy this file** into the root as `workspace_setup.md` (it moves to `toolkit-kb/workspace/` at the end).
3. **Optional: copy `Original_Build_Guide.md`, `open_questions.md` and `product_enhancements.md`** into the root too,
   if I have them on the VDI. Any that are there get moved or merged into place. Any that aren't get a placeholder, and
   I bring them in later with §11 task 0. Skipping this step doesn't block the bootstrap.
4. **Open VS Code** → File → Open Folder → `neuro_workspace`. Open Copilot Chat in **agent mode** with a
   general agent, *not* the Working Hub Guide agent.
5. **Run the bootstrap prompt** (§9). Review each step as it goes.
6. **Reopen** using File → Open Workspace from File → `neuro_workspace.code-workspace`. From now on, always
   open it this way (or from File → Open Recent, where the entry is marked `(Workspace)`). Opening the folder
   directly skips every setting (D2).
7. **Do the VDI tasks in §11**, in order: clone the plugin, point the plugin at sandbox,
   add the skills, and so on. The last one runs the §10 checklist.

---

## 9. Bootstrap prompt (paste into Copilot agent mode)

```
You are setting up my VS Code workspace for owning the product-owner-plugin as a product.
The full spec is in ./workspace_setup.md in this folder. Read all of it before doing anything.

Do the following, in order, and pause after each numbered step to show me what you did:

1. Create every folder and file in §2 that is NOT inside plugin-repo/. Leave plugin-repo/ as an empty folder.
   Under runs/real/ create nothing: initiative folders are made when a real initiative starts.
   Do not create a git repo at the root.
2. Write neuro_workspace.code-workspace exactly as in §3.
3. Write .github/copilot-instructions.md exactly as in §4, the three files in §5 exactly as written
   (including their applyTo frontmatter), the five prompt files in §5A into .github/prompts/.
   Create the four empty skill folders in §5B under .github/skills/. Do NOT write any SKILL.md or script:
   I will provide those files. If I have already put them there, leave them unchanged.
4. Write the README, .gitignore and starter files in §6.
5. Bring in the source files. Each one is OPTIONAL: handle whichever are in the root and skip the rest.
   Don't ask me for missing files and don't stop.
   - If ./Original_Build_Guide.md exists: move it to toolkit-kb/reference/original-build-guide.md and fill
     toolkit-kb/product/glossary.md from the acronyms table in its §6.
     If not: write both files as placeholders (see the placeholder text below).
   - If ./open_questions.md exists: move it to toolkit-kb/open_questions.md, unchanged.
     If not: write toolkit-kb/open_questions.md as a placeholder.
   - If ./product_enhancements.md exists: merge its items into toolkit-kb/backlog/product_backlog.md, keeping their
     PO-NNN IDs and full detail, then delete ./product_enhancements.md (ask me first).
     If not: leave the product backlog as the empty starter from §6.3.
   Placeholder text: a title line, then
   "> PLACEHOLDER: not imported yet (workspace_setup.md §11 task 0). Don't cite this file. If you need it,
   > say it isn't loaded yet."
   Then tell me which files were imported and which are placeholders.
6. Run `git init` inside toolkit-kb/ only, then make the first commit:
   "Initial toolkit-kb scaffold". Do not push.
7. Check this VS Code version against the spec. Don't run the §10 checklist yet: that comes after the VDI tasks
   in §11, once the workspace is opened through its workspace file. For every setting in the workspace file, tell me whether this VS Code version recognises it
   (an unknown setting shows faded or underlined in the settings JSON). Suggest the current name if one was renamed.
   Also check the prompt-file frontmatter: if this version expects `agent:` instead of `mode:`, tell me and fix all five.
   Check whether this version supports agent skills and where it expects them. If I have provided the skill
   files, report what runtime and libraries their scripts need and whether they're installed. Do not install anything.
8. Move ./workspace_setup.md to toolkit-kb/workspace/workspace_setup.md and commit it.

Rules while doing this:
- Do not run any product-owner-plugin skills and do not call Working Hub, Jira or Confluence.
- Ask before running any terminal command that isn't mkdir, file creation, git init/add/commit or git status.
- If anything in the spec is ambiguous or doesn't fit this machine, stop and ask me. Don't guess.
```

### Follow-up prompt once `plugin-repo/` is cloned

```
plugin-repo/ is now cloned. Product-management mode.
1. Show me the top-level structure of plugin-repo/ (2 levels deep) and tell me where the skills,
   templates, SETUP.md and any scripts live.
2. Check whether plugin-repo/ has its own .github/copilot-instructions.md or AGENTS.md and summarise it.
3. List every skill you find, and compare it with the skill inventory in
   toolkit-kb/reference/original-build-guide.md §13. Report: in both / only in the docs / only in source.
4. Don't change anything. Offer doc-gap backlog items for any differences.
5. Suggest an order for running /tk-skill-note on each skill (stage order, starting with the shared ones like working-hub).
```

After that, run `/tk-skill-note <skill>` one skill at a time and review each note before moving on.

---

## 10. Verification checklist

### Verify after setup

- [ ] The title bar reads `neuro_workspace (Workspace)`, so the workspace file's settings are active (D2).
- [ ] Explorer shows a single root `PO-TOOLKIT-PRODUCT` with all subfolders (not several roots).
- [ ] Auto-approve works as intended (D8):
  - `git status` in `toolkit-kb/` runs **without** asking.
  - `git fetch` in `plugin-repo/` **asks** first. Decline it.
  - A `curl` / `Invoke-RestMethod` GET to Jira runs **without** asking. The same call with `-Method Post` **asks**.
  - A Working Hub status check (`GET …/status`) runs **without** asking. A `POST` to `…/approvals` **asks** first.
    Decline it, and use a sandbox initiative if you test this at all.
  - `Remove-Item runs/sandbox/test.txt` (on a throwaway file) **asks** first.
  - Ask the agent to "delete runs/sandbox/test.txt". It uses the terminal (so it asks), not an edit tool.
  - If any of these runs without asking, the `false` rules aren't winning. Check whether a user-level
    `autoApprove` setting is overriding this one, and check the regex.
- [ ] Source Control shows two repos: `toolkit-kb` and `plugin-repo`. No repo at the root.
- [ ] Copilot picks up `.github/copilot-instructions.md`. Test: ask "what are the two modes in this workspace?"
- [ ] Per-folder instructions load. Test: open a file under `plugin-repo/` and ask "what are the rules for this folder?"
- [ ] Each setting in the workspace file is recognised by this VS Code version (no faded or unknown entries).
- [ ] A search for any term doesn't return results from `runs/`.
- [ ] The terminal opens in PowerShell.
- [ ] Mode guard test: say "check epic quality". The agent should explain the skill, not run it.
- [ ] Mode switch test: say `run mode: sandbox`. It confirms the mode and LOCAL_PROJECT_ROOT in one line, and its
      replies start with `[run: sandbox]`. Say `exit run mode`: it confirms, and the tag disappears.
- [ ] Typing `/tk` in chat lists the five prompt files (`/tk-backlog-add`, `/tk-decide`, `/tk-skill-note`,
      `/tk-fix-triage`, `/tk-note`) and nothing else.
- [ ] `/tk-note` test: "meeting with WH team, we agreed to test commits in sandbox first, Sam to check access". It saves to
      `notes/meetings/` with the action item listed. "idea: a gate summary view" saves to `notes/` as a general note.
- [ ] toolkit-kb-first test: ask "what do we know about the epic-quality skill?" The agent should look in
      `toolkit-kb/product/skill-notes/` first, and say the note doesn't exist yet rather than answer from memory.
- [ ] No setting anywhere includes a `plugin-repo/` path.
- [ ] Pushing is disabled: `git remote -v` in `plugin-repo/` shows `DISABLED` as the push URL, and
      `git remote set-url --push origin x` **asks** first. Decline it.
- [ ] Skill files are in place: each folder under `.github/skills/` has my `SKILL.md` and scripts (§5B), not ones the
      agent wrote.
- [ ] Skills load: ask "what skills do you have in this workspace?" It should list `tk-pdf-scrape-standard`, `tk-pdf-scrape-vision`,
      `tk-confluence-scrape` and `tk-jira-scrape` only. None of the PO plugin's skills should appear as *workspace* skills.
- [ ] `tk-pdf-scrape-standard` test: put any non-sensitive PDF in `runs/sandbox/sources/` and say "extract this PDF".
      `tk-pdf-scrape-standard` runs (not the vision one) and writes to `runs/sandbox/sources/_extracted/`.
- [ ] `tk-pdf-scrape-vision` test: with a non-sensitive scanned or diagram-heavy PDF, say "extract this PDF". The standard
      skill reports it couldn't extract well and offers vision. Say yes: `tk-pdf-scrape-vision` runs, and marks anything
      it interpreted.
- [ ] `tk-confluence-scrape` test: "scrape this Confluence page <a page from the plugin docs space>". The output goes to
      `toolkit-kb/reference/confluence/`. Only read calls are made.
- [ ] `tk-jira-scrape` test: "export Jira ticket <a non-sensitive key> to markdown". It runs without asking,
      writes `<KEY>.md` and `_index.md`, and makes only read calls.
- [ ] `jira-intake/` is ignored: after a scrape, `git status` in `toolkit-kb/` doesn't show it.
- [ ] Backlog routing: `/tk-backlog-add` with "the commit step fails with path_out_of_area" goes to `fix_backlog.md` as a
      FIX. `/tk-backlog-add` with "add a summary view of all gates" goes to `product_backlog.md` as a PO.
- [ ] `/tk-fix-triage` keys mode: give two non-sensitive keys, one of them already on a backlog item. It shows a
      triage table with that one as "already tracked", and writes nothing until you approve.
- [ ] `/tk-fix-triage` scan mode: give an epic key. It reports how many open children it found before triaging.
- [ ] Trigger separation (Jira): say "check epic quality for <key>". `tk-jira-scrape` must **not** load.
- [ ] Trigger separation: say "publish this to Confluence". `tk-confluence-scrape` must **not** load. The agent should say
      that publishing happens in run mode with the PO plugin.

---

## 11. VDI tasks

The scaffold leaves these as placeholders or empty files. Each one needs me to do something on the VDI before that
part of the workspace is usable. Work through them in order, because later tasks depend on earlier ones. Task 0 is only needed if the bootstrap
left placeholders. §8 and §9 say
*how* to set the workspace up. This list says *what's still missing* afterwards.

| # | Task | What's missing | How | Needs | Spec |
|---|---|---|---|---|---|
| 0 | **Bring in the source files** (only the ones the bootstrap left as placeholders) | Any of `toolkit-kb/reference/original-build-guide.md`, `toolkit-kb/product/glossary.md` and `toolkit-kb/open_questions.md` that still say PLACEHOLDER. And the product backlog, if `product_enhancements.md` wasn't merged | Put the files in the root and ask the agent: "Do §9 step 5 again for the files now in the root, replacing the placeholders, then commit in toolkit-kb/." Do it before tasks 5 and 6 and the §9 follow-up prompt, which all read the build guide. Until it's done, OQ-NNN references in this spec (OQ-013, OQ-014, OQ-020–022) point at nothing | The three files | §9 step 5 |
| 1 | **Clone the plugin source** into `plugin-repo/`, then disable pushing | `plugin-repo/` is empty, and the clone URL is a placeholder (`<PLUGIN_REPO_SSH_URL>`) | See the commands below the table | SSH key on Bitbucket | D5 |
| 2 | **Point the installed plugin at sandbox** | `LOCAL_PROJECT_ROOT` in the installed plugin's `SETUP.md` | Set it to `I:\ds\Neuro_Workspace\runs\sandbox` | Plugins installed (OQ-014) | §2 |
| 3 | **Build and add the 4 skills**, one at a time: `tk-pdf-scrape-standard`, `tk-pdf-scrape-vision`, `tk-confluence-scrape`, `tk-jira-scrape` | Each folder in `.github/skills/` is empty: no `SKILL.md`, no scripts | Build each one from what I have on the VDI. The folder name and the `name:` in `SKILL.md` match, with the `tk-` prefix. Meet the "it must" points in §5B. Check the runtime the scripts need (OQ-020). Test each one with its §10 check before starting the next | — | §5B, D14 |
| 4 | **Scrape the plugin's Confluence docs** | `toolkit-kb/reference/confluence/` is empty | Use `tk-confluence-scrape` on the plugin's pages (space `<CONFLUENCE_SPACE_KEY>`), including the Tutorial page the screenshots missed | Task 3 (`tk-confluence-scrape`) | §5B.3 |
| 5 | **Write the skill notes**, one per plugin skill | `toolkit-kb/product/skill-notes/` has only `_template.md` | Run the follow-up prompt in §9 to list the skills, then `/tk-skill-note <skill>` for each, in stage order. Review each note before the next | Task 1 | §5A.3, §9 |
| 6 | **Populate the 7 stage files** (Stages 1, 2, 3, 4, 4.5, 5, 6) | Each `stages/stage-*.md` has a title only | Fill each one from `stages/_template.md`, using the Confluence pages (task 4), the plugin code (task 1), the skill notes (task 5) and the build guide. Cite every claim. Link gaps as OQ-NNN items | Tasks 1, 4, 5 | §5.1 stage-file format |
| 7 | **Write the overview** | `how-it-works.md` has headings only | A few lines per heading, summarising the stage files. Link each stage line to its file | Task 6 | §6.3 |
| 8 | **Fill in where the toolkit's Jira tickets live** | `toolkit-kb/backlog/jira-sources.md` has placeholders | Record the Jira project, how items hang off a deliverable, and the parents to scan (OQ-022). Until then, `/tk-fix-triage` works in keys mode only | Access to Jira | §5.1, §5A.4 |
| 9 | **Run the verification checklist** | Nothing confirms the setup works yet | Go through §10. Re-run the skill checks after task 3, and the Jira checks after task 8 | Tasks 1–3 | §10 |

**Task 1 commands.** The marketplace repo is
`<MARKETPLACE_REPO_SSH_URL>`. Check whether the plugin
has its own repo or lives inside the marketplace repo (OQ-013), and clone whichever holds the source:
```powershell
cd I:\ds\Neuro_Workspace
git clone <PLUGIN_REPO_SSH_URL> plugin-repo
cd plugin-repo
git remote set-url --push origin DISABLED
```

**Answering open questions.** Several of these tasks will answer questions in `toolkit-kb/open_questions.md` along
the way. Fill in each Answer as you go, with the evidence.
