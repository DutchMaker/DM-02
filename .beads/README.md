# DM-02 work tracking

Beads is the project backlog for getting from CP1-R2 to a fabricatable PCB set
and a measured, working computer. Issues contain acceptance criteria, source
references, formal requirement mappings and blocking dependencies.

Start with `bd show dm02-57n` for the programme. The fabrication gate is
`dm02-57n.7.5`; working-machine acceptance is `dm02-57n.8.8`.

## Daily use

```sh
bd prime
bd ready --exclude-type epic
bd ready --label work-agent --exclude-type epic
bd list --label work-owner --limit 0
bd list --type milestone
bd show <id>
bd update <id> --claim
bd close <id> --reason "Evidence path, revision and acceptance result"
bd blocked
```

`bd dep add <dependent> <prerequisite>` means the prerequisite must finish
first. Parent/child links group work; blocking links determine readiness.
Keep findings and corrective work in Beads rather than parallel Markdown lists.

## Acceptance and labels

The backlog has two distinct release milestones: **ready for fabrication** and
**working hardware accepted**. Pre-fabrication measurements use representative
circuits or coupons; the final-board qualification follows fabrication.

CP1-R2's digital acceptance, schematic/package checks and verified archive are
recorded as closed baseline issues with their original scope. The formal
milestone 1–3 totals remain 3/5, 3/5 and 8/9. Closing a Beads issue never changes
a technical gate without current supporting evidence.

- `phase-prefab`, `phase-fabrication`, `phase-postfab`: delivery stage.
- `phase-baseline`: completed evidence inherited from CP1-R2.
- `area-*`: engineering workstream.
- `work-agent`: primarily source, design, analysis or verification work.
- `work-owner`: owner decision, stock confirmation or purchasing action.
- `work-bench`: physical hardware/equipment access required.
- `work-reviewer`: independent review required.
- `req-BASE-02`, `req-PCB-01`, etc.: formal requirements from
  `Verification/requirements.json`.
- `release-gate`: fabrication or working-machine acceptance milestone.

P1 work resolves release-critical dependencies; P2 is supporting work that can
be scheduled behind those decisions. Priority does not waive prerequisites.
Owners/reviewers and physical observations must be real; an agent can prepare
their inputs but cannot infer approval or measurement results.

## Storage and recovery

Initialised with Beads 1.3.4 using embedded Dolt and issue prefix `dm02`.
The local database is under `.beads/embeddeddolt/` (ignored by Git). Code and
configuration live on `master`; the Beads database uses `refs/dolt/data` on
the same `DutchMaker/DM-02` GitHub repository. JSONL exports are interchange
snapshots, not the database or the sync protocol.

On a fresh clone with a compatible `bd` installed:

```sh
bd bootstrap --yes
bd prime
bd status
bd ready --exclude-type epic
```

For an existing workspace, use `bd dolt pull` before editing shared work and
`bd dolt push` when authorised to publish. Push code changes separately with
Git. Do not reinitialise or import an old JSONL snapshot over live work.

On a machine with multiple GitHub accounts, use the authorised DutchMaker
credential for both pushes; keep tokens in the environment/credential helper,
never in configuration or issue descriptions. `bd init` installs Git and
agent hooks. Full `bd doctor` is unavailable in 1.3.4 embedded mode; use the
supported checks plus `bd ping`, `bd lint --status all`, `bd dep cycles` and
a fresh-clone recovery check.

For hardware evidence restoration, follow `Backup/README.md`. Beads recovery
does not restore the large simulation release assets. The live evidence
dashboard remains at <https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/>.
