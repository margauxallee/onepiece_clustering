import pandas as pd
import re
from typing import Optional
from terminal_style import sprint

BRACKET_PAREN_PATTERN = r"\[.*?\]|\(.*?\)"


def remove_patterns(text: str, pattern: str = BRACKET_PAREN_PATTERN) -> str:
    """
    Strip all substrings matching the given regex pattern (default: brackets and parentheses).
    """
    return re.sub(pattern, '', str(text)).strip()


def extract_number(text: str, regex: str) -> Optional[int]:
    """
    Extract integer from text using regex group; strips commas if present.
    """
    match = re.search(regex, str(text))
    if not match:
        return None
    num = match.group(1).replace(',', '')
    return int(num)


def extract_chapter(val: str) -> Optional[int]:
    return extract_number(val, r'Chapter\s*(\d+)')


def extract_last_bounty(val: str) -> Optional[int]:
    """
    From strings like '330,000,000[8]280,000,000[3]', extract the last number.
    """
    if pd.isna(val):
        return None
    amounts = re.findall(r'([\d,]+)(?=\[)', str(val))
    if not amounts:
        return None
    return int(amounts[-1].replace(',', ''))


def extract_int(val: str) -> Optional[int]:
    """
    Extract first integer found in text.
    """
    return extract_number(val, r'(\d+)')


def clean_text_column(series: pd.Series,
                      split_on: str = ';',
                      lower: bool = False,
                      replace_commas: bool = False,
                      remove_spaces: bool = False,
                      remove_nan: bool = False) -> pd.Series:
    """
    Generic cleaner: strip brackets/parentheses, split on delimiter, optional transforms.
    """
    cleaned_text = (series.astype(str)
              .str.replace(BRACKET_PAREN_PATTERN, '', regex=True)
              .str.split(split_on).str[0]
              .str.strip())
    if lower:
        cleaned_text = cleaned_text.str.lower()
    if replace_commas:
        cleaned_text = cleaned_text.str.replace(',', ';')
    if remove_spaces:
        cleaned_text = cleaned_text.str.replace(r'\s+', '', regex=True)
    if remove_nan:
        cleaned_text = cleaned_text.replace('nan', '', regex=True)
    return cleaned_text


def main():
    # Load and primary clean
    df_filtered = pd.read_csv("data_extraction/raw_crawled_data.csv")
    df_filtered['name'] = clean_text_column(df_filtered['name'])
    df_filtered['key'] = df_filtered['name'].str.replace(r'\s+', '', regex=True).str.lower()
    df_filtered['apparition'] = df_filtered['apparition'].apply(extract_chapter)

    # Clean demographic columns
    demo_cols = ['affiliations', 'occupations', 'origin', 'residence']
    for col in demo_cols:
        df_filtered[col] = clean_text_column(df_filtered[col], lower=True,
                                     replace_commas=True,
                                     remove_spaces=True,
                                     remove_nan=True)

    # Drop unused
    df_filtered.drop(columns=['age','birthday'], errors='ignore', inplace=True)

    # measures
    df_filtered[['height', 'weight']] = df_filtered[['height', 'weight']].applymap(extract_int)

    # Blood type / bounty
    df_filtered['bloodtype'] = df_filtered['bloodtype'].apply(lambda x: remove_patterns(x, r"\[.*?\]")).str.strip().str.replace('nan', '')
    df_filtered['bounty'] = df_filtered['bounty'].apply(extract_last_bounty)

    # Fruit names
    df_filtered['fruit.name'] = (df_filtered['fruit.name']
                             .str.split(';').str[0]
                             .str.replace(r"\(.*?\)", '', regex=True)
                             .str.replace('SMILE', ' Smile')
                             .str.strip())


    # HAKI MERGE
    # This table is initilaly imported from Kaggle and has been adapted 
    # to be ready-to-merge with the crawled data (key, columns names)
    df_haki = pd.read_csv("data_extraction/df_haki_table.csv")

    df_cleaned = df_filtered.merge(df_haki, left_on='key', right_on='character', how='outer')
    for col in ['haki.observation', 'haki.armament', 'haki.conqueror']:
        df_cleaned[col] = df_cleaned[col].fillna(0)

    df_cleaned.drop(columns=['character'], errors='ignore', inplace=True)

    df_cleaned.to_csv("data_extraction/df_final_onepiece.csv", index=False)

    sprint("Cleaning and merging processes completed.", color="green", bold=True)


if __name__ == '__main__':
    sprint("Starting data cleaning...", bold=True)
    main()
