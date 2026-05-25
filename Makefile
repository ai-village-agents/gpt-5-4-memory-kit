PYTHON ?= python3
CANDIDATE_PATH ?= /tmp/gpt54-memory-candidate.txt

.PHONY: test brief audit start session-start render-candidate prepare-consolidation finalize-public-comm

test:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v

brief:
	$(PYTHON) tools/build_session_brief.py

audit:
	$(PYTHON) tools/audit_memory_store.py

start:
	python3 tools/start_session.py

session-start: start

render-candidate:
	$(PYTHON) tools/render_lean_memory.py --write $(CANDIDATE_PATH)

prepare-consolidation:
	@if [ -z "$(NEXT_SESSION_GOAL)" ]; then \
		echo "Missing NEXT_SESSION_GOAL."; \
		echo "Usage: make prepare-consolidation NEXT_SESSION_GOAL='...' NEXT_SHORT_GOAL='...'"; \
		exit 2; \
	fi
	@if [ -z "$(NEXT_SHORT_GOAL)" ]; then \
		echo "Missing NEXT_SHORT_GOAL."; \
		echo "Usage: make prepare-consolidation NEXT_SESSION_GOAL='...' NEXT_SHORT_GOAL='...'"; \
		exit 2; \
	fi
	$(PYTHON) tools/prepare_consolidation.py \
		--next-session-goal "$(NEXT_SESSION_GOAL)" \
		--next-short-goal "$(NEXT_SHORT_GOAL)"

finalize-public-comm:
	@if [ -z "$(STATE)" ]; then \
		echo "Missing STATE."; \
		echo "Usage: make finalize-public-comm STATE='announced|do_not_repeat' TOPIC='...' MESSAGE_SUMMARY='...' AUDIENCE='...' DATE_DAY='420'"; \
		exit 2; \
	fi
	@if [ -z "$(TOPIC)" ]; then \
		echo "Missing TOPIC."; \
		echo "Usage: make finalize-public-comm STATE='announced|do_not_repeat' TOPIC='...' MESSAGE_SUMMARY='...' AUDIENCE='...' DATE_DAY='420'"; \
		exit 2; \
	fi
	@if [ -z "$(MESSAGE_SUMMARY)" ]; then \
		echo "Missing MESSAGE_SUMMARY."; \
		echo "Usage: make finalize-public-comm STATE='announced|do_not_repeat' TOPIC='...' MESSAGE_SUMMARY='...' AUDIENCE='...' DATE_DAY='420'"; \
		exit 2; \
	fi
	@if [ -z "$(AUDIENCE)" ]; then \
		echo "Missing AUDIENCE."; \
		echo "Usage: make finalize-public-comm STATE='announced|do_not_repeat' TOPIC='...' MESSAGE_SUMMARY='...' AUDIENCE='...' DATE_DAY='420'"; \
		exit 2; \
	fi
	@if [ -z "$(DATE_DAY)" ]; then \
		echo "Missing DATE_DAY."; \
		echo "Usage: make finalize-public-comm STATE='announced|do_not_repeat' TOPIC='...' MESSAGE_SUMMARY='...' AUDIENCE='...' DATE_DAY='420'"; \
		exit 2; \
	fi
	$(PYTHON) tools/finalize_public_comm.py \
		--state "$(STATE)" \
		--topic "$(TOPIC)" \
		--message-summary "$(MESSAGE_SUMMARY)" \
		--audience "$(AUDIENCE)" \
		--date-day "$(DATE_DAY)"
