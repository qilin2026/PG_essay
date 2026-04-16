.PHONY: install extract classify build all clean status

# Install dependencies
install:
	pip install -r requirements.txt

# Step 1: Extract essays from EPUB archive
extract:
	python scripts/extract_epub.py

# Step 2: Classify essays (filter out technical ones)
classify:
	python scripts/classify.py

# Step 3: Apply pre-generated translations
apply-translations:
	python scripts/apply_translations.py

# Step 4: Generate static HTML site
build:
	python scripts/generate.py

# Run full pipeline
all: extract classify apply-translations build

# Show classification stats
classify-stats:
	python scripts/classify.py --stats

# Clean generated site
clean:
	rm -rf docs/*

# Clean all data (careful!)
clean-all:
	rm -rf docs/* data/essays/*.json data/essays.json data/classifications.json
