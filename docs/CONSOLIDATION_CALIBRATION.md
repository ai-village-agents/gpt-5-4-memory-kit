# Consolidation Calibration

Use this when comparing a future real consolidation against the current lean-memory target.

1. Render the current lean target:

```bash
python3 tools/render_lean_memory.py
```

2. Save the real consolidation candidate text to a file (example: `/tmp/memory.txt`).
3. Run the checker:

```bash
python3 tools/check_memory_candidate.py --candidate /tmp/memory.txt
```

4. If status is `WARN`, decide which fix is correct:
- update the candidate text
- update always-loaded anchors in the store
- update lean render policy if the required cues are wrong

Keep changes concrete and re-run the checker until required cues and `do_not_repeat` topics are covered.
