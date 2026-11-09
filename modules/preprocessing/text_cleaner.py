# Module to clean and filter the selected text columns
import pandas as pd
import re


def clean_text(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"@\w+", "", text)  # Remove @usernames
    text = re.sub(r"http\S+|www\S+", "", text)  # Remove URLs
    text = re.sub(r"\d+", "", text)  # Remove digits
    text = re.sub(r"[^\w\säöüß]", "", text)  # Remove punctuation (keep umlauts)
    text = re.sub(r"\s+", " ", text)  # Collapse multiple spaces
    return text.strip()


def clean_text_column(df: pd.DataFrame, text_column: str) -> pd.DataFrame:
    """
    Apply `clean_text()` to a specified text column.
    """
    df = df.copy()
    df[text_column] = df[text_column].fillna("").astype(str)
    df[text_column] = df[text_column].apply(clean_text)
    return df


def filter_text_column(df: pd.DataFrame, text_column: str) -> pd.DataFrame:
    """
    Remove rows where the text column is empty or whitespace.
    """
    df = df.copy()
    df = df.dropna(subset=[text_column])
    df = df[df[text_column].str.strip() != ""]
    return df
