"""Validation happens before encoder work; archives preserve current assignments."""
import io
import json
import zipfile
import unittest
from dataclasses import replace
from unittest.mock import Mock
import pandas as pd
from streamlit.testing.v1 import AppTest
from pathlib import Path
from modules.modeling.configuration import TrainingConfig, get_default_params, MULTILINGUAL_MODEL, ENGLISH_MODEL
from modules.modeling.train_model import train_bertopic_model
from modules.analysis.export import build_result_archive

ROOT = Path(__file__).resolve().parents[1]

class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.config = TrainingConfig(ENGLISH_MODEL, 'Englisch', n_components=2, n_neighbors=3, min_cluster_size=2)
        self.docs = ['cat dog animal'] * 8

    def test_reject_invalid_parameters_before_encoding(self):
        for changes in ({'n_neighbors':8}, {'n_components':7}, {'min_cluster_size':9},
                        {'min_dist':float('nan')}, {'min_df':.9, 'max_df':.1},
                        {'ngram_range':(2,1)}, {'language':'Deutsch'},
                        {'representation_models':('unknown',)}, {'top_n_words':0}):
            with self.subTest(changes=changes):
                encoder = Mock()
                with self.assertRaises(ValueError):
                    train_bertopic_model(self.docs, replace(self.config, **changes), encoder)
                encoder.encode.assert_not_called()

    def test_empty_and_small_corpora(self):
        for docs in ([], ['cat']*3, ['cat']*7 + [' ']):
            self.assertTrue(self.config.validate(docs))

    def test_empty_vocabulary_before_encoding(self):
        encoder = Mock()
        with self.assertRaisesRegex(ValueError, 'keine verwendbaren Begriffe'):
            train_bertopic_model(['the and'] * 8, self.config, encoder)
        encoder.encode.assert_not_called()

    def test_model_default_does_not_depend_on_text_length(self):
        for length in (10, 50, 1000):
            self.assertEqual(get_default_params(30, length)['embedding_model'], MULTILINGUAL_MODEL)

    def test_configuration_roundtrip(self):
        self.assertEqual(TrainingConfig.from_dict(self.config.to_dict()), self.config)

    def test_modeling_ui_disables_invalid_training_without_network(self):
        app = AppTest.from_file(str(ROOT/'pages/2_Modellierung.py'))
        app.session_state['cleaned_data'] = pd.DataFrame({'id':range(3), 'text':['cat dog']*3})
        app.session_state['text_column'] = 'text'
        app.session_state['id_column'] = 'id'
        app.run(timeout=60)
        self.assertFalse(app.exception, list(app.exception))
        self.assertTrue(app.button[0].disabled)
        self.assertTrue(any('Mindestens vier' in e.value for e in app.error))
        app.selectbox(key='model_language').select('Englisch').run(timeout=30)
        self.assertFalse(app.exception, list(app.exception))
        self.assertEqual(app.selectbox(key='embedding_model_Englisch').value, ENGLISH_MODEL)

class ExportTests(unittest.TestCase):
    def test_archive_roundtrip_and_csv_formula_protection(self):
        info = pd.DataFrame({'Topic':[-1,0], 'Count':[1,1], 'Representation':[['wort'],['katze']]})
        blob = build_result_archive(['=SUM(1,2)', 'Grüße'], [12,12], [-1,0], info,
                                    {'language':'Deutsch'}, {'outlier_thresholds':[.1]})
        with zipfile.ZipFile(io.BytesIO(blob)) as archive:
            self.assertEqual(set(archive.namelist()), {'documents.csv','topics.csv','documents.json','topics.json','manifest.json'})
            docs = json.loads(archive.read('documents.json'))
            self.assertEqual(docs[0], {'id':12,'text':'=SUM(1,2)','topic':-1})
            self.assertEqual(docs[1]['text'], 'Grüße')
            csv = pd.read_csv(io.BytesIO(archive.read('documents.csv')))
            self.assertEqual(csv.text.iloc[0], "'=SUM(1,2)")
            manifest = json.loads(archive.read('manifest.json'))
            self.assertEqual(manifest['document_count'], 2)
            self.assertEqual(manifest['metadata']['outlier_thresholds'], [.1])
            self.assertIn('bertopic', manifest['versions'])

    def test_reject_misaligned_documents(self):
        with self.assertRaises(ValueError):
            build_result_archive(['text'], [], [0], pd.DataFrame(), {})
