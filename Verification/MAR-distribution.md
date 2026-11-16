# CP1-MD1 buffered memory address candidate

MD1 adds two **SN74AHCT244N DIP-20** buffers and two through-hole 100 nF decoupling capacitors to CA1. Open `Circuits/KiCad/Integrated/candidates/MD1/MD1.kicad_sch`; its seventeen native sheets contain 610 fitted candidate component records, including 272 DIP logic/memory ICs.

The memory-side address loads move behind the new buffers. The raw MAR bus still drives the existing HCT245 source-bus input, MQ1's live-address input and one new buffer input. MQ1 retains its original latency and distributed reset branch. The CPU DIN contact allocation is unchanged.

## Load allocation

| Stage | Previous IC-only subtotal | MD1 IC-only subtotal | Parasitic allocation | Total planning load | Margin to 50 pF fixture |
| --- | --- | --- | --- | --- | --- |
| Raw MAR0–13 | 44 pF | 30 pF | 15 pF | 45 pF | 5 pF |
| Raw MAR14–15 | 48 pF | 30 pF | 15 pF | 45 pF | 5 pF |
| Buffered memory address0–13 | Part of raw MAR load | 24 pF | 15 pF | 39 pF | 11 pF |
| Buffered memory address14–15 | Part of raw MAR load | 28 pF | 15 pF | 43 pF | 7 pF |

Every path has four attached IC pins: one driver and three receivers. The 15 pF design allocation comprises 1 pF per attached socket pin, 6 pF for trace/via/pad capacitance and 5 pF for a probe. These are layout/component-selection targets, not measured or manufacturer-guaranteed parasitics. Actual socket, routing and probe choices must fit them or trigger a revised budget and timing assessment. No DIN contacts lie on these local raw/buffered address paths; MQ1 drives the separate live-address DIN paths.

The pin-capacitance conditions from LL1 still apply. HCT245 A-port capacitance is an unguaranteed 10 pF allocation; AHC/AHCT Ci values are conditional at 5 V; memory capacitance maxima apply at 25 °C. Thus the table establishes positive **planning margins**, while every complete physical load remains unknown across OC1. It does not close the parent full-envelope electrical acceptance gate.

The candidate uses an existing R2 part type rather than substituting another logic family. Exact inventory, socket/PCB placement, supply decoupling performance and procurement remain open. The two new capacitors inherit the existing through-hole footprint and generic value; no manufacturer or owned quantity is inferred.

## Physical-pin verification

MB1 contains U17001 for address bits 0–7 and U17002 for bits 8–15. Both active-low enable inputs of each buffer are tied to the memory-card ground domain. Pins 20/10 connect to that card's supply/ground. C17001/C17002 provide local 100 nF decoupling connections.

All three original ME1 receivers of each address bit move to its buffered output. Original module/reference/pin identities remain in `final/provenance.json` and `final/loads.json`. New buffer input and output pins are taken from the native embedded AHCT244 symbol, and the HDL mapping is derived from the independently exported pin groups.

The complete export has **7,368 pins in 2,436 unmated groups**. Checking those groups detects any accidental bypass between buffer input and output. A separate logical contraction of the sixteen always-enabled transfers, followed by removing the four added component records, reproduces CA1's complete unmated pin graph exactly. This contraction expresses steady-state logical equivalence, not a physical short or a zero-delay claim. Existing card/contact isolation remains checked upstream.

Three native mutations are rejected: swapping buffered address bits 0/1, bypassing the buffers with shared labels, and tying the first output-enable group high. The bypass and disable faults can both leave the contracted graph correct; the separate physical graph rejects them. A fresh export from the checked-in native hierarchy also passes.

## Affected simulations

Only ME1's sixteen address input assignments change in the pinned CPU/memory models. Their source bits and enabled/disabled states come from the exported buffer pin mapping. The maximum profile adds 9.5 ns per buffer, using the inherited R2 AHCT244 timing-table bound. Zero and mixed 0/9.5 ns profiles are sensitivity cases; zero is not a characterized physical minimum. Characterized load and input waveform conditions remain prerequisites for applying that bound physically.

The exhaustive transfer test checks all **65,536 address words**. Swapped-address and disabled-buffer variants both fail that test.

The complete maximum-delay memory exercise passes **131,073 reads, 48,897 writes, 16,384 protected-write checks and 256 IO cases**. It retains the previous standalone fixture that loops SOURCE to DATA; the integrated CPU cases below exercise the actual BF1/DT1 composition.

| ROM/text profile | Buffer delays | Minimum sampled CPU IO setup | Minimum sampled CPU IO hold |
| --- | --- | --- | --- |
| Maximum | 9.5 ns | 81.5 ns | 425.5 ns |
| Zero sensitivity | 0 ns | 710 ns | 250 ns |
| Mixed 2 | Alternating 9.5/0 ns | 373 ns | 367 ns |
| Mixed 3 | Alternating 0/9.5 ns | 352 ns | 364.5 ns |

All four runs start at ROM PC zero with the 25 ms startup guard, deposit the complete 160-byte payload into poisoned SRAM, jump to `$4000`, perform the text/IO diagnostic and finish `TX1\r\n` after CPU HALT. Every passing run reports zero timing-monitor violations. The swapped-address CPU run fails the loader's first write-address check (`got=a540`), so the new physical mapping is exercised by boot rather than merely checked in isolation.

These results cover the affected memory, boot and IO paths at the selected 500 kHz microcycle contract. They do not repeat the unchanged all-opcode suite or promote MD1 into R2. DATA-bus disable, SRAM release fixtures, CDC, full min/max timing, loaded slew and powered-off behavior remain open.

## Replay and preserved evidence

`iteration-1` preserves the first passing native topology and mutations. `final` adds explicit load budgets, native-to-model bindings and the independent canonical export. `simulation-1` preserves all nine runs: one exhaustive pass, two exhaustive faults, four boot passes, one boot fault and one full memory pass. `failed-regression-1` preserves the first full harness failure: two isolated-replay tests exposed five omitted original memory-fixture dependencies. The corrected lock declares all simulation input files explicitly.

Restore LL1, CA1 and their earlier dependencies through `Backup/README.md`, then restore `build/cp1-mar-distribution/`. Regenerate into new folders:

```sh
PYTHONPATH=Verification python3 -m dm02.mar_distribution \
  --output Verification/build/mar-distribution-new
```

`mar-distribution-evidence.json` pins the native sources, graph/load results, actual models, input fixtures and logs. Bounded replay regenerates the native text and load inventory, verifies the sixteen model transformations against the pinned baseline, and checks saved simulation evidence. Eight focused tests cover isolation, logical contraction, native-derived fault mapping, all 32 stage budgets, incomplete binding, omitted boot evidence and complete fixture-dependency declaration.

The Jev workflow skill was unavailable; no advisory or independent review is claimed. Physical qualification and production-source promotion remain in Beads. CP1-R2 stays the accepted digital revision.
