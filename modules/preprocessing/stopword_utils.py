# Module to get stopwords for selected language
from nltk.corpus import stopwords
import nltk

def get_stopwords(language: str):
    """
    Liefert die passenden Stopwords für die angegebene Sprache.
    """
    if language.lower() == "deutsch":
        try:
            return stopwords.words("german")
        except LookupError:
            nltk.download("stopwords")
            return stopwords.words("german")
    else:
        return "english"  # 'english' as string because scikit-learn handles this
