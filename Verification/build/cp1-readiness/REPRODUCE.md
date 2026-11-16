# Reproduce the readiness experiments

Restore the CP1-R2 release using `Backup/README.md` first. Python 3 and Icarus Verilog are required. Publication additionally uses Pandoc and Playwright with Chrome.

The scripts refuse to overwrite experiment directories. Run a replay in a new sibling directory, preserving the published evidence:

```sh
mkdir Verification/build/cp1-readiness-replay
cp -f Verification/build/cp1-readiness/{frequency_sweep,timing_screen,trace_transfer,verify_study}.py Verification/build/cp1-readiness-replay/
python3 Verification/build/cp1-readiness-replay/frequency_sweep.py
python3 Verification/build/cp1-readiness-replay/frequency_sweep.py --matrix capture
python3 Verification/build/cp1-readiness-replay/frequency_sweep.py --mhz 5 --corner 1 --duty .37 --cases --observation capture
python3 Verification/build/cp1-readiness-replay/trace_transfer.py
python3 Verification/build/cp1-readiness-replay/timing_screen.py
python3 Verification/build/cp1-readiness-replay/verify_study.py
```

The first matrix has 37 profiles, the capture matrix 28, and the all-opcode run one. Three trace replays explain the same-word MAR transfer. Seven selected paths at five frequencies produce 35 analytical rows. Expected high-frequency design failures are retained and do not make the integrity audit fail. A timeout, missing completion marker or compile error is not accepted as a design-failure result.

`verify_study.py` verifies source/output hashes, matrix completeness, every original fatal assertion verbatim, completion markers and analytical sums. Neither the frequency runner nor the integrity audit is a physical-acceptance gate.

`publish.py` publishes the canonical study directory at its fixed Tailscale URL. Its manifest excludes the subsequently generated browser screenshots/receipt and remote-validation receipt. The release backup manifest covers those files too. The preserved `failed-runs/documentation-drift/` records a separate normal replay rejected because `Verification/CP1.md` changed during that run; all 164 harness tests passed in that rejected replay.
