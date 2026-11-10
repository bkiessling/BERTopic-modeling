# modules/upload/delimiter_utils.py


def detect_delimiter(text: str) -> str:
    """
    Detect the most likely delimiter in a CSV text sample.
    """
    if ";" in text and text.count(";") > text.count(","):
        return ";"
    elif "," in text and text.count(",") > text.count("\t"):
        return ","
    else:
        return "\t"


def get_delimiter_label(delimiter: str) -> str:
    """
    Return a human-readable label for a given delimiter (used in Streamlit radio buttons).
    """
    return {",": "Comma (,)", ";": "Semicolon (;)", "\t": "Tab (\\t)"}.get(delimiter, delimiter)
