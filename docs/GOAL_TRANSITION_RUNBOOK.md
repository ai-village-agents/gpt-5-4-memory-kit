# Goal Transition Runbook (GPT-5.4)

Use this runbook when Shoshannah/admin announces a new goal or room assignment.

## Protocol

1. Treat visible current event text as source-of-truth. If it conflicts with older memory or search-history, trust the visible event text.
2. If timing or day context seems odd, use `search_history` to cross-check the canonical transcript before drawing conclusions from session-visible timestamps alone.
3. Capture exact transition facts before editing anything: new goal text, day number/date, and room assignment.
4. Update `data/active_frontier.json` only where needed: adjust `focus` and immediate `tasks` to align with the new goal.
5. Re-check prior active tasks and move stale items to `settled_facts` or `open_loops` when appropriate instead of leaving them active.
6. If the room changed, update room anchors consistently across memory artifacts so references match the new location.
7. Before any public update, inspect visible events for an existing GPT-5.4 `AGENT_TALK`, then run `python3 tools/pre_send_chat.py ...` (it blocks if the topic already exists in active or archived public comms).
8. After any meaningful public update, run `python3 tools/log_public_comm.py ...`, and before session end after a transition run both `python3 tools/pre_consolidate.py ...` and `python3 tools/render_lean_memory.py`.

## Transition Checklist (Commands)

```bash
python3 tools/start_session.py
python3 tools/pre_send_chat.py --purpose '...' --recipient '...' --topic '...' --duplicate-check '...'
python3 tools/log_public_comm.py --state announced --topic '...' --message-summary '...' --audience '...' --date-day ...
python3 tools/pre_consolidate.py --next-session-goal '...' --next-short-goal '...'
python3 tools/render_lean_memory.py
```
