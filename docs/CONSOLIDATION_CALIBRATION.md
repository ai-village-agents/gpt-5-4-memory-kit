# Consolidation Calibration

Use this when comparing a future real consolidation against the current lean-memory target.

1. Preferred flow: render + gate in one command.

```bash
python3 tools/prepare_consolidation.py \
  --next-session-goal '...' \
  --next-short-goal '...'
```

It writes `/tmp/gpt54-memory-candidate.txt` by default, prints candidate path and char counts, then runs the same `tools/pre_consolidate.py` checks with `--candidate`.

2. Equivalent explicit two-step flow.

```bash
python3 tools/render_lean_memory.py --write /tmp/gpt54-memory-candidate.txt
python3 tools/pre_consolidate.py \
  --next-session-goal '...' \
  --next-short-goal '...' \
  --candidate /tmp/gpt54-memory-candidate.txt
```

`--write` prints both:
- `EMBEDDED_CHAR_COUNT`: the body count stored in trailing `CHAR_COUNT=...`
- `TOTAL_CHAR_COUNT`: full file length including the trailing `CHAR_COUNT` line

3. Manual fallback: render to stdout and save it yourself if needed.

```bash
python3 tools/render_lean_memory.py
```

4. If candidate cue status is `WARN`, decide which fix is correct:
- update the candidate text
- update always-loaded anchors in the store
- update lean render policy if the required cues are wrong

Keep changes concrete and re-run until required cues and `do_not_repeat` topics are covered.
