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

#  ----------- CREATING THE MAIN DATAFRAME WITH ALL THE ONE PIECE CHARACTERS INFOBOXES FROM ONE PIECE FANDOM WIKI -----------

#Parameters for the crawlers
schema_file_path = "schema.json"
with open(schema_file_path, "r", encoding="utf-8") as f:
    schema = json.load(f)

schema_infobox_file_path = "schema_infobox.json"
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
    cache_mode=CacheMode.BYPASS
)

browser_config = BrowserConfig(
    headless=True,
    stream=True,
    viewport_width=1280,
    viewport_height=800
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

    infoboxes = []

    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = await crawler.arun_many(characters_df["url"].tolist(), config=ib_config)

        for result in results:
            if result.success:
                infobox = json.loads(result.extracted_content)
                infoboxes.append(infobox)  
            else:
                print("The extraction failed.")

        infoboxes_df = pd.DataFrame(infoboxes)
        infoboxes_df.columns = [
                                "name",
                                "officialenglishname",
                                "debut.manga",
                                "debut.anime",
                                "affiliations",
                                "occupations",
                                "origin",
                                "residence",
                                "status",
                                "age",
                                "birthday",
                                "height",
                                "bloodtype",
                                "bounties",
                                "devilfruit.japanesename",
                                "devilfruit.englishname",
                                "devilfruit.type"
                                ]

        return infoboxes_df
        

if __name__ == "__main__":
    infoboxes_df = asyncio.run(infobox_extractor())
    print(infoboxes_df.head())
    infoboxes_df.to_csv("main_data.csv", index=False)
