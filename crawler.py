import asyncio
import json
from typing import Set, List
from urllib.parse import urljoin, urlparse
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig


class PDFCollector:
    def __init__(
        self, base_url: str, max_depth: int = 1, output_file: str = "pdf_links.json"
    ):
        self.base_url = base_url
        self.max_depth = max_depth
        self.output_file = output_file
        self.visited: Set[str] = set()
        self.pdf_links: Set[str] = set()
        self.session_id = "pdf_collection_session"

    async def collect_pdfs(self):
        browser_config = BrowserConfig(
            headless=True,
            accept_downloads=False,
            extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
        )
        crawl_config = CrawlerRunConfig()

        async with AsyncWebCrawler(config=browser_config) as crawler:
            await self._crawl_parallel(
                crawler, [self.base_url], current_depth=0, crawl_config=crawl_config
            )

        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(list(self.pdf_links), f, indent=1)

        print(
            f"Collected {len(self.pdf_links)} PDF links. Saved to '{self.output_file}'."
        )

    async def _crawl_parallel(
        self,
        crawler: AsyncWebCrawler,
        urls: List[str],
        current_depth: int,
        crawl_config: CrawlerRunConfig,
        max_concurrent: int = 1,
    ):
        if current_depth > self.max_depth:
            return

        semaphore = asyncio.Semaphore(max_concurrent)

        async def sem_task(url):
            async with semaphore:
                if url not in self.visited:
                    self.visited.add(url)
                    print(f"Crawling: {url} (Depth: {current_depth})")
                    session_id = f"{self.session_id}_{current_depth}"
                    await self._crawl_single(
                        crawler, url, current_depth, crawl_config, session_id
                    )

        tasks = [sem_task(url) for url in urls]
        await asyncio.gather(*tasks)

    async def _crawl_single(
        self,
        crawler: AsyncWebCrawler,
        url: str,
        current_depth: int,
        crawl_config: CrawlerRunConfig,
        session_id: str,
    ):
        try:
            result = await crawler.arun(
                url=url, config=crawl_config, session_id=session_id
            )
            if result.success:
                links = result.links.get("internal", []) + result.links.get(
                    "external", []
                )
                for link in links:
                    href = link.get("href")
                    if not href:
                        continue
                    full_url = urljoin(self.base_url, href)
                    parsed_url = urlparse(full_url)

                    if parsed_url.netloc != urlparse(self.base_url).netloc:
                        continue

                    if full_url.lower().endswith(".pdf"):
                        self.pdf_links.add(full_url)
                        print(f"Found PDF: {full_url}")
                    elif full_url not in self.visited:
                        await self._crawl_parallel(
                            crawler, [full_url], current_depth + 1, crawl_config
                        )
            else:
                print(f"Failed to crawl {url}: {result.error_message}")
        except Exception as e:
            print(f"Error crawling {url}: {str(e)}")


async def main():
    with open("link.txt", "r") as file:
        base_url = file.readline().strip()

    collector = PDFCollector(
        base_url=base_url, max_depth=1, output_file="pdf_links.json"
    )
    await collector.collect_pdfs()


if __name__ == "__main__":
    asyncio.run(main())
