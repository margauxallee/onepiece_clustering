import json
import asyncio
from typing import List, Dict, Any
from terminal_style import sprint
from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    BrowserConfig,
    CacheMode,
    RateLimiter,
    CrawlerMonitor,
    DisplayMode
)
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from crawl4ai.async_dispatcher import SemaphoreDispatcher
import pandas as pd

#  ----------- CREATING THE MAIN DATAFRAME WITH ALL THE ONE PIECE CHARACTERS INFOBOXES FROM ONE PIECE FANDOM WIKI -----------

#Parameters for the crawlers
schema_file_path = "data_extraction/schema.json"
with open(schema_file_path, "r", encoding="utf-8") as f:
    schema = json.load(f)

schema_infobox_file_path = "data_extraction/schema_infobox.json"
with open(schema_infobox_file_path, "r", encoding="utf-8") as f:
    schema_infobox = json.load(f)

css_extraction_1 = JsonCssExtractionStrategy(schema)
css_extraction_2 = JsonCssExtractionStrategy(schema_infobox)

config = CrawlerRunConfig(
    extraction_strategy=css_extraction_1,
    cache_mode=CacheMode.BYPASS    
)
ib_config = CrawlerRunConfig(
    extraction_strategy=css_extraction_2,
    cache_mode=CacheMode.BYPASS,
    js_code="await new Promise(resolve => setTimeout(resolve, 3000));",
    wait_for="css:aside.portable-infobox",
    semaphore_count =3,
    remove_overlay_elements=True, 
    page_timeout=60000
)

browser_config = BrowserConfig(
    headless=True,
    viewport_width=1280,
    viewport_height=800,
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
)



dispatcher = SemaphoreDispatcher(
    max_session_permit= 5,         # Maximum concurrent tasks
    rate_limiter=RateLimiter(      # Optional rate limiting
        base_delay=(0.5, 1.0),
        max_delay=10.0
    ))
# ======================== EXTRACTING CHARACTER URLS AND NAMES ==========================
# Extracted using the crawl4ai library (LLM free strategy)

async def urls_extractor(
    url: str = "https://onepiece.fandom.com/wiki/List_of_Canon_Characters"
) -> pd.DataFrame:
    """
    Asynchronously extracts character names and URLs from the One Piece Fandom wiki page.

    Args:
        url (str): URL of the Fandom page listing canon characters.
                   Defaults to the official One Piece list.

    Returns:
        pd.DataFrame: A DataFrame with two columns:
                      - 'name': character's display name
                      - 'url': full URL to the character's wiki page
    """


    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url, config=config)

        print(f"Status: {result.success}")
        if result.success:
            data = json.loads(result.extracted_content)
            characters_df = pd.DataFrame(data)
            characters_df.columns = ["url", "name"]

            # Add the base URL to the character URLs
            characters_df["url"] = "https://onepiece.fandom.com" + characters_df["url"]
        else:
            print("The extraction failed.")

        return characters_df


# ============== EXTRACTING INFOBOX DATA ==============


async def infobox_extractor():
    
    characters_df = await urls_extractor()

    infoboxes_raw: List[List[Dict[str, Any]]] = []

    # Fetch infoboxes (list of dicts) for each character page

    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = await crawler.arun_many(characters_df["url"].tolist(), config=ib_config, dispatcher=dispatcher)

        for result in results:
            if result.success:
                # Parse JSON content into a Python list of dicts
                infobox = json.loads(result.extracted_content)
                infoboxes_raw.append(infobox)
            else:
                print(f"Extraction failed for {result.url}")

    # Define keys to exclude before building the DataFrame
    drop_keys = {
        "Japanese Name:",
        "Romanized Name:",
        "Alias:",
        "Epithet:",
        "Japanese Voice:",
        "English Voice:",
        "Meaning:",
    }

    # For each infobox, build a dict of key → value, skipping unwanted keys
    records: List[Dict[str, Any]] = []

    for idx, infobox in enumerate(infoboxes_raw):
        record: Dict[str, Any] = {}

        for entry in infobox:

            # Retrieve key and value (or pd.NA if missing)
            key = entry.get("key", pd.NA)
            value = entry.get("value", pd.NA)

            # Skip entries without a key
            if pd.isna(key):
                continue

            if key in drop_keys:
                continue

            record[key] = value

        records.append(record)

    df_infoboxes = pd.DataFrame(records)

    df_infoboxes.columns = [
                            "name",
                            "apparition",
                            "affiliations",
                            "occupations",
                            "origin",
                            "status",
                            "age",
                            "birthday",
                            "height",
                            "weight",
                            "bloodtype",
                            "devilfruit.name",
                            "devilfruit.type",
                            "residence",
                            "bounties",
                            ]

    return df_infoboxes


if __name__ == "__main__":
    df_infoboxes = asyncio.run(infobox_extractor())
    print(df_infoboxes.head(10))
    print(df_infoboxes.columns)
    output_path = "data_extraction/main_data.csv"
    df_infoboxes.to_csv(output_path, index=False)
    sprint(f"DataFrame saved to {output_path}", color="green", bold=True)