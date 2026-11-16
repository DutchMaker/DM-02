# HCT sourcing review and memory-buffer candidate

CP1-HP1 reviews **142 non-HCT logic packages** in MD1. Its native inventory also
contains 126 HCT packages and four memories. The review records nine exact HCT
replacement parts, their manufacturer conditions and lifecycle rows, and every
affected reference's connected input/output pins and load scenarios.

The owner prefers HCT for availability. That preference does not establish a
particular manufacturer suffix, owned quantity or distributor stock. Existing
CD74HCT parts retain their exact identities; generic SN74HCT stock is not an
automatic replacement.

## Source conditions

| Candidate | Conditional delay at 4.5 V / 50 pF | Temperature column | DIP lifecycle on retrieval |
| --- | --- | --- | --- |
| SN74HCT00N | 25 ns | −40…85 °C | NRND |
| SN74HCT04N | 25 ns | −40…85 °C | NRND |
| SN74HCT08N | 30 ns | −40…85 °C | Active |
| SN74HCT32N | 30 ns | −40…85 °C | Active |
| SN74HCT74N | clock 35 ns; async 44 ns | −40…85 °C | NRND |
| SN74HCT157N | data 35; select 40; strobe 33 ns, withheld pending source clarification | −40…85 °C | NRND |
| SN74HCT244N | data 42; enable/disable 53 ns | **−55…125 °C** | Active |
| CD74HCT175E | clock 41; reset 44 ns | −40…85 °C | Active |
| CD74HCT377E | clock 48 ns | −40…85 °C | Active |

The full PDFs, extracted text, SHA-256 hashes and retrieval times are in
`build/cp1-hct-preference/sources/`. `conditions-review.pdf` preserves the
visually inspected HCT244 waveform page and the HCT157/HCT377 tables.
Lifecycle observations describe the retrieved TI addenda, not stock availability.

SCLS175I page 8, Figure 6-1 note C specifies a 6 ns input edge, measured between
0.3 and 2.7 V, with 1.3 V propagation references. Its 500 ns recommended input
transition limit is a separate constraint. The table's 18 ns output transition
bound does not establish the downstream devices' faster timing-input fixtures.
The 42 ns value must not be replaced by CD74HCT244E's 31 ns specification.

SCLS071D pages 3–4 have PRODUCT PREVIEW watermarks in the **SN54** columns and
a generic preview footer. The SN74HCT157N addendum says NRND/Production. HP1
retains this distinction and withholds a replacement timing guarantee until
the applicable provenance is resolved or a separately reviewed CD74HCT157E
is selected. The existing six CD74HCT157E devices are a separate exact part.

## Reference-level decisions

`build/cp1-hct-preference/review.json` contains the full per-reference review:

| Decision | Packages | Reason |
| --- | ---: | --- |
| Test memory-address buffers first | 2 | Local always-enabled sixteen-bit boundary with a bounded affected test scope |
| Test HCT377 next | 6 | TTL-compatible inputs address the HC input-threshold concern; clock-Q grows from 40 to 48 ns |
| Retain pending clock/sequential review | 22 | Phase, reset, pulse and capture timing changes |
| Retain pending distribution review | 27 | Control/reset/data fanout and enable/disable timing |
| Retain pending mux review | 29 | Data/select/strobe delays and reconvergent glitches |
| Retain pending individual path review | 56 | Decode/gating delay, pulse width, setup/hold and handover |

These are sourcing/requalification decisions. Retention does not establish that
AHCT is uniquely necessary. HCT175 increases setup from the current 2 ns model
to 25 ns, hold from 2 to 5 ns and reset removal from 1 to 5 ns. HCT377 retains
5 ns enable hold and requires 3 ns data hold. Lowering the clock alone cannot
settle these minimum-delay obligations.

## CP1-HB1: two memory-address buffers

HB1 changes only MB1 **U17001/U17002** from SN74AHCT244N to **SN74HCT244N**.
The native candidate is in `Circuits/KiCad/Integrated/candidates/HB1/`.
Both active-low output-enable inputs remain grounded; each output drives the
same three ME1 address receivers. The raw MAR taps used by MQ1 are preserved.
Package count remains 272, with HCT increasing to 128 and AHCT decreasing to 115.

The pin/function review checks the non-inverting buffer pairs
2→18, 4→16, 6→14, 8→12, 17→3, 15→5, 13→7 and 11→9;
enables are pins 1/19, VCC pin 20 and GND pin 10. HB1 inherits MD1's symbol
geometry and checks the complete native pin signature and component identity.

SN74HCT244's 10 pF input maximum is specified over 4.5–5.5 V and the table's
temperature range. It replaces the inherited AHCT 10 pF planning value, so
the numerical MAR load allocation is unchanged. Other receivers, sockets,
routes and probes still need their own physical bounds. Raw MAR and buffered
address planning totals are not measured capacitances.

The affected digital suite uses 42 ns maximum, zero-delay sensitivity and two
alternating 0/42 ns profiles. It checks all 65,536 address words, a full memory
exercise and ROM-only startup through the five-byte TX1 serial transcript.
Native swapped-address, disabled-buffer and buffer-bypass mutations, dynamic
mapping faults and a swapped-address ROM boot test exercise the checks.
The recorded results and logs are in `build/cp1-hct-buffers/iteration-1/`.

Zero delay is a stress case, not a manufacturer minimum. Four sampled profiles
cannot establish every mixed-delay assignment, minimum hold or continuous
voltage/temperature operation. The existing SRAM setup and register hold
monitors remain active. Input slew, output thresholds, wiring delay, actual
capacitive load and full physical hold/release qualification remain open.

## Reproduction

Restore the earlier MD1/TB1 dependencies using `Backup/README.md`, then the
HP1/HB1 evidence. `hct-evidence.json` pins the source review, native candidate,
models, logs and input hashes. Bounded replay regenerates the review, native
comparison, load inventory and the altered ME1 HDL; it reuses the archived
long simulations. A changed timing/model/native input requires new affected
verification.

```sh
PYTHONPATH=Verification python3 -m dm02.hct_buffers --output Verification/build/cp1-hct-buffers/new-run
python3 Verification/run.py --allow-design-failures
```

The selected OC1 rate remains 500 kHz microcycles. CP1-R2 remains the accepted
digital revision. Fabrication and measured-working-machine gates require
their own evidence. Remaining engineering work is tracked in Beads under
`dm02-57n.2.2`, `.3.2`, `.3.3`, `.3.4`, `.7.2` and `.8.2`.
