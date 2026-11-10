# Module to build a df containing a ID column and at least one text column
import pandas as pd


def build_text_df(df: pd.DataFrame, text_cols: list, id_col: str) -> pd.DataFrame:
    """
    Returns a DataFrame with columns: ['id', 'text'].
    Stacks multiple text columns into one long-form column.
    If id_col is 'ID generieren', a new ID is added automatically.
    """
    frames = []

    for col in text_cols:
        if id_col == "ID generieren":
            temp = df[[col]].copy()
            temp.rename(columns={col: "text"}, inplace=True)
            temp.insert(0, "id", range(1, len(temp) + 1))
        else:
            temp = df[[id_col, col]].copy()
            temp.rename(columns={id_col: "id", col: "text"}, inplace=True)
        frames.append(temp)

    text_df = pd.concat(frames, axis=0, ignore_index=True)
    return text_df
