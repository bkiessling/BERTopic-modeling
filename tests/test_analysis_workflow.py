"""Exercise real BERTopic training and all analysis charts through Streamlit."""
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
from bertopic.backend import BaseEmbedder
from streamlit.testing.v1 import AppTest
from modules.modeling.train_model import train_bertopic_model
from modules.analysis.outlier_handler import reduce_outliers
from modules.modeling.configuration import TrainingConfig
from modules.modeling.train_model import TrainingResult
from modules.ui.analysis_state import AnalysisState

ROOT = Path(__file__).resolve().parents[1]

class OfflineEncoder(BaseEmbedder):
    def encode(self, documents, **kwargs):
        rng = np.random.default_rng(42)
        return np.vstack([np.eye(3)[i // 20] + rng.normal(0, .03, 3) for i in range(len(documents))])

class AnalysisWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = [text + ' ' + str(i) for text in (
            'katze hund tier futter', 'fussball sport stadion tor', 'computer software daten technik'
        ) for i in range(20)]
        cls.params = {
            'embedding_model': 'offline-test', 'language': 'Englisch',
            'umap': {'n_neighbors': 5, 'n_components': 2, 'min_dist': .1},
            'hdbscan': {'min_cluster_size': 5},
            'vectorizer': {'ngram_range': (1, 1), 'min_df': 1, 'max_df': .95},
            'representation_models': [], 'top_n_words': 5,
        }
        cls.config = TrainingConfig.from_dict(cls.params)
        cls.result = train_bertopic_model(cls.docs, cls.config, OfflineEncoder())
        cls.model, cls.info = cls.result.model, cls.result.topic_info
        cls.embeddings = OfflineEncoder().encode(cls.docs)

    def test_train_button_navigates_to_analysis_without_import_error(self):
        app = AppTest.from_file(str(ROOT / 'app.py'))
        for key, value in {
            'cleaned_data': pd.DataFrame({'id': range(60), 'text': self.docs}),
            'id_column': 'id', 'text_column': 'text', 'original_text_columns': ['Textbeitrag'],
        }.items():
            app.session_state[key] = value
        with patch('sentence_transformers.SentenceTransformer', return_value=OfflineEncoder()) as loader:
            app.run(timeout=60)
            app.switch_page('pages/2_Modellierung.py').run(timeout=60)
            app.selectbox(key='model_language').select('Englisch').run(timeout=30)
            app.multiselect[0].set_value([]).run(timeout=30)
            app.button[0].click().run(timeout=90)
            self.assertFalse(app.exception, list(app.exception))
            self.assertEqual(len(app.get('plotly_chart')), 3)
            self.assertEqual(len(app.get('download_button')), 1)
            self.assertEqual(len(app.session_state['analysis'].result.documents), 60)
            loader.assert_called_once()

    def test_analysis_renders_all_three_visualizations_and_reruns(self):
        app = AppTest.from_file(str(ROOT / 'pages/3_Analyse.py'))
        app.session_state['analysis'] = AnalysisState(self.result, [i//2 for i in range(60)])
        app.run(timeout=90)
        self.assertFalse(app.exception, list(app.exception))
        self.assertEqual(len(app.get('plotly_chart')), 3)
        self.assertEqual(sum(self.info.Count), 60)
        self.assertGreaterEqual(len(self.info[self.info.Topic != -1]), 2)
        app.radio[0].set_value('ID').run(timeout=30)
        self.assertFalse(app.exception, list(app.exception))
        metrics = {m.label: m.value for m in app.metric}
        self.assertEqual(metrics['Textbeiträge (n)'], '60')
        self.assertEqual(metrics['Unique IDs'], '30')
        app.multiselect[0].set_value([]).run(timeout=30)
        self.assertFalse(app.exception, list(app.exception))
        self.assertEqual(len(app.get('plotly_chart')), 2)
        self.assertTrue(any('Keine Themen ausgewählt' in x.value for x in app.info))

    def test_analysis_with_only_outliers(self):
        from test_visualizations import TopicModel
        model = TopicModel((-1,))
        model.topics_ = [-1, -1]
        info = model.get_topic_info()
        info['Count'] = 2
        info['Representation'] = [['wort']]
        app = AppTest.from_file(str(ROOT / 'pages/3_Analyse.py'))
        result = TrainingResult(model, info, np.ones((2, 4)), ['text eins', 'text zwei'], self.config)
        app.session_state['analysis'] = AnalysisState(result, [1, 2])
        app.run(timeout=30)
        self.assertFalse(app.exception, list(app.exception))
        self.assertEqual(len(app.get('plotly_chart')), 2)

    def test_modeling_without_data_does_not_download_model(self):
        app = AppTest.from_file(str(ROOT / 'pages/2_Modellierung.py')).run(timeout=60)
        self.assertFalse(app.exception, list(app.exception))
        self.assertTrue(any('zuerst Daten' in x.value for x in app.info))

    def test_no_outliers_is_a_noop(self):
        class Model:
            topics_ = [0, 0]
        self.assertFalse(reduce_outliers(Model(), ['a', 'b'], np.eye(2), .1))

    def test_outlier_reset_restores_model_and_tables(self):
        class Model:
            topics_ = [-1, 0, 0]
            vectorizer_model = None
            representation_model = None
            def reduce_outliers(self, **kwargs): return [0, 0, 0]
            def update_topics(self, docs, topics, **kwargs): self.topics_ = list(topics)
            def get_topic_info(self):
                ids, counts = np.unique(self.topics_, return_counts=True)
                return pd.DataFrame({'Topic': ids, 'Count': counts, 'Name': ['test']*len(ids),
                                     'Representation': [['test']]*len(ids)})
        model = Model()
        result = TrainingResult(model, model.get_topic_info(), np.eye(3), ['a', 'b', 'c'], self.config)
        state = AnalysisState(result, [1, 2, 3])
        self.assertTrue(state.reduce_outliers(.1))
        self.assertEqual(model.topics_, [0, 0, 0])
        self.assertTrue(state.restore_outliers())
        self.assertEqual(model.topics_, [-1, 0, 0])
        self.assertEqual(result.topic_info.Topic.tolist(), [-1, 0])
        self.assertFalse(state.restore_outliers())

if __name__ == '__main__': unittest.main()
