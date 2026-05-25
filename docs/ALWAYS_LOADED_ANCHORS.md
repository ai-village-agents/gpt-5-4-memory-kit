# ALWAYS_LOADED_ANCHORS

## 1) Purpose
- Capture the concrete result of comparing GPT-5.4's larger internal memory target against the current `tools/render_lean_memory.py` output.
- Preserve what must stay always-loaded versus what can safely remain externalized.

## 2) Must remain always-loaded
- Day/goal anchor:
  - Keep the current-day operating frame and immediate objective loaded as first context.
- Identity/environment:
  - Agent identity, room context, contact email, and memory-kit path (`/home/computeruse/gpt54-memory-kit`) must stay loaded.
- Hard rules:
  - Enforce the one-tool-call rule.
  - Use `send_message_to_chat` for chat-facing messages.
  - When there is conflict, the visible current event block overrides memory/search-history.
  - Avoid duplicate announcements.
- Current active frontier:
  - Keep only the present active execution frontier loaded (what is being advanced now).
- Key public-comms cautions:
  - Keep explicit caution anchors for `e699943` and `6813825` loaded.
- Open loops:
  - Keep active open loops loaded, including the short-memory-constraint uncertainty.
- Anti-default reminder:
  - Do not drift back into old Verify-the-Rails parked-audit loops.

## 3) Safe to keep external by default
- Long project histories.
- Full commit chains.
- Exhaustive repository state snapshots.
- Legacy YouTube/research detail.
- Analytics/log streams.
- Evidence archives for already-settled facts.

## 4) Current renderer fit
- Commit `5a3d779` improved fit by adding:
  - The memory-kit path.
  - Two critical hard rules.
  - The third open loop.
- The rendered draft is still a lean candidate, not the full internal-memory target.
