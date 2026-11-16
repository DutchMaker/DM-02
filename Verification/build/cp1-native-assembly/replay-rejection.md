# Preserved NA1 replay rejection

The first `python3 Verification/build/cp1-native-assembly/lock_evidence.py`
attempt failed before writing an evidence lock:

```text
ValueError: NA1 saved comparison differs
```

The then-current mutation comparator returned tuples inside pin lists and
iterated an unordered set of differing nets. Saved JSON contained arrays, so
the replay's direct comparison rejected the regenerated mutation result.

That complete study was retained as `iteration-3/`. The final comparator sorts
the differing groups and emits lists for physical-pin pairs. The final native
hierarchy was regenerated and exported. Its schematic bytes are identical to
iteration 3; the unchanged canonical export and SVG renders were reused after
that byte comparison. No earlier native exports or comparison records were
overwritten.
