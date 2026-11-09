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
from modules.modeling.configuration import TrainingConfig, get_default_params, MULTILINGUAL_MODEL, ENGLISH_MODEL, MODELS, MODEL_OPTIONS
from modules.modeling.train_model import train_bertopic_model
from modules.analysis.export import build_result_archive
from modules.modeling.encoders import build_encoder
from unittest.mock import patch

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
        self.assertEqual(TrainingConfig.from_dict(json.loads(json.dumps(self.config.to_dict()))), self.config)

    def test_modeling_ui_disables_invalid_training_without_network(self):
        app = AppTest.from_file(str(ROOT/'pages/2_Modellierung.py'))
        app.session_state['cleaned_data'] = pd.DataFrame({'id':range(3), 'text':['cat dog']*3})
        app.session_state['text_column'] = 'text'
        app.session_state['id_column'] = 'id'
        app.run(timeout=60)
        self.assertFalse(app.exception, list(app.exception))
        self.assertTrue(next(button for button in app.button if button.label == 'Modell trainieren').disabled)
        self.assertTrue(any('Mindestens vier' in e.value for e in app.error))
        app.selectbox(key='model_language').select('Englisch').run(timeout=30)
        self.assertFalse(app.exception, list(app.exception))
        self.assertEqual(app.selectbox(key='embedding_model_Englisch').value, ENGLISH_MODEL)

    def test_all_six_german_models_are_visible_and_selectable(self):
        app = AppTest.from_file(str(ROOT/'pages/2_Modellierung.py')).run(timeout=60)
        options = [name for name, languages in MODELS.items() if 'Deutsch' in languages]
        self.assertGreaterEqual(len(options), 6)
        selector = app.selectbox(key='embedding_model_Deutsch')
        self.assertEqual(set(selector.options), {MODEL_OPTIONS[name].label for name in options})
        for name in options:
            app.selectbox(key='embedding_model_Deutsch').select(name).run(timeout=30)
            self.assertFalse(app.exception, list(app.exception))
            self.assertEqual(app.selectbox(key='embedding_model_Deutsch').value, name)

    def test_encoder_receives_model_specific_prompts(self):
        for name, prefix in (
            ('intfloat/multilingual-e5-base', 'query: '),
            ('Qwen/Qwen3-Embedding-0.6B', 'Instruct: Identify the main topic of the text for clustering.\nQuery: '),
            ('BAAI/bge-m3', ''),
        ):
            with self.subTest(model=name), patch('modules.modeling.encoders.SentenceTransformer') as loader:
                build_encoder(name)
                options = loader.call_args.kwargs
                self.assertEqual(options['model_kwargs'], {'use_safetensors': True})
                if prefix:
                    self.assertEqual(options['prompts']['clustering'], prefix)
                    self.assertEqual(options['default_prompt_name'], 'clustering')
                else:
                    self.assertNotIn('default_prompt_name', options)

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

    def test_export_includes_custom_topic_names(self):
        info = pd.DataFrame({'Topic':[0], 'Name':['auto'], 'CustomName':['Solarenergie']})
        archive = build_result_archive(['solar strom'], [1], [0], info, {})
        with zipfile.ZipFile(io.BytesIO(archive)) as output:
            self.assertEqual(json.loads(output.read('documents.json'))[0]['topic_name'], 'Solarenergie')
            self.assertEqual(json.loads(output.read('topics.json'))[0]['CustomName'], 'Solarenergie')

    def test_reject_misaligned_documents(self):
        with self.assertRaises(ValueError):
            build_result_archive(['text'], [], [0], pd.DataFrame(), {})
