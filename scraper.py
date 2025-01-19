import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode


async def main():
    browser_config = BrowserConfig()
    run_config = CrawlerRunConfig()

    # Load URLs from links.txt
    with open("links.txt", "r", encoding="utf-8") as file:
        urls = [line.strip() for line in file if line.strip()]

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for url in urls:
            result = await crawler.arun(
                url=url,
                config=run_config,
            )
            with open("result.txt", "a", encoding="utf-8") as f:
                f.write(f"### {url}\n")
                f.write(result.markdown + "\n\n")


if __name__ == "__main__":
    asyncio.run(main())
