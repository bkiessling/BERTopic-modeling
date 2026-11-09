"""Framework-independent training configuration and input validation."""
from dataclasses import dataclass
from numbers import Integral, Real
import math

MULTILINGUAL_MODEL = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
ENGLISH_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
MODELS = {
    MULTILINGUAL_MODEL: ('Deutsch', 'Englisch'),
    'sentence-transformers/paraphrase-multilingual-mpnet-base-v2': ('Deutsch', 'Englisch'),
    ENGLISH_MODEL: ('Englisch',),
    'sentence-transformers/all-mpnet-base-v2': ('Englisch',),
}


def recommended_model(language):
    return MULTILINGUAL_MODEL if language == 'Deutsch' else ENGLISH_MODEL


def get_default_params(n_docs, avg_text_len=100):
    """Language determines the embedding default; length only affects n-grams."""
    return {
        'embedding_model': MULTILINGUAL_MODEL, 'language': 'Deutsch',
        'n_neighbors': min(50 if n_docs >= 10000 else 15 if n_docs >= 1000 else 5, max(2, n_docs - 1)),
        'n_components': min(5, max(2, n_docs - 2)), 'min_dist': .1,
        'min_cluster_size': min(30 if n_docs >= 10000 else 15 if n_docs >= 1000 else 5, max(2, n_docs)),
        'ngram_range': (1, 1) if avg_text_len < 30 else (1, 2),
        'min_df': .001, 'max_df': 1.0,
        'representations': ['KeyBERT', 'MMR'], 'top_n_words': 10,
    }


@dataclass(frozen=True)
class TrainingConfig:
    embedding_model: str
    language: str
    n_neighbors: int = 5
    n_components: int = 5
    min_dist: float = .1
    min_cluster_size: int = 5
    ngram_range: tuple[int, int] = (1, 2)
    min_df: int | float = .001
    max_df: int | float = 1.0
    representation_models: tuple[str, ...] = ('KeyBERT', 'MMR')
    top_n_words: int = 10
    random_state: int = 42

    def to_dict(self):
        return {
            'embedding_model': self.embedding_model, 'language': self.language,
            'umap': {'n_neighbors': self.n_neighbors, 'n_components': self.n_components, 'min_dist': self.min_dist},
            'hdbscan': {'min_cluster_size': self.min_cluster_size},
            'vectorizer': {'ngram_range': self.ngram_range, 'min_df': self.min_df, 'max_df': self.max_df},
            'representation_models': list(self.representation_models), 'top_n_words': self.top_n_words,
            'random_state': self.random_state,
        }

    @classmethod
    def from_dict(cls, params):
        return cls(embedding_model=params['embedding_model'], language=params['language'],
                   **params['umap'], **params['hdbscan'], **params['vectorizer'],
                   representation_models=tuple(params['representation_models']),
                   top_n_words=params.get('top_n_words', 10), random_state=params.get('random_state', 42))

    def validate(self, documents):
        errors = []
        count = len(documents)
        if count < 4:
            errors.append('Mindestens vier nichtleere Texte sind für das Training erforderlich.')
        if any(not isinstance(doc, str) or not doc.strip() for doc in documents):
            errors.append('Alle Dokumente müssen nichtleere Texte sein.')
        if self.language not in ('Deutsch', 'Englisch'):
            errors.append('Sprache muss Deutsch oder Englisch sein.')
        if not isinstance(self.embedding_model, str) or not self.embedding_model.strip():
            errors.append('Ein Embedding-Modell muss angegeben werden.')
        if self.embedding_model in MODELS and self.language not in MODELS[self.embedding_model]:
            errors.append('Das ausgewählte Embedding-Modell unterstützt die gewählte Sprache nicht.')
        for name, value, low, high in (
            ('n_neighbors', self.n_neighbors, 2, count - 1),
            ('n_components', self.n_components, 2, count - 2),
            ('min_cluster_size', self.min_cluster_size, 2, count),
            ('top_n_words', self.top_n_words, 1, 100),
            ('random_state', self.random_state, 0, 2**32 - 1),
        ):
            if isinstance(value, bool) or not isinstance(value, Integral) or not low <= value <= high:
                errors.append(f'{name} muss eine ganze Zahl zwischen {low} und {max(low, high)} sein.')
        if not isinstance(self.min_dist, Real) or not math.isfinite(self.min_dist) or not 0 <= self.min_dist <= 1:
            errors.append('min_dist muss zwischen 0 und 1 liegen.')
        if (not isinstance(self.ngram_range, (tuple, list)) or len(self.ngram_range) != 2 or any(isinstance(n, bool) or not isinstance(n, Integral) for n in self.ngram_range)
                or not 1 <= self.ngram_range[0] <= self.ngram_range[1] <= 3):
            errors.append('N-Gramme müssen aufsteigend zwischen 1 und 3 liegen.')
        valid_df = True
        for name, value in (('min_df', self.min_df), ('max_df', self.max_df)):
            if (isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value)
                    or (isinstance(value, Integral) and value < 1)
                    or (not isinstance(value, Integral) and not 0 < value <= 1)):
                errors.append(f'{name}: positive ganze Anzahl oder Anteil größer 0 bis 1 angeben.')
                valid_df = False
        if valid_df:
            # Preflight on source documents; BERTopic later vectorizes topic aggregates.
            lower = self.min_df if isinstance(self.min_df, Integral) else math.ceil(self.min_df * count)
            upper = self.max_df if isinstance(self.max_df, Integral) else math.floor(self.max_df * count)
            if lower > upper:
                errors.append('min_df darf die durch max_df erlaubte Häufigkeit nicht überschreiten.')
        if set(self.representation_models) - {'KeyBERT', 'MMR'}:
            errors.append('Unbekannte Themenrepräsentation; erlaubt sind KeyBERT und MMR.')
        return errors
