# Module to build table to display assinged topics on document level
import pandas as pd

# Function to build table containing ID, text column and assigned topic
def build_document_table(
    ids: list[str],
    docs: list[str],
    doc_topics: list[int],
    topic_info: pd.DataFrame,
    main_txt_col: str,
    view_mode: str = "Textbeitrag"
) -> pd.DataFrame:
    """
    Build a table of documents for display.

    Args:
        ids: List of document IDs.
        docs: List of cleaned text documents.
        doc_topics: List of assigned topic IDs for each document.
        topic_info: Topic info table (from BERTopic).
        main_txt_col: Column name to display as main text.
        view_mode: 'Textbeitrag' (long) or 'ID' (wide).

    Returns:
        DataFrame ready for display in the UI.
    """
    df = pd.DataFrame({
        "ID": ids,
        "Textbeitrag": docs,
        "Thema": doc_topics
    })

    # Merge topic keywords if available
    if "Representation" in topic_info.columns:
        keyword_map = topic_info[["Topic", "Representation"]].rename(
            columns={"Topic": "Thema", "Representation": "Keywords"}
        )
        df = df.merge(keyword_map, on="Thema", how="left")

    if view_mode == "Textbeitrag":
        # Return long format
        return df.rename(columns={"Textbeitrag": main_txt_col})[
            ["ID", "Thema", main_txt_col, "Keywords"]
        ]

    # Return wide format (group by ID)
    parts = []
    tmp = df.sort_values("ID").reset_index(drop=True)
    tmp["seq"] = tmp.groupby("ID").cumcount() + 1

    for i in range(1, tmp["seq"].max() + 1):
        part = (
            tmp[tmp["seq"] == i][["ID", "Thema", "Textbeitrag", "Keywords"]]
            .rename(columns={
                "Thema": f"Thema_{i}",
                "Textbeitrag": f"{main_txt_col}_{i}",
                "Keywords": f"Keywords_{i}"
            })
            .set_index("ID")
        )
        parts.append(part)

    return pd.concat(parts, axis=1).reset_index()

# Function to compute unique ids and number of text documents
def compute_document_stats(display_documents: pd.DataFrame) -> tuple[int, int]:
    """
    Compute summary stats from document table.

    Args:
        display_documents: Document table (either view mode).

    Returns:
        Tuple of (total_text_count, unique_id_count)
    """
    n_unique_ids = display_documents["ID"].nunique()
    n_texts = len(display_documents)
    return n_texts, n_unique_ids
