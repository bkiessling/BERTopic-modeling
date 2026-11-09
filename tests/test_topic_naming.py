"""Keyword-only boundary, disabled controls and naming failures use no live API."""
import json
import os
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import numpy as np
import pandas as pd
import requests
from streamlit.testing.v1 import AppTest
from modules.analysis.topic_naming import name_topics, topic_keywords, TopicNamingError
from modules.modeling.configuration import TrainingConfig, ENGLISH_MODEL
from modules.modeling.train_model import TrainingResult
from modules.ui.analysis_state import AnalysisState

ROOT = Path(__file__).resolve().parents[1]


def response(labels, status=200):
    return Mock(status_code=status, json=lambda: {
        'status': 'completed', 'output': [{'type': 'message', 'content': [
            {'type': 'output_text', 'text': json.dumps({'topics': labels})}]}]})


class TopicNamingTests(unittest.TestCase):
    def test_only_keywords_reach_api_never_representative_documents(self):
        model = Mock()
        model.get_topic_info.return_value = pd.DataFrame({
            'Topic': [-1, 0], 'Representative_Docs': [['PRIVATE ORIGINAL TEXT']]*2,
            'Name': ['PRIVATE NAME']*2,
        })
        model.get_topic.return_value = [('solar', .5), ('strom', .2)]
        keywords = topic_keywords(model)
        with patch('modules.analysis.topic_naming.requests.post', return_value=response([{'topic_id':0, 'label':'Erneuerbare Energie'}])) as post:
            self.assertEqual(name_topics(keywords, 'Deutsch', 'test-only-key'), {0:'Erneuerbare Energie'})
        payload = post.call_args.kwargs['json']
        self.assertNotIn('PRIVATE', json.dumps(payload))
        self.assertEqual(json.loads(payload['input']), {'topics':[{'topic_id':0,'keywords':['solar','strom']}]})
        self.assertFalse(payload['store'])
        self.assertEqual(post.call_args.args[0], 'https://api.openai.com/v1/responses')

    def test_missing_key_and_no_topics_never_send_request(self):
        with patch('modules.analysis.topic_naming.requests.post') as post:
            with self.assertRaises(TopicNamingError): name_topics({0:['solar']}, 'Deutsch', '')
            self.assertEqual(name_topics({}, 'Deutsch', 'test-only-key'), {})
            post.assert_not_called()

    def test_provider_and_transport_errors_are_safe(self):
        for status in (401, 403, 404, 429, 500):
            with self.subTest(status=status), patch('modules.analysis.topic_naming.requests.post', return_value=response([], status)):
                with self.assertRaises(TopicNamingError) as caught:
                    name_topics({0:['solar']}, 'Deutsch', 'test-only-key')
                self.assertNotIn('test-only-key', str(caught.exception))
        with patch('modules.analysis.topic_naming.requests.post', side_effect=requests.ConnectionError()):
            with self.assertRaises(TopicNamingError): name_topics({0:['solar']}, 'Deutsch', 'test-only-key')

    def test_reject_missing_extra_duplicate_and_invalid_names(self):
        invalid = ([], [{'topic_id':1,'label':'Wrong'}], [{'topic_id':0,'label':' '}],
                   [{'topic_id':0,'label':'A'}, {'topic_id':0,'label':'B'}])
        for rows in invalid:
            with self.subTest(rows=rows), patch('modules.analysis.topic_naming.requests.post', return_value=response(rows)):
                with self.assertRaises(TopicNamingError): name_topics({0:['solar']}, 'Deutsch', 'test-only-key')

    def test_batch_response_is_validated(self):
        keywords = {i:['solar'] for i in range(21)}
        responses = [response([{'topic_id':i,'label':f'Thema {i}'} for i in range(20)]),
                     response([{'topic_id':20,'label':'Letztes Thema'}])]
        with patch('modules.analysis.topic_naming.requests.post', side_effect=responses) as post:
            labels = name_topics(keywords, 'Deutsch', 'test-only-key')
        self.assertEqual(len(labels), 21)
        self.assertEqual(post.call_count, 2)

    def test_ui_option_disabled_without_key(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY':'', 'BERTOPIC_OPENAI_API_KEY':''}), patch('modules.ui.topic_naming.openai_key', return_value=''):
            app = AppTest.from_file(str(ROOT/'pages/2_Modellierung.py')).run(timeout=60)
        self.assertFalse(app.exception, list(app.exception))
        self.assertTrue(app.checkbox(key='use_openai_naming').disabled)
        self.assertFalse(app.checkbox(key='use_openai_naming').value)

    def test_ui_option_enabled_but_off_with_key(self):
        with patch('modules.ui.topic_naming.openai_key', return_value='test-only-key'):
            app = AppTest.from_file(str(ROOT/'pages/2_Modellierung.py')).run(timeout=60)
        self.assertFalse(app.exception, list(app.exception))
        self.assertFalse(app.checkbox(key='use_openai_naming').disabled)
        self.assertFalse(app.checkbox(key='use_openai_naming').value)

    def test_names_are_view_metadata_and_clear_after_assignment_change(self):
        model = Mock()
        model.topics_ = [-1, 0, 0]
        info = pd.DataFrame({'Topic':[-1,0], 'Count':[1,2], 'Name':['outlier','auto'], 'Representation':[['noise'], ['solar']]})
        model.get_topic_info.return_value = info
        model.reduce_outliers.return_value = [0,0,0]
        state = AnalysisState(TrainingResult(model, info, np.eye(3), ['a','b','c'], TrainingConfig(ENGLISH_MODEL, 'Englisch')), [1,2,3])
        state.set_topic_names({0:'Solarenergie'}, 'gpt-4.1-mini')
        self.assertEqual(state.named_topic_info().CustomName.tolist(), ['outlier','Solarenergie'])
        self.assertNotIn('CustomName', info.columns)
        state.reduce_outliers(.1)
        self.assertEqual(state.topic_names, {})
        self.assertEqual(state.naming_metadata, {})
