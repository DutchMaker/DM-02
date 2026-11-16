# CP1-OC1: first-build operating contract

Selected 16 November 2026 under Beads `dm02-57n.1.1`. Machine-readable authority: [`operating-contract.json`](operating-contract.json). Hardware/digital baseline: **CP1-R2**.

## Selected rate and envelope

Use **ACH-4.000MHZ-EK at 4 MHz**, divided into **500 kHz microcycles** (eight oscillator periods per microcycle). Instruction throughput varies with microcycle count. The owner accepts a lower speed when the selected ICs cannot feasibly support the preferred 1 MHz microcycle rate. The [readiness study](CP1-readiness.md) supplies the selection evidence.

Voltage remains **4.75–5.25 V at every IC's supply and ground pins**, including ripple, droop and distribution drop. Ambient remains **0–50 °C**. These are requirements, not measured operating capability. Exact owned-part identity, loading and full-envelope qualification remain open.

At ±30 ppm, the oscillator interval is 3,999,880–4,000,120 Hz and the corresponding microcycle interval is 499,985–500,015 Hz. The nominal microcycle is 2,000 ns. This tolerance follows the selected oscillator specification; actual startup, waveform and receiver-threshold timing must also qualify.

The existing conditional timing allocations give at least 717.478 ns phase separation and 967.470 ns pulse width at the fastest oscillator, before downstream distribution and receiver constraints. These numbers use 32.5 ns output spread and are not measured guarantees. All new setup budgets must retain **at least 10 ns reserve after worst-case delay and uncertainty**. Hold, release, recovery/removal and pulse checks need positive residual margin after uncertainty. The 10 ns setup reserve is a new engineering acceptance criterion, not a claimed property of every R2 path.

The study's same-word MAR→ROM control-branch margin is about 153 ns at the selected rate, versus 3 ns at 625 kHz. The opposite-edge clock screen has about 40 ns at 4 MHz. These selected-path results justify the target while leaving complete min/max closure in `dm02-57n.3.9`.

## Startup, reset and clock modes

Keep reset asserted for at least **25 ms after continuously valid supply**. The oscillator's 10 ms startup limit must have elapsed and its waveform must meet the qualified limits before release. Any loss of supply validity restarts the guard. The reset request must be at least **1,000 ns**. READY indicates internal initialization, not power-good.

An externally qualified reset remains the boundary until the supervisor and write-inhibit design passes `dm02-57n.3.5`. The owned MCP100-450D alone cannot establish the 4.75 V minimum. Its eventual replacement or accompanying circuitry must provide enough threshold and propagation headroom to inhibit writes before any IC falls below valid supply.

The oscillator runs during reset to initialize resetless registers. One documented initial invalid microcycle is permitted; the first valid microcycle must fetch the address. Reset abort can truncate a cycle, but no partial operation may be reported as completed. RAM contents after an interrupted write are unspecified; restart diagnostics must initialize what they use.

Allowed modes are continuous execution, HALT/RESUME, debounced single-step and asynchronous reset abort. A valid stop request must finish an already accepted cycle and reach safe idle within **four nominal microcycles (8 μs)**. This is a design/bench acceptance limit, not a new measured result. PH2 and PH3 must be low in idle and writes inhibited. HALT remains latched until explicit RESUME.

One debounced STEP edge while READY and idle requests exactly one complete microcycle. Holding STEP must not repeat; STEP during ACTIVE is ignored. Raw switch bounce is outside this boundary and needs separate qualification. Oscillator replacement or frequency changes require power removal, a versioned contract and affected verification. A slower fallback is not silently accepted under CP1-OC1.

## Qualification matrix and evidence

The active runner generates `build/cp1/qualification-matrix.json` directly from the contract:

- Six physical test groups at nine supply/ambient combinations: 4.75, 5.0 and 5.25 V × 0, 25 and 50 °C, for **54 specified rows**.
- Ten digital delay selections × three receiver-duty sensitivities × three oscillator offsets, for **90 requested digital profiles**. Existing R2 suites retain their actual archived coverage. This requested matrix does not assert that all combinations have run.
- Each row carries the contract/design revision, oscillator and microcycle rates, stimulus and pass criteria. Physical rows start `not-run`; digital rows start `coverage-request-only`.

The six physical groups cover supply/startup, clock modes, data timing, bus release, SRAM turnaround and repeated functional execution. Every measurement record needs exact board/part/lot identity, instrument calibration, actual pin supply and ambient, probe/fixture load, stimulus, raw waveforms, uncertainty, observed margin and pass/fail.

The contract defines the operating envelope and behavioural limits. The first-machine IO choice (`dm02-57n.1.3`), equipment availability (`.8.1`), detailed repetitions and test-program selection (`.8.7`) remain with their owning tasks. They must be resolved before physical acceptance. A successful digital test cannot fill a physical matrix row.

## Requirements versioning and replay

CP1-OC1 is an operating-contract revision, not a new circuit revision. `Verification/requirements.json` remains the hashed historical `prototype-baseline-1` input for the reference pilot and R2 replay. The active CP1 report composes that unchanged requirement/gate map with CP1-OC1's selected envelope and records both revisions. The frozen pilot's 1,000 ns stimulus period is labelled historical; it is not the selected machine microcycle period.

The active report validates the contract against the pinned R2 oscillator configuration and the readiness-study hashes. Missing, changed or inconsistent evidence fails the run and withholds control acceptance. Source freshness covers the contract, loader and dashboard; the post-test artifact check also covers the decision evidence.

Restore the R2, preserved reference and **cp1-readiness-2026-11-16** release assets as described in `Backup/README.md`, then run:

```sh
python3 Verification/run.py --allow-design-failures
```

The contract check can pass while timing, physical clock, module integration, PCB and bench gates remain open. Expected formal milestone totals remain **3/5, 3/5 and 8/9**. Fabrication readiness is `dm02-57n.7.5`; measured working-machine acceptance is `.8.8`.
