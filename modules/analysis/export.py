"""Portable result export; no Streamlit or executable model serialization."""
import io
import json
import zipfile
from importlib.metadata import version
import pandas as pd


def _csv(frame):
    # Protect spreadsheet users from uploaded text interpreted as formulas.
    def safe(value):
        if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@')):
            return "'" + value
        return value
    # Series.map also works with pandas < 2.1 (DataFrame.map does not).
    return frame.apply(lambda column: column.map(safe)).to_csv(index=False).encode('utf-8-sig')


def build_result_archive(documents, ids, topics, topic_info, config, metadata=None):
    """Export current assignments, topic representations and reproducibility metadata."""
    if len(documents) != len(ids) or len(documents) != len(topics):
        raise ValueError('Dokumente, IDs und Themenzuordnungen müssen gleich lang sein.')
    frame = pd.DataFrame({'id': ids, 'text': documents, 'topic': topics})
    if 'CustomName' in topic_info.columns:
        frame['topic_name'] = frame.topic.map(dict(zip(topic_info.Topic, topic_info.CustomName)))
    manifest = {
        'schema_version': 1,
        'document_count': len(documents),
        'parameters': config,
        'metadata': metadata or {},
        'versions': {name: version(name) for name in (
            'bertopic', 'sentence-transformers', 'transformers', 'numpy',
            'pandas', 'scikit-learn', 'umap-learn', 'hdbscan', 'torch',
        )},
        'notes': [
            'CSV-Textzellen mit Formelpräfix werden mit einem Apostroph geschützt; JSON bewahrt Originalwerte.',
            'Enthält bereinigte Texte und aktuelle Topic-Zuordnungen, kein gespeichertes Modell und keine Rohdatei.',
            'Seed und Paketversionen dokumentieren den Lauf; hardwareübergreifende Bitgleichheit ist nicht garantiert.',
        ],
    }
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('documents.csv', _csv(frame))
        archive.writestr('topics.csv', _csv(topic_info))
        archive.writestr('documents.json', frame.to_json(orient='records', force_ascii=False, date_format='iso'))
        archive.writestr('topics.json', topic_info.to_json(orient='records', force_ascii=False, date_format='iso'))
        archive.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False))
    return output.getvalue()
