.PHONY: install extract classify build all clean

# Install dependencies
install:
	pip install -r requirements.txt

# Step 1: Extract essays from EPUB archive
extract:
	python scripts/extract_epub.py

# Step 2: Classify essays (filter out technical ones)
classify:
	python scripts/classify.py

# Step 3: Generate static HTML site
build:
	python scripts/generate.py

# Run full pipeline (extract + classify + build)
all: extract classify build

# Show classification stats
classify-stats:
	python scripts/classify.py --stats

# Clean generated site
clean:
	rm -rf docs/*.html

# Clean all data (careful!)
clean-all:
	rm -rf docs/*.html data/essays/*.json data/essays.json data/classifications.json
