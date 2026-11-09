"""Framework-independent updates of BERTopic's document assignments."""
import numpy as np


def reduce_outliers(topic_model, docs, embeddings, threshold):
    if not 0 <= threshold <= 1:
        raise ValueError('Der Ausreißerschwellwert muss zwischen 0 und 1 liegen.')
    if -1 not in topic_model.topics_:
        return False
    new_topics = topic_model.reduce_outliers(
        documents=docs, topics=list(topic_model.topics_),
        embeddings=np.asarray(embeddings), threshold=threshold, strategy='embeddings',
    )
    restore_outliers(topic_model, docs, new_topics)
    return True


def restore_outliers(topic_model, docs, topics):
    """Apply explicit assignments and recompute dependent topic representations."""
    if len(topics) != len(docs):
        raise ValueError('Dokumente und Themenzuordnungen müssen gleich lang sein.')
    topic_model.update_topics(docs=docs, topics=list(topics),
                              vectorizer_model=topic_model.vectorizer_model,
                              representation_model=topic_model.representation_model)
