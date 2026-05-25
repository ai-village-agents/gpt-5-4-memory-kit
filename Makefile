PYTHON ?= python3

test:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v

brief:
	$(PYTHON) tools/build_session_brief.py

audit:
	$(PYTHON) tools/audit_memory_store.py

start:
	python3 tools/start_session.py
