# CP1-NA1 native assembly candidate

NA1 composes the eleven R2 CPU modules, MQ1, BR1 and TX1 into one native KiCad hierarchy. Open `Circuits/KiCad/Integrated/candidates/NA1/NA1.kicad_sch`. The fifteen checked-in schematic files contain their symbol definitions and use unique component references and per-sheet library namespaces.

KiCad's independent export matches **6,491 physical pins in 1,762 net groups**, with 648 component records. Of those, 590 retain candidate fitted status and 58 are explicitly excluded from both BOM and board transfer. The excluded symbols mark logical R2/MQ1/BR1 boundaries; they are not additional fitted connectors. Component values, footprint references, pin names/types and fitted flags are checked as well as connectivity.

## Package allocation

| MC1 role | Functional modules | DIP logic/memory ICs |
| --- | --- | --- |
| Control | CW1, SQ1 | 35 |
| Compute | AL1, RG1 | 38 |
| Counters | PC1, SP1 | 35 |
| Memory | MA1, ME1, MQ1 | 64 |
| Active backplane | C1, DT1, BF1, BR1 | 61 |
| Text | TX1 | 37 |
| Total | | 270 |

This is the combined R2/BR1/TX1 candidate count, before supervisor, operator-control and debugger additions. Physical placement and complete load/current/timing budgets remain open.

## Connection method

R2 cross-sheet aliases come from the locked BP1 native export and its connection table. Equal local labels on different sheets do not create connections by themselves. MQ1/BR1 joins use the previously verified physical connector-pin bindings and the 17 CN1 memory extensions. The native candidate exposes these joins as globally named nets while retaining the original embedded symbols, physical pins and component geometry.

MQ1 receives the distributed `ME1_RESET_n` branch at ME1 J1.6. BR1 receives the reset root at C1 J90.4. These nets remain distinct. The live MAR read-address path is separate from ME1's registered write address. All 96 slot-5 contact assignments are checked; assigned contacts join BR1 J5 to TX1 J1 by contact number, and unused contacts retain their unconnected status. TX1's ground strap defines slot-5 presence. This logical mating does not qualify connector orientation, keying or mechanical fit.

The original module reference is retained in the provenance table. Each module receives a distinct thousand-number annotation range: for example, ME1 U1 becomes U9001 and TX1 U1 becomes U14001. Internal symbol IDs also receive a module-specific namespace, such as `NA1_ME1:U1`.

## Verification and preserved failures

The final hierarchy and a separate export from the checked-in candidate both pass the full graph and metadata comparison. Three independently exported mutations fail with explicit missing/extra pin groups:

- MQ1 reset joined to the root instead of the memory branch.
- BR1 live read-address bit zero joined to the registered write address.
- TX1 return bit zero joined to slot 6's private return.

The first iteration passed pin-group parity but reused `DM02:U1` and similar symbol IDs across sheets. KiCad's exported library metadata consequently described some components with another sheet's pin definitions. The expanded checker rejects this iteration even though its component values and pin connectivity match. It is preserved with both its original result and `metadata-recheck.json`.

The second iteration introduced unique library namespaces and enlarged page canvases to contain the inherited layouts. The third added explicit model-port binding evidence, but bounded replay exposed nondeterministic ordering and tuple/list representation in mutation reports. The final checker emits sorted JSON-native pin lists. All three development iterations remain archived.

Five focused tests cover the final replay, the real library-ID failure, a pin-type-only mutation, a boundary marker incorrectly made fitted, and omitted mutation evidence.

## Relationship to TB1

The native export verifies 134 explicit boundary bindings against the existing TB1 composition. It checks the separate reset branches, live versus registered addresses, memory extensions and assigned slot-5 contacts. The checker also verifies the exact bridge/text instance argument order in the pinned TB1 probe.

This is static pin-graph and port-binding equivalence. The ROM-startup results remain the six previously recorded TB1 runs; no new dynamic simulation or electrical qualification is claimed for NA1. TB1's slot-6 endpoint remains an external behavioral test fixture. It is not a fitted NA1 peripheral. Changes to functional connections require affected simulation and a new candidate evidence set.

## Source and acceptance scope

The hierarchy is a checked-in integration candidate. R2 remains the accepted digital circuit. CPU-card DIN connectors, complete service/operator circuitry, exact fitted BOM and footprint qualification, production schematic layout, ERC closure, board placement/routing and physical acceptance remain in Beads. Existing BR1/TX1 connector part numbers are inherited candidates, not newly approved purchase selections.

The native child sheets retain the functional layouts from the accepted modules and candidate studies. Their page canvases now contain those layouts; production redraw and review remain separate work. Embedded symbols make the hierarchy viewable without the historical legacy symbol-library paths. Footprint libraries and the unresolved mechanical choices still require qualification.

The Jev workflow skill was unavailable; no advisory acceptance result is claimed.

## Reproduction

Restore the R2, BR1, TX1, TB1 and other bounded-replay dependencies from `Backup/README.md`. Generate into a new directory:

```sh
PYTHONPATH=Verification python3 -m dm02.native_assembly \
  --output Verification/build/native-assembly-new
```

`native-assembly-evidence.json` pins the checked-in hierarchy, generator, original native inputs and saved exports. Bounded replay regenerates all final and mutated schematic text, compares physical pin groups and component metadata, and rechecks the TB1 bindings. Keep the locked studies and prior candidates intact when making a revision.
