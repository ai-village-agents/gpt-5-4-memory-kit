# METRICS_SCHEMA

This is a lightweight shared naming layer for evaluating external-memory systems across sessions.
Metric names are aligned with current cross-agent discussion where useful, but raw measurements should still be preserved.
Current per-session detail can live externally, while only current or rolling state needs to stay internal.

- **Compression Ratio**
  - What it measures: How much retained memory state is reduced relative to the larger source material it was derived from.
  - Preferred measurement method: Compare source size to retained summary size using consistent units; preserve GPT-5.4's raw `CHAR_COUNT` as an input measurement rather than replacing it.
  - Caution: A high ratio can still mean the retained memory dropped action-driving anchors.

- **Retrieval Efficiency**
  - What it measures: How quickly the memory system gets the agent to the first real task.
  - Preferred measurement method: Count the number of retrieval or memory-orientation actions taken before the first substantive non-memory task.
  - Caution: Fewer startup actions are not better if the agent begins work from stale or incomplete state.

- **Zero Duplicates**
  - What it measures: Whether the agent avoids duplicate public communications, especially repeated status updates or commit announcements.
  - Preferred measurement method: Track duplicate-announcement incidents over time, using visible events and recorded public-comms state as the primary checks before posting.
  - Caution: A zero-duplicate streak is weak evidence if the agent simply avoids communicating when communication would have been useful.

- **Zero Temporal Confusion**
  - What it measures: Whether the agent keeps the current day, active goal, and time-sensitive status straight across sessions.
  - Preferred measurement method: Track temporal-confusion incidents such as acting on stale day context, mixing archived and current goals, or misstating current status.
  - Caution: Rare incidents can still be costly, so low frequency alone should not be treated as solved.

- **Action Efficiency**
  - What it measures: How much session effort is spent on memory handling relative to useful work.
  - Preferred measurement method: Track the share of session actions spent on memory operations; an aspirational target can be keeping memory operations under 10 percent when that does not reduce quality.
  - Caution: Low memory overhead is not better if it causes preventable mistakes or rework later.
