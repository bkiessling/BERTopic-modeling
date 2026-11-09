"""BERTopic training independent of Streamlit and browser-session state."""
from dataclasses import dataclass
from typing import Any, Callable
import numpy as np
import pandas as pd
from bertopic import BERTopic
from bertopic.representation import KeyBERTInspired, MaximalMarginalRelevance
from bertopic.vectorizers import ClassTfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer
from nltk.corpus import stopwords
import umap
import hdbscan
from modules.modeling.configuration import TrainingConfig


@dataclass
class TrainingResult:
    model: Any
    topic_info: pd.DataFrame
    embeddings: np.ndarray
    documents: list[str]
    config: TrainingConfig


def train_bertopic_model(documents, config: TrainingConfig, embedding_model,
                        on_progress: Callable[[int, str], None] | None = None) -> TrainingResult:
    """Validate, train and return all artifacts; an optional callback reports progress."""
    documents = list(documents)
    errors = config.validate(documents)
    if errors:
        raise ValueError('\n'.join(errors))
    report = on_progress or (lambda percent, message: None)

    # Validate vocabulary before loading/encoding texts. Topic-level pruning may
    # still fail later because BERTopic vectorizes aggregated topic documents.
    if config.language == 'Deutsch':
        try:
            stop_words = stopwords.words('german')
        except LookupError as exc:
            raise ValueError('NLTK-Stopwörter fehlen. Bitte python -m nltk.downloader stopwords ausführen.') from exc
    else:
        stop_words = 'english'
    vectorizer = CountVectorizer(ngram_range=config.ngram_range, min_df=config.min_df,
                                 max_df=config.max_df, stop_words=stop_words)
    try:
        CountVectorizer(ngram_range=config.ngram_range, stop_words=stop_words).fit(documents)
    except ValueError as exc:
        raise ValueError('Nach Tokenisierung und Stopwortfilter bleiben keine verwendbaren Begriffe übrig.') from exc

    report(5, '1/6: Berechne Embeddings …')
    embeddings = np.asarray(embedding_model.encode(documents, batch_size=32, show_progress_bar=False))
    if embeddings.ndim != 2 or embeddings.shape[0] != len(documents) or not np.isfinite(embeddings).all():
        raise ValueError('Das Embedding-Modell hat ungültige oder unvollständige Vektoren erzeugt.')
    report(20, '2/6: Reduziere Dimensionen (UMAP) …')
    reducer = umap.UMAP(n_neighbors=config.n_neighbors, n_components=config.n_components,
                        min_dist=config.min_dist, metric='cosine', random_state=config.random_state, n_jobs=1)
    report(30, '3/6: Clustere mit HDBSCAN …')
    clusterer = hdbscan.HDBSCAN(min_cluster_size=config.min_cluster_size, metric='euclidean', prediction_data=True)
    report(40, '4/6: Baue Vektorisierung …')
    ctfidf = ClassTfidfTransformer(reduce_frequent_words=True)
    report(50, '5/6: Konfiguriere Repräsentationen …')
    representations = {}
    if 'KeyBERT' in config.representation_models:
        representations['KeyBERT'] = KeyBERTInspired(top_n_words=config.top_n_words)
    if 'MMR' in config.representation_models:
        representations['MMR'] = MaximalMarginalRelevance(top_n_words=config.top_n_words)
    report(60, '6/6: Trainiere Modell …')
    model = BERTopic(embedding_model=embedding_model, top_n_words=config.top_n_words,
                    umap_model=reducer, hdbscan_model=clusterer, vectorizer_model=vectorizer,
                    ctfidf_model=ctfidf, representation_model=representations,
                    calculate_probabilities=True, verbose=False)
    try:
        model.fit_transform(documents, embeddings)
    except ValueError as exc:
        if any(message in str(exc).lower() for message in ('empty vocabulary', 'no terms remain', 'max_df corresponds')):
            raise ValueError('Keine Begriffe für die ermittelten Themen übrig. min_df senken, max_df auf 1.0 setzen oder Textauswahl ändern. Die Häufigkeitsfilter gelten bei BERTopic für zusammengefasste Themen.') from exc
        raise
    report(100, 'Modelltraining abgeschlossen.')
    return TrainingResult(model, model.get_topic_info(), embeddings, documents, config)
