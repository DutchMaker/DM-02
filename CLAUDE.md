# Project Instructions for AI Agents

This file provides instructions and context for AI coding agents working on this project.

<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:1105d646 -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

**Architecture in one line:** issues live in a local Dolt DB; sync uses `refs/dolt/data` on your git remote; `.beads/issues.jsonl` is a passive export. See https://github.com/gastownhall/beads/blob/main/docs/core-concepts/sync-concepts.md for details and anti-patterns.

## Agent Context Profiles

The managed Beads block is task-tracking guidance, not permission to override repository, user, or orchestrator instructions.

- **Conservative (default)**: Use `bd` for task tracking. Do not run git commits, git pushes, or Dolt remote sync unless explicitly asked. At handoff, report changed files, validation, and suggested next commands.
- **Minimal**: Keep tool instruction files as pointers to `bd prime`; use the same conservative git policy unless active instructions say otherwise.
- **Team-maintainer**: Only when the repository explicitly opts in, agents may close beads, run quality gates, commit, and push as part of session close. A current "do not commit" or "do not push" instruction still wins.

## Session Completion

This protocol applies when ending a Beads implementation workflow. It is subordinate to explicit user, repository, and orchestrator instructions.

1. **File issues for remaining work** - Create beads for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **Handle git/sync by active profile**:
   ```bash
   # Conservative/minimal/default: report status and proposed commands; wait for approval.
   git status

   # Team-maintainer opt-in only, unless current instructions forbid it:
   git pull --rebase
   git push
   git status
   ```
5. **Hand off** - Summarize changes, validation, issue status, and any blocked sync/commit/push step

**Critical rules:**
- Explicit user or orchestrator instructions override this Beads block.
- Do not commit or push without clear authority from the active profile or the current user request.
- If a required sync or push is blocked, stop and report the exact command and error.
<!-- END BEADS INTEGRATION -->


## DM-02 engineering context

- Goal: fabrication-ready PCB designs followed by a demonstrably working TTL computer. Beads task closure does not replace technical acceptance evidence.
- Start from CP1-R2 and `Verification/CP1.md`. Preserve the locked overlay, archived evidence and failed runs; changes require affected verification and a new accepted revision.
- All logic and memory must be DIP; other fitted components through-hole. Prefer owned parts, but never infer an exact manufacturer/suffix/count or substitute HCT/HC/AHCT/ACT without qualification.
- Owner clarification (2026-11-16): 1 MHz is preferred, not mandatory; a lower clock is acceptable if the chosen ICs cannot feasibly support it. Prioritise reliable operation and timing margin. Select and document the actual rate; the conditional 500 kHz microcycle evidence is not physical qualification. Voltage/temperature requirements are unchanged.
- CP1-OC1 (`Verification/operating-contract.json`) selects 4 MHz oscillator / 500 kHz microcycles, 4.75–5.25 V at IC pins and 0–50 °C. New budgets and qualification plans use this contract and the generated `build/cp1/qualification-matrix.json`. The root requirements file is a frozen historical input; the active report composes the live envelope separately. Contract selection does not qualify physical operation.
- CP1-SC1 / CP1-IO1 (`Verification/IO-interface.md`, `io-interface.json`) define the approved text-first expandable stack/backplane scope and logical IO protocol. An external ESP32/LCD debugger may use non-74xxx/SMD parts; computer/peripheral boards remain DIP/through-hole and must operate independently. R2 J902 carries a registered write address; J903 has no live read-address/qualifier. The new bridge is unimplemented; do not decode reads from the write latch or infer physical acceptance from protocol checks.
- Use `work-owner`, `work-bench` and `work-reviewer` labels to identify decisions, physical measurements and independent review. Do not fabricate their evidence. Track remaining work only in Beads.
- Normal bounded replay: `python3 Verification/run.py --allow-design-failures`. Harness: `PYTHONPATH=Verification python3 -m unittest discover -s Verification/tests -v`. Restore archived dependencies using `Backup/README.md` first. Do not repeat unchanged long boot simulations.
- See `.beads/README.md` for workflow, issue labels, remote recovery and the two release gates. Code and Beads data use separate Git refs; publish both when authorised.
