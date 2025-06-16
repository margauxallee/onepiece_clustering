import json
import asyncio
import os
import pandas as pd
from typing import List, Dict, Any
from terminal_style import sprint
from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    BrowserConfig,
    CacheMode,
    RateLimiter
)
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from crawl4ai.async_dispatcher import SemaphoreDispatcher


#  ----------- CREATING THE MAIN DATAFRAME WITH ALL THE ONE PIECE CHARACTERS INFOBOXES FROM ONE PIECE FANDOM WIKI -----------

# ----- DATAFRAME CONFIGURATION -----
OUTPUT_CSV = "data/dataframes/raw_crawled_data.csv"

COLUMN_ORDER = [
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
    "fruit.name",
    "devilfruit.type",
    "residence",
    "bounty",
]

KEY_MAP: Dict[str, str] = {
    "Official English Name:": "name",
    "Debut:": "apparition",
    "Affiliations:": "affiliations",
    "Occupations:": "occupations",
    "Status:": "status",
    "Birthday:": "birthday",
    "Origin:": "origin",
    "Age:": "age",
    "Height:": "height",
    "Weight:": "weight",
    "Blood Type:": "bloodtype",
    "English Name:": "fruit.name",
    "Type:": "devilfruit.type",
    "Residence:": "residence",
    "Bounty:": "bounty",
}

drop_keys = {
    "Japanese Name:",
    "Romanized Name:",
    "Alias:",
    "Epithet:",
    "Japanese Voice:",
    "English Voice:",
    "Meaning:",
}

# --- Parameters for the crawlers ---
schema_file_path = "data_extraction/json_schemas/schema.json"
with open(schema_file_path, "r", encoding="utf-8") as f:
    schema = json.load(f)

schema_infobox_file_path = "data_extraction/json_schemas/schema_infobox.json"
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
    max_session_permit=10,               #
    rate_limiter=RateLimiter(
        base_delay=(0.2, 0.5),          
        max_delay=5.0
    )
)

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

        if result.success:
            data = json.loads(result.extracted_content)
            characters_df = pd.DataFrame(data)
            characters_df.columns = ["url", "name"]

            # Add the base URL to the character URLs
            characters_df["url"] = "https://onepiece.fandom.com" + characters_df["url"]
        else:
            sprint("The extraction failed.", color="red", bold=True)

        return characters_df


# ============== EXTRACTING INFOBOX DATA ==============

async def infobox_extractor(chunk_size: int = 25) -> pd.DataFrame:
    """
        Asynchronously extracts infoboxes, by batches, from the One Piece Fandom wiki page.

        Args:
            chunk_size (int): Number of urls in each batch. THis helps to avoid overloading the server.
                            Defaults to 25.

        Returns:
            pd.DataFrame: A DataFrame containing the extracted infobox data with standardized column names.
                        The columns are defined in the COLUMN_ORDER list.
    """
     
    sprint("===== Starting the extraction of character URLs and names... =====", color="cyan", bold=True)

    characters_df = await urls_extractor()
    urls = characters_df["url"].tolist()

    # Remove existing CSV so header logic works
    if os.path.exists(OUTPUT_CSV):
        os.remove(OUTPUT_CSV)

    sprint(" ===== Starting the extraction of infobox data... =====", color="cyan", bold=True)

    for batch_start in range(0, len(urls), chunk_size):
        batch_urls = urls[batch_start : batch_start + chunk_size]

        async with AsyncWebCrawler(config=browser_config) as crawler:
            results = await crawler.arun_many(
                batch_urls,
                config=ib_config,
                dispatcher=dispatcher
            )

        records: List[Dict[str, Any]] = []
        for result in results:
            if not result.success:
                sprint(f"Failure for {result.url}", color="red")
                continue

            infobox = json.loads(result.extracted_content)
            record: Dict[str, Any] = {}

            for info in infobox:
                initial_key = info.get("key", pd.NA)
                value = info.get("value", pd.NA)

                if pd.isna(initial_key):
                    continue
                new_key = KEY_MAP.get(initial_key)
                if new_key is None:
                    continue

                record[new_key] = value

            records.append(record)

        # Build the DataFrame and ensure correct columns/order
        df_batch = pd.DataFrame(records)
        df_batch = df_batch.reindex(columns=COLUMN_ORDER)

        # Write header only for the first batch
        write_header = not os.path.exists(OUTPUT_CSV)
        df_batch.to_csv(OUTPUT_CSV, mode="a", index=False, header=write_header)

        batch_number = (batch_start // chunk_size) + 1
        sprint(f" Batch {batch_number} saved ({len(records)} lines)", color= "pink", bold=True)

    # Load and return the full dataset
    df_infoboxes = pd.read_csv(OUTPUT_CSV)
    return df_infoboxes


if __name__ == "__main__":
    final_df = asyncio.run(infobox_extractor())
    print(final_df.head(10))
    print(final_df.columns)
    sprint(f"DataFrame saved to {OUTPUT_CSV}", color="green", bold=True)