import json
import asyncio
from crawl4ai import (
    AsyncWebCrawler,
    JsonCssExtractionStrategy,
    CrawlerRunConfig,
    BrowserConfig
)

async def test_one_character():
    with open("data_extraction/test.json", "r") as f:
        schema = json.load(f)

    strategy = JsonCssExtractionStrategy(schema)

    config = CrawlerRunConfig(
        extraction_strategy=strategy,
        cache_mode="bypass"
    )

    browser = BrowserConfig(headless=True)

    async with AsyncWebCrawler(config=browser) as crawler:
        result = await crawler.arun("https://onepiece.fandom.com/wiki/Monkey_D._Luffy", config=config)

        if result.success:
            print(json.dumps(json.loads(result.extracted_content), indent=2))
        else:
            print("Extraction failed.")

if __name__ == "__main__":
    asyncio.run(test_one_character())

