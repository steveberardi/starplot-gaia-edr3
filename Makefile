PYTHONPATH=./src/
PYTHON=./venv/bin/python

REPO_NAME=starplot-gaia-edr3

VERSION=$(shell ./venv/bin/python -c 'from build import __version__; print(__version__)')
VERSION_CHECK=$(shell gh release list \
		-R steveberardi/$(REPO_NAME) \
		--limit 1000 \
		--json tagName \
		--jq '.[] | select(.tagName == "v$(VERSION)")' | wc -c)

BUILD_WORKERS=12

# Data Paths ------------------------------------------
GAIA_SOURCE_PATH=/Volumes/Blue2TB/gaia/gdr3/gaia_source/
GAIA_BUILD_PATH_BASE=/Volumes/starship500/build/

# Environment Variables ------------------------------------------
export STARPLOT_DATA_PATH=./data/

# Development ------------------------------------------
install: venv/bin/activate

format: venv/bin/activate
	@$(PYTHON) -m ruff format src/*.py $(ARGS)
	@$(PYTHON) -m ruff check src/*.py --fix $(ARGS)

venv/bin/activate: requirements.txt
	python -m venv venv
	./venv/bin/pip install -r requirements.txt

shell: venv/bin/activate
	$(PYTHON)

clean:
	rm -rf __pycache__
	rm -rf venv
	rm -f build.log

build: venv/bin/activate
	rm -rf $(BUILD_DESTINATION)
	rm -f build.log
	@mkdir -p $(BUILD_DESTINATION)
	$(PYTHON) src/build.py \
		--source $(GAIA_SOURCE_PATH) \
		--destination $(BUILD_DESTINATION) \
		--num_workers $(BUILD_WORKERS) \
		--nside $(BUILD_NSIDE) \
		--mag_min $(BUILD_MAG_MIN) \
		--mag_max $(BUILD_MAG_MAX) \
		--sample_rate $(BUILD_SAMPLE_RATE)

squash: venv/bin/activate
	$(PYTHON) src/squash.py \
		--source $(BUILD_DESTINATION) \
		--num_workers $(BUILD_WORKERS)

archive: venv/bin/activate
	rm -rf $(BUILD_DESTINATION_ARCHIVE)
	@mkdir -p $(BUILD_DESTINATION_ARCHIVE)
	$(PYTHON) src/archive.py \
		--source $(BUILD_DESTINATION) \
		--destination $(BUILD_DESTINATION_ARCHIVE)

# Mag 6-18 at 80% sampling rate
build-18: BUILD_DESTINATION=$(GAIA_BUILD_PATH_BASE)gaia-18/
build-18: BUILD_DESTINATION_ARCHIVE=$(GAIA_BUILD_PATH_BASE)gaia-18-archive/
build-18: BUILD_NSIDE=4
build-18: BUILD_MAG_MIN=6
build-18: BUILD_MAG_MAX=18
build-18: BUILD_SAMPLE_RATE=0.80
build-18: venv/bin/activate build squash archive

# Mag 6-18 at 100% sampling rate
build-18-c: BUILD_DESTINATION=$(GAIA_BUILD_PATH_BASE)gaia-18-c/
build-18-c: BUILD_DESTINATION_ARCHIVE=$(GAIA_BUILD_PATH_BASE)gaia-18-c-archive/
build-18-c: BUILD_NSIDE=4
build-18-c: BUILD_MAG_MIN=6
build-18-c: BUILD_MAG_MAX=18
build-18-c: BUILD_SAMPLE_RATE=1
build-18-c: venv/bin/activate build squash archive

# Mag 9-16 at 50% sampling rate
build-16: BUILD_DESTINATION=$(GAIA_BUILD_PATH_BASE)gaia-16/
build-16: BUILD_DESTINATION_ARCHIVE=$(GAIA_BUILD_PATH_BASE)gaia-16-archive/
build-16: BUILD_NSIDE=2
build-16: BUILD_MAG_MIN=9
build-16: BUILD_MAG_MAX=16
build-16: BUILD_SAMPLE_RATE=0.5
build-16: venv/bin/activate build squash archive

# Complete Build, but with min mag of 6
build-complete: BUILD_DESTINATION=$(GAIA_BUILD_PATH_BASE)gaia-complete/
build-complete: BUILD_NSIDE=8
build-complete: BUILD_MAG_MIN=6
build-complete: BUILD_MAG_MAX=30
build-complete: BUILD_SAMPLE_RATE=1
build-complete: venv/bin/activate build squash archive



stats: venv/bin/activate
	$(PYTHON) src/stats.py

m13: venv/bin/activate
	$(PYTHON) src/m13.py

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
