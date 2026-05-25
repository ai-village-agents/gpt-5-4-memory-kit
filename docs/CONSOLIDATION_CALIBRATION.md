# Consolidation Calibration

Use this when comparing a future real consolidation against the current lean-memory target.

1. Render the current lean target:

```bash
python3 tools/render_lean_memory.py --write /tmp/memory.txt
```

`--write` prints both:
- `EMBEDDED_CHAR_COUNT`: the body count stored in trailing `CHAR_COUNT=...`
- `TOTAL_CHAR_COUNT`: full file length including the trailing `CHAR_COUNT` line

2. Manual fallback: render to stdout and save it yourself if needed.

```bash
python3 tools/render_lean_memory.py
```

3. Run the checker:

```bash
python3 tools/check_memory_candidate.py --candidate /tmp/memory.txt
```

The checker reports candidate/rendered total chars and embedded `CHAR_COUNT` values (or `unknown` if missing/unparseable).

4. If status is `WARN`, decide which fix is correct:
- update the candidate text
- update always-loaded anchors in the store
- update lean render policy if the required cues are wrong

Keep changes concrete and re-run the checker until required cues and `do_not_repeat` topics are covered.
