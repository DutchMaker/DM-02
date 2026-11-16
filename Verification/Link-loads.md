# CP1-LL1 whole-link load inventory

LL1 inventories the exported CA1 assembly at physical-pin level. It covers **7,324 pins, 2,018 fitted connector pins and 1,708 potential-driver scenarios**. All physical load totals remain unknown because socket, connector, routing, cable and probe capacitances have not been qualified.

## Electrical findings

| Path | IC-only subtotal | Comparison |
| --- | --- | --- |
| MAR bits 0–13 | 44 pF each | 49 pF with the previous 5 pF planning allowance, against a 50 pF fixture |
| MAR bits 14–15 | 48 pF each | 53 pF with that allowance, exceeding the 50 pF screen |
| DATA0–3 | 100 pF each | HCT245 data/enable fixture is 150 pF; disable fixture is 50 pF |
| DATA4–7 | 90 pF each | Same separate data/enable and disable fixtures |
| SRAM RAM0–7 | 20 pF per active driver | SRAM read fixture is 30 pF; output-release fixture is 5 pF |
| C1 and TX1 oscillator outputs | 10 pF each | 5 pF remains against the selected ACH 15 pF load before unknown parasitics |

These subtotals mix manufacturer table maxima under stated conditions with explicit allocations. They are neither measured capacitances nor guaranteed full-envelope upper bounds. Exceeding a fixture identifies an unsupported timing assumption; it does not establish that the physical circuit fails.

Each MAR bit has one additional MQ1 receiver relative to R2. Bits 14–15 have higher pre-existing loading. The MAR storage pins and MQ1 inputs are on the same memory card; the new DIN contacts carry MQ1's buffered live-address outputs. The inventory follows that distinction rather than assigning the connector capacitance to the original MAR taps.

The eight DATA paths each have eight fitted CPU contact pins. All 39 pull resistors are listed with both physical pins, their rail and nominal resistance; tolerances and parasitic capacitance remain unknown. TX1's 1 kΩ serial resistor is a separate RC path to J2. Its remote receiver/cable load stays unknown and is not shorted into the direct-net capacitance sum.

## Native graph and counting rules

The input is `cp1-connector-assembly/final/native/CA1.xml`, checked against CA1's complete unmated and mated graph before accounting begins. Manufacturer pin metadata comes from its embedded library definitions. Provenance maps every fitted component to its original module/reference and physical card.

LL1 applies the 768 CPU contact pairs and accounts for all 96 slot-5 pairs, for **864 mating pairs**. Slot-5 used contacts already share CA1's backplane/text net domain; their two physical pins are still counted once each. Mating its unused positions changes no functional load. The resulting 1,908 groups include two supply rails, unused contacts, unloaded outputs and 1,906 non-supply groups. This count differs from CA1's projected functional graph because LL1 retains connector pins.

The fitted contact count includes the three unpopulated peripheral-slot connectors and the two-pin terminal header. Their present stubs and contacts are counted; future peripheral input loads remain unspecified. CA1's 58 excluded logical boundary markers are not counted as fitted hardware. External operator, supervisor and debugger electronics remain outside this candidate and require updated inventory when implemented.

All **19 SN74HCT245N DIR pins are physically tied to 5 V** in the mated graph. A-side pins 2–9 are receivers and B-side pins 11–18 are potential drivers, enabled by their individual active-low OE nets. The inventory records every DIR/OE binding. It establishes no new bus-exclusivity proof.

For each potential active driver, the direct load contains every other input, bidirectional port and potential output on that net. The driver's own characterized output capacitance is excluded. A bidirectional SRAM pin is counted once even though it can receive and drive. Other potential outputs contribute their inactive-output capacitance under the stated assumption that they are inactive. Fixed-output contention and enable timing require separate verification.

Every non-supply group lists unresolved trace/via/pad, socket, testpoint/probe and contact/mating terms. Resistor parasitics and external-endpoint terms appear where applicable. Unknown values are JSON `null`, never zero. The old 5 pF planning allowance is shown only as a comparison; it cannot cover an arbitrary number of DIN contacts.

## Manufacturer evidence and conditions

The inventory contains reviews for all **31 fitted logic, memory and oscillator part types**, with source hashes, original provenance, literal table extracts and page/line references. The archived excerpts are in `sources/`; the available original PDFs are included too. Earlier R2/BR1/TX1 evidence remains preserved.

* SN74HCT245's 10 pF Ci maximum explicitly excludes A/B data ports. Both port directions retain a **10 pF allocation** with no guaranteed maximum. DIR/OE have the separate 4.5–5.5 V Ci specification.
* SN74HCT574 and SN74HC377 have input-capacitance table ranges covering OC1. This capacitance classification does not resolve HC377 DC threshold compatibility.
* AHC/AHCT input-capacitance rows generally specify 5 V. Those values remain conditional at 5 V rather than being promoted to full 4.75–5.25 V guarantees. Rows with an unspecified capacitance supply condition are explicitly marked unresolved.
* M27C1024, M27C322, W27C512 and UM61512A capacitance tables are limited to 25 °C. Input values are 6, 10, 6 and 8 pF respectively; output/I/O values are 12, 12, 12 and 10 pF. The full 0–50 °C maxima remain unknown.
* SN74AHCT244's output-capacitance row is 3 pF typical only. The inventory retains the old 10 pF inactive-output allocation. The CD74HCT244 source places a 20 pF output-capacitance row under **HC**, not HCT; LL1 does not transfer that maximum to the fitted HCT part.
* W27C512's high-speed read fixture is 30 pF with 5 ns input edges. The historical load audit fell back to 50 pF; LL1 records that historical default separately and screens the high-speed fixture at 30 pF.

The review separates recommended input transition limits from timing-test waveform conditions. Where the selected source excerpt lacks the latter, it records the gap. A source's 3 ns or 6 ns input test waveform is not evidence that a preceding fitted driver produces that edge under the complete load. No new delay, hold or release bounds are derived here.

## Replay and fault evidence

The matrix compares 1,089 R2 load rows, 179 BR1 rows and 150 TX1 rows using physical pins as anchors. Additional-pin lists include newly connected drivers as well as receivers; a new upstream driver does not add its own capacitance to its active-drive scenario.

Five mutations are rejected: a dropped receiver, a dropped mating contact, an omitted resistor, an unjustified HCT245 port maximum and a shared-global-label bypass between CPU domains. Eight focused tests also check duplicate-pin rejection, bidirectional-port accounting, each MAR tap, oscillator headroom and the evidence lock.

Source collection attempts are preserved. The first stopped on a dictionary-shaped manifest, the second on an unavailable `pdftotext` executable, and the third snapshot included an AC175 excerpt before the exact ACT175 source was selected. The final snapshot uses the exact ACT175 source. Inventory iteration 1 predates TX1 comparison and mutation reporting; iteration 2 preserves the intermediate TX1 comparison and W27C512 historical-default screen. The final evidence corrects those comparisons and uses the 30 pF high-speed W27C512 fixture.

Restore CA1 and its dependencies from `Backup/README.md`, then restore `build/cp1-link-loads/`. Reproduce into a new directory:

```sh
PYTHONPATH=Verification python3 -m dm02.link_loads \
  --output Verification/build/link-loads-new
```

`link-loads-evidence.json` pins the source, manufacturer excerpts, prior-study inputs, inventory and mutation receipts. Bounded replay regenerates the inventory and checks equality. Physical electrical closure stays in Beads under `dm02-57n.3.2`; CP1-R2 remains the accepted digital circuit.
