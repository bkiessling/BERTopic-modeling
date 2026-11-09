"""Keep model assignments, analysis tables and reset state consistent."""
import numpy as np
from modules.analysis.topic_table import build_topic_table


def _refresh(topic_model, docs, top_n_words, session_state):
    info = topic_model.get_topic_info()
    session_state['topic_info'] = info
    session_state['display_topics'] = build_topic_table(info, docs, top_n_words)


def reduce_outliers(topic_model, docs, embeddings, threshold, top_n_words, session_state):
    if -1 not in topic_model.topics_:
        return False
    original_topics = list(topic_model.topics_)
    new_topics = topic_model.reduce_outliers(
        documents=docs, topics=original_topics,
        embeddings=np.asarray(embeddings), threshold=threshold, strategy='embeddings',
    )
    topic_model.update_topics(docs=docs, topics=new_topics,
                              vectorizer_model=topic_model.vectorizer_model,
                              representation_model=topic_model.representation_model)
    if session_state.get('original_topics') is None:
        session_state['original_topics'] = original_topics
    _refresh(topic_model, docs, top_n_words, session_state)
    return True


def restore_outliers(topic_model, docs, top_n_words, session_state):
    original = session_state.get('original_topics')
    if original is None:
        return False
    topic_model.update_topics(docs=docs, topics=list(original),
                              vectorizer_model=topic_model.vectorizer_model,
                              representation_model=topic_model.representation_model)
    _refresh(topic_model, docs, top_n_words, session_state)
    session_state['original_topics'] = None
    return True
