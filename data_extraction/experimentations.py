import json
import asyncio
from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    BrowserConfig,
    CacheMode
)
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
import pandas as pd
from typing import List, Dict, Any
from terminal_style import sprint

#  ----------- CREATING THE MAIN DATAFRAME WITH ALL THE ONE PIECE CHARACTERS INFOBOXES FROM ONE PIECE FANDOM WIKI -----------

#Parameters for the crawlers

schema_infobox_file_path = "data_extraction/schema_infobox.json"
with open(schema_infobox_file_path, "r", encoding="utf-8") as f:
    schema_infobox = json.load(f)


css_extraction_2 = JsonCssExtractionStrategy(schema_infobox)


ib_config = CrawlerRunConfig(
    extraction_strategy=css_extraction_2,
    cache_mode=CacheMode.BYPASS
)

from crawl4ai import BrowserConfig

browser_config = BrowserConfig(
    headless=True,
    viewport_width=1280,
    viewport_height=800,
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
)



# ============== EXTRACTING INFOBOX DATA ==============


async def infobox_extractor() -> pd.DataFrame:
    """
    Extract infoboxes from multiple URLs and return a DataFrame where each row
    corresponds to one infobox (one page) and each column corresponds to a key
    encountered in those infoboxes. Specified columns are filtered out before
    DataFrame creation for performance.
    """

    infoboxes_raw: List[List[Dict[str, Any]]] = []

    # 1) Fetch infoboxes (list of dicts) for each character page
    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = await crawler.arun_many(
            [
                "https://onepiece.fandom.com/wiki/Bartholomew_Kuma",
                "https://onepiece.fandom.com/wiki/Absalom"
            ],
            config=ib_config
        )

        for result in results:
            if result.success:
                # Parse JSON content into a Python list of dicts
                infobox = json.loads(result.extracted_content)
                infoboxes_raw.append(infobox)
            else:
                print(f"Extraction failed for {result.url}")

    # 2) Define keys to exclude before building the DataFrame
    drop_keys = {
        "Japanese Name:",
        "Romanized Name:",
        "Alias:",
        "Epithet:",
        "Japanese Voice:",
        "English Voice:",
        "Meaning:",
    }

    # 3) For each infobox, build a dict of key → value, skipping unwanted keys
    records: List[Dict[str, Any]] = []

    for idx, infobox in enumerate(infoboxes_raw):
        record: Dict[str, Any] = {}
        undefined_count = 0

        for entry in infobox:
            # Skip any entry that is not a dict
            if not isinstance(entry, dict):
                continue

            # Retrieve key and value (or pd.NA if missing)
            key = entry.get("key", pd.NA)
            value = entry.get("value", pd.NA)

            # Skip entries without a key
            if pd.isna(key):
                continue

            # Skip keys that are in the drop list
            if key in drop_keys:
                continue

            # If the same key appears multiple times, append a numeric suffix
            if key in record:
                suffix = 1
                new_key = f"{key.rstrip(':')}_{suffix}:"
                while new_key in record:
                    suffix += 1
                    new_key = f"{key.rstrip(':')}_{suffix}:"
                key = new_key

            record[key] = value

        records.append(record)

    # 4) Build the final DataFrame (one row per infobox)
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