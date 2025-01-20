# Search and Crawl

This project is a simple implementation of a search and crawl tool using the `crawl4ai` library. It allows you to search for a specific keyword on a website and then crawl the website to collect all the PDF links.

### Setting up the environment

```bash
uv venv
source .venv/bin/activate
```

### Installing the dependencies

```bash
uv pip install "crawl4ai @ git+https://github.com/unclecode/crawl4ai.git" transformers torch nltk
uv pip install -r requirements.txt

# Installing Playwright
playwright install
```

### Running the crawler

```bash
uv python search.py
uv python crawler.py
```
