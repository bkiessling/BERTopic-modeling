"""Explicit analysis state, independent of HTTP and UI."""

from copy import deepcopy
from numbers import Integral
from dataclasses import dataclass, field
from datetime import datetime, timezone
from server.services.modeling.train_model import TrainingResult
from server.services.analysis.topic_naming import with_topic_names
from server.services.analysis.outlier_handler import reduce_outliers, restore_outliers


@dataclass
class AnalysisState:
    result: TrainingResult
    ids: list
    text_columns: list[str] = field(default_factory=lambda: ["Textbeitrag"])
    preprocessing: dict = field(default_factory=dict)
    original_topics: list[int] | None = None
    outlier_thresholds: list[float] = field(default_factory=list)
    topic_names: dict[int, str] = field(default_factory=dict)
    naming_metadata: dict = field(default_factory=dict)
    topic_reductions: list[dict] = field(default_factory=list)
    names_need_refresh: bool = False
    trained_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if len(self.ids) != len(self.result.documents):
            raise ValueError("IDs und Dokumente müssen gleich lang sein.")

    def named_topic_info(self):
        return with_topic_names(self.result.topic_info, self.topic_names)

    def set_topic_names(self, labels, model):
        self.names_need_refresh = False
        self.topic_names = dict(labels)
        self.naming_metadata = {
            "provider": "OpenAI",
            "model": model,
            "input": "topic_keywords_only",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "topic_count": len(labels),
        }

    def clear_topic_names(self):
        self.names_need_refresh = self.names_need_refresh or bool(self.topic_names)
        self.topic_names.clear()
        self.naming_metadata.clear()

    def reduce_outliers(self, threshold):
        result = self.result
        original = list(result.model.topics_)
        if not reduce_outliers(result.model, result.documents, result.embeddings, threshold):
            return False
        if self.original_topics is None:
            self.original_topics = original
        self.outlier_thresholds.append(threshold)
        result.topic_info = result.model.get_topic_info()
        self.clear_topic_names()
        return True

    def restore_outliers(self):
        if self.original_topics is None:
            return False
        restore_outliers(self.result.model, self.result.documents, self.original_topics)
        self.result.topic_info = self.result.model.get_topic_info()
        self.clear_topic_names()
        self.original_topics = None
        self.outlier_thresholds.clear()
        return True

    def reduce_topics(self, target):
        """Merge semantically similar topics on a copy; preserve the result if merging fails."""
        current = len(set(self.result.model.topics_) - {-1})
        if (
            isinstance(target, bool)
            or not isinstance(target, Integral)
            or not 1 <= target < current
        ):
            raise ValueError(f"Die Zielanzahl muss zwischen 1 und {max(1, current - 1)} liegen.")
        model = self.result.model
        # These fitted objects are read-only during reduce_topics. Avoid copying encoder weights.
        shared = [
            getattr(model, name, None)
            for name in ("embedding_model", "umap_model", "hdbscan_model")
        ]
        candidate = deepcopy(model, {id(value): value for value in shared if value is not None})
        candidate.reduce_topics(
            self.result.documents, nr_topics=int(target) + int(-1 in model.topics_)
        )
        info = candidate.get_topic_info()
        if len(set(candidate.topics_) - {-1}) != target:
            raise ValueError("Die gewünschte Themenanzahl konnte nicht hergestellt werden.")
        self.result.model = candidate
        self.result.topic_info = info
        self.topic_reductions.append({"from": current, "to": int(target)})
        # Saved outlier assignments refer to the old topic IDs and cannot be restored safely.
        self.original_topics = None
        self.clear_topic_names()
