import asyncio
import json
from typing import Set, List
from urllib.parse import urljoin, urlparse
from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import os
from threading import Lock


class PDFCollector:
    def __init__(self, base_url: str, max_depth: int = 1, output_dir: str = "results"):
        self.base_url = base_url
        self.max_depth = max_depth
        self.output_dir = output_dir
        self.visited: Set[str] = set()
        self.pdf_links: Set[str] = set()
        self.session_id = f"session_{urlparse(base_url).netloc.replace('.', '_')}"
        self.max_retries = 3
        self.retry_delay = 5
        self.file_lock = Lock()

        os.makedirs(self.output_dir, exist_ok=True)
        self._initialize_json_file()

    def _get_output_filename(self):
        domain = urlparse(self.base_url).netloc
        return os.path.join(self.output_dir, f"{domain}.json")

    def _initialize_json_file(self):
        output_file = self._get_output_filename()
        if not os.path.exists(output_file):
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _save_pdf_link(self, pdf_url: str):
        output_file = self._get_output_filename()
        with self.file_lock:
            try:
                with open(output_file, "r", encoding="utf-8") as f:
                    links = json.load(f)

                if pdf_url not in links:
                    links.append(pdf_url)
                    with open(output_file, "w", encoding="utf-8") as f:
                        json.dump(links, f, indent=2)
                    print(f"Saved new PDF link to {output_file}: {pdf_url}")
            except Exception as e:
                print(f"Error saving PDF link to file: {str(e)}")

    async def collect_pdfs(
        self, crawler: AsyncWebCrawler, crawl_config: CrawlerRunConfig
    ):
        try:
            await self._crawl_parallel(
                crawler, [self.base_url], current_depth=0, crawl_config=crawl_config
            )
            print(
                f"Completed crawling {self.base_url}. Total PDFs found: {len(self.pdf_links)}"
            )
        except Exception as e:
            print(f"Error collecting PDFs from {self.base_url}: {str(e)}")

    async def _crawl_parallel(
        self,
        crawler: AsyncWebCrawler,
        urls: List[str],
        current_depth: int,
        crawl_config: CrawlerRunConfig,
        max_concurrent: int = 2,
    ):
        if current_depth > self.max_depth:
            return

        batch_size = 3
        for i in range(0, len(urls), batch_size):
            batch_urls = urls[i : i + batch_size]
            semaphore = asyncio.Semaphore(max_concurrent)

            async def sem_task(url):
                async with semaphore:
                    if url not in self.visited:
                        self.visited.add(url)
                        print(f"Crawling: {url} (Depth: {current_depth})")
                        await self._crawl_single_with_retry(
                            crawler, url, current_depth, crawl_config, self.session_id
                        )

            tasks = [sem_task(url) for url in batch_urls]
            await asyncio.gather(*tasks)

    async def _crawl_single_with_retry(
        self,
        crawler: AsyncWebCrawler,
        url: str,
        current_depth: int,
        crawl_config: CrawlerRunConfig,
        session_id: str,
    ):
        for attempt in range(self.max_retries):
            try:
                await self._crawl_single(
                    crawler, url, current_depth, crawl_config, session_id
                )
                break
            except Exception as e:
                if attempt == self.max_retries - 1:
                    print(
                        f"Failed to crawl {url} after {self.max_retries} attempts: {str(e)}"
                    )
                else:
                    print(
                        f"Attempt {attempt + 1} failed for {url}. Retrying in {self.retry_delay} seconds..."
                    )
                    await asyncio.sleep(self.retry_delay)
                    crawl_config = CrawlerRunConfig(
                        cache_mode=CacheMode.BYPASS,
                        wait_for_images=False,
                        delay_before_return_html=0.1,
                    )

    async def _crawl_single(
        self,
        crawler: AsyncWebCrawler,
        url: str,
        current_depth: int,
        crawl_config: CrawlerRunConfig,
        session_id: str,
    ):
        # Skip non-webpage files
        skip_extensions = [
            ".zip",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".ppt",
            ".pptx",
            ".rar",
            ".7z",
        ]
        if any(url.lower().endswith(ext) for ext in skip_extensions):
            print(f"Skipping non-webpage file: {url}")
            return

        try:
            result = await crawler.arun(
                url=url, config=crawl_config, session_id=session_id
            )
            if result.success:
                all_links = result.links.get("internal", []) + result.links.get(
                    "external", []
                )
                next_urls = []

                for link in all_links:
                    href = link.get("href")
                    if not href:
                        continue

                    if any(
                        pattern in href.lower()
                        for pattern in [
                            "menu",
                            "nav",
                            "header",
                            "footer",
                            "about",
                            "contact",
                            "privacy",
                            "terms",
                            "sitemap",
                            "search",
                            "login",
                            "register",
                        ]
                    ) or any(href.lower().endswith(ext) for ext in skip_extensions):
                        continue

                    full_url = urljoin(self.base_url, href)
                    parsed_url = urlparse(full_url)

                    if parsed_url.netloc != urlparse(self.base_url).netloc:
                        continue

                    if full_url.lower().endswith(".pdf"):
                        self.pdf_links.add(full_url)
                        self._save_pdf_link(full_url)
                        print(f"Found PDF: {full_url}")
                    elif full_url not in self.visited:
                        next_urls.append(full_url)

                if next_urls:
                    await self._crawl_parallel(
                        crawler, next_urls, current_depth + 1, crawl_config
                    )
            else:
                if "ERR_ABORTED" in str(result.error_message):
                    print(f"Skipping non-webpage URL: {url}")
                else:
                    raise Exception(result.error_message)
        except Exception as e:
            if "ERR_ABORTED" in str(e):
                print(f"Skipping non-webpage URL: {url}")
            else:
                raise Exception(f"Error crawling {url}: {str(e)}")


async def main():
    with open("links.txt", "r") as file:
        urls = [line.strip() for line in file if line.strip()]

    browser_config = BrowserConfig(
        headless=True,
        accept_downloads=False,
        light_mode=True,
        extra_args=[
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-extensions",
            "--disable-notifications",
            "--disable-popup-blocking",
        ],
    )

    batch_size = 10
    for i in range(0, len(urls), batch_size):
        batch_urls = urls[i : i + batch_size]
        print(
            f"\nProcessing batch {i//batch_size + 1} of {(len(urls) + batch_size - 1)//batch_size}"
        )

        crawl_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            wait_for_images=False,
            delay_before_return_html=0.1,
        )

        collectors = [
            PDFCollector(url, max_depth=1, output_dir="results") for url in batch_urls
        ]

        async with AsyncWebCrawler(config=browser_config) as crawler:
            semaphore = asyncio.Semaphore(5)

            async def process_site(collector):
                async with semaphore:
                    await collector.collect_pdfs(crawler, crawl_config)

            tasks = [process_site(collector) for collector in collectors]
            await asyncio.gather(*tasks)

        if i + batch_size < len(urls):
            print("Waiting between batches to avoid overload...")
            await asyncio.sleep(5)

    print("\nAll websites have been processed!")


if __name__ == "__main__":
    asyncio.run(main())
