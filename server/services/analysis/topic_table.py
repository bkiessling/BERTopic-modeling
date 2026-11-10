# modules/analysis/topic_utils.py
import pandas as pd


def build_topic_table(
    topic_info: pd.DataFrame, docs: list[str], top_n_words: int = 10
) -> pd.DataFrame:
    """Return a display-ready topics table (renamed cols, percentages, keywords)."""
    tbl = topic_info.copy()
    tbl["Percentage"] = (tbl["Count"] / len(docs) * 100).round(2)
    tbl = tbl.rename(
        columns={
            "Topic": "Thema",
            "Name": "Themenname",
            "Count": "Dokumente (n)",
            "Percentage": "Anteil (%)",
            "Representation": "Keywords",
        }
    )
    if "CustomName" in tbl.columns:
        tbl["Themenname"] = tbl["CustomName"]
    if "Keywords" in tbl.columns:
        tbl["Keywords"] = tbl["Keywords"].apply(
            lambda x: ", ".join(word for word in x[:top_n_words] if word)
            if isinstance(x, list)
            else x
        )
    for col in ["KeyBERT", "MMR"]:
        if col not in tbl.columns:
            tbl[col] = ""
    return tbl[["Themenname", "Thema", "Dokumente (n)", "Anteil (%)", "Keywords", "KeyBERT", "MMR"]]


def compute_topic_stats(topic_info: pd.DataFrame, docs: list[str]) -> tuple[int, float, int]:
    """Return n_topics, outlier_pct, avg_docs."""
    stats = topic_info.rename(columns={"Topic": "Thema", "Count": "Dokumente (n)"})
    non_outl = stats[stats["Thema"] != -1]
    outl = stats[stats["Thema"] == -1]
    n_topics = len(non_outl)
    outlier_pct = round(outl["Dokumente (n)"].sum() / len(docs) * 100, 2)
    avg_docs = int(non_outl["Dokumente (n)"].mean()) if n_topics else 0

    return n_topics, outlier_pct, avg_docs
