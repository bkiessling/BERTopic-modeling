"""One explicit analysis object at the Streamlit session boundary."""

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
    trained_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if len(self.ids) != len(self.result.documents):
            raise ValueError("IDs und Dokumente müssen gleich lang sein.")

    def named_topic_info(self):
        return with_topic_names(self.result.topic_info, self.topic_names)

    def set_topic_names(self, labels, model):
        self.topic_names = dict(labels)
        self.naming_metadata = {
            "provider": "OpenAI",
            "model": model,
            "input": "topic_keywords_only",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "topic_count": len(labels),
        }

    def clear_topic_names(self):
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
