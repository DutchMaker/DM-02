# CP1-CA1 CPU connector assembly candidate

CA1 implements the CN1 CPU-card contact allocation in a native KiCad hierarchy. Open `Circuits/KiCad/Integrated/candidates/CA1/CA1.kicad_sch`. Its sixteen native schematic files retain the fourteen NA1 functional modules and add a CPU-connector sheet.

The candidate has **16 fitted DIN96 connectors**, representing eight card/backplane pairs, and checks **768 mating contacts / 1,536 connector pins**. It removes all 58 non-fitted NA1 boundary-marker symbols and their orphan labels/no-connect marks. The result has 606 component records, all marked for candidate BOM/board transfer, including the unchanged 270 DIP logic/memory ICs. Exact parts and physical acceptance remain open.

## Contact allocation

| CPU role | Baseline signals | New memory signals | Card connectors | Backplane connectors |
| --- | --- | --- | --- | --- |
| Control | 71 | 0 | J15001, J15002 | J16001, J16002 |
| Compute | 57 | 0 | J15003, J15004 | J16003, J16004 |
| Counters | 66 | 0 | J15005, J15006 | J16005, J16006 |
| Memory | 92 | 17 | J15007, J15008 | J16007, J16008 |

The 768 paired contact positions comprise 303 signal assignments, 32 supply contacts, 256 ground contacts and 177 unused/reserved contacts. Each card has two 96-position connectors. The memory additions carry `LIVE_ADDRESS0–15` and `IO_READ_VALID`; they are driven by MQ1 and retain the existing BR1 bindings.

Card-side values/footprints are inherited from the TX1 candidate (`09031966921`, male horizontal THT), and backplane-side values/footprints from BR1 (`09032966824`, female vertical THT). These remain candidate identities. Connecting identical contact numbers in the verification graph does not qualify mating-face orientation, coding, stack fit, current capacity or parasitic loading.

## Two graphs, checked separately

The exported native circuit assigns each CPU card its own net domain. A card's power, ground and signal nets are distinct from the backplane's nets until mating is applied. The existing NA1 text/backplane composition remains in one shared domain; CA1 changes the CPU-card boundaries specifically.

The first comparison checks the **unmated** KiCad netlist against the four card domains and backplane/text domain. It includes every connector pin, component value, footprint reference, pin name/type and fitted flag. This rejects accidental shared-label connections across CPU cards.

The second comparison joins only the declared matching card/backplane contacts. It then removes the new connector pins from the comparison and checks every remaining physical-pin group against NA1 with its non-fitted boundary markers removed. All 5,788 functional component pins match in 1,755 groups. The seven NA1 groups containing only boundary markers disappear with those markers.

The complete unmated export contains **7,324 pins in 2,420 net groups**. The root reset and distributed reset branches, private source buses, registered write addresses and live-read extensions retain their distinct functional connections after mating. There is no new dynamic simulation: this is static equivalence to the NA1/TB1 composition. Added connector capacitance, trace lengths, ground/supply impedance and edge behavior still require full-link qualification.

## Mutations

| Mutation | Unmated differing groups | Mated functional differing groups |
| --- | --- | --- |
| Reverse a/c contact rows on the first counter-card connector | 112 | 112 |
| Disconnect the memory card's `IO_READ_VALID` contact | 3 | 3 |
| Connect compute `BRANCH0_0` to `DATA0` | 4 | 4 |
| Bypass all CPU connector boundaries with shared global labels | 713 | 0 |

The bypass mutation is an important check on the method: a fully mated comparison alone accepts it, because the final functional connections are correct. The unmated comparison rejects the hidden inter-card connections.

Five focused tests cover the pinned matrix, the bypass, the three functional wiring mutations, a changed connector footprint with otherwise correct nets, and omitted bypass evidence.

## Preserved development and source scope

`iteration-1` passed connectivity but left orphan labels and no-connect graphics at removed boundary symbols. The final generator removes those graphics and labels child sheets as CA1. Both versions remain archived. A second independent export from the checked-in CA1 hierarchy also passes.

The native files embed their symbol definitions and preserve NA1's unique per-module library namespaces and references. The new DIN96 symbol has its own `CA1:DIN96` identity. Each connector records its card role, side and P1/P2 allocation in the schematic and provenance table.

This remains a combined connectivity candidate, not separate released PCB projects. Production redraw/readability, ERC closure, exact fitted BOM and mechanical qualification, physical service/operator interfaces, board placement/routing and loaded electrical timing remain in Beads. Removing logical boundary markers does not implement those missing external interfaces. CP1-R2 remains the accepted digital circuit.

The Jev workflow skill was unavailable; no advisory result is claimed.

## Reproduction

Restore the dependencies in `Backup/README.md`, including NA1, then generate into a new directory:

```sh
PYTHONPATH=Verification python3 -m dm02.connector_assembly \
  --output Verification/build/connector-assembly-new
```

`connector-assembly-evidence.json` pins the generator, source hierarchy, native exports and all mutations. Bounded replay regenerates the final and mutated schematic text and rechecks both connectivity graphs. Functional changes require affected simulation and a new evidence revision; preserve the existing locks and candidates.
