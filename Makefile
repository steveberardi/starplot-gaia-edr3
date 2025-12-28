PYTHONPATH=./src/
PYTHON=./venv/bin/python

REPO_NAME=starplot-gaia-edr3

VERSION=$(shell ./venv/bin/python -c 'from build import __version__; print(__version__)')
VERSION_CHECK=$(shell gh release list \
		-R steveberardi/$(REPO_NAME) \
		--limit 1000 \
		--json tagName \
		--jq '.[] | select(.tagName == "v$(VERSION)")' | wc -c)

# Development ------------------------------------------
install: venv/bin/activate

format: venv/bin/activate
	@$(PYTHON) -m ruff format *.py $(ARGS)
	@$(PYTHON) -m ruff check *.py --fix $(ARGS)

venv/bin/activate: requirements.txt
	python -m venv venv
	./venv/bin/pip install -r requirements.txt

shell: venv/bin/activate
	$(PYTHON)

clean:
	rm -rf __pycache__
	rm -rf venv
	rm -rf build

build: venv/bin/activate
	rm -rf build
	rm build.log
	@mkdir -p build
	$(PYTHON) build.py

chunk: venv/bin/activate
	$(PYTHON) build.py

m13: venv/bin/activate
	$(PYTHON) m13.py

profile:
# 	$(PYTHON) -m cProfile -o results.prof m13.py
	$(PYTHON) -m snakeviz -s -p 8080 -H 0.0.0.0 results.prof

# Releases ------------------------------------------
release-check:
	@CHECK="$(VERSION_CHECK)";  \
	if [ $$CHECK -eq 0 ] ; then \
		echo "version check passed!"; \
	else \
		echo "version tag already exists"; \
		false; \
	fi

release: release-check
	gh release create \
		v$(VERSION) \
		build/constellations.$(VERSION).parquet \
		--title "v$(VERSION)" \
		-R steveberardi/$(REPO_NAME)

version: venv/bin/activate
	@echo $(VERSION)


.PHONY: clean test release release-check build
