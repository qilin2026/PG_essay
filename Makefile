.PHONY: install scrape classify translate build all clean status

# Install dependencies
install:
	pip install -r requirements.txt

# Step 1: Scrape essay index and content from paulgraham.com
scrape:
	python scripts/scrape.py

# Scrape index only (no individual essays)
scrape-index:
	python scripts/scrape.py --index-only

# Scrape limited number of essays (for testing)
scrape-test:
	python scripts/scrape.py --limit 10

# Step 2: Classify essays (filter out technical ones)
classify:
	python scripts/classify.py

# Step 3: Translate essays to Chinese
translate:
	python scripts/translate.py

# Translate limited number (for testing)
translate-test:
	python scripts/translate.py --limit 5

# Step 4: Generate static HTML site
build:
	python scripts/generate.py

# Run full pipeline
all: scrape classify translate build

# Show translation progress
status:
	python scripts/translate.py --status

# Show classification stats
classify-stats:
	python scripts/classify.py --stats

# Clean generated site
clean:
	rm -rf site/*

# Clean all data (careful!)
clean-all:
	rm -rf site/* data/essays/*.json data/essays.json data/classifications.json
