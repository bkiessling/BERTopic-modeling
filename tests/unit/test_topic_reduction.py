"""Reduction must preserve outliers, invalidate old IDs, and leave failed results intact."""

import unittest
import numpy as np
import pandas as pd
from server.services.analysis.state import AnalysisState
from server.services.modeling.train_model import TrainingResult
from server.services.modeling.configuration import TrainingConfig, ENGLISH_MODEL


class SmallModel:
    def __init__(self, fail=False):
        self.topics_ = [-1, 0, 1, 2]
        self.fail = fail

    def get_topic_info(self):
        topics = sorted(set(self.topics_))
        return pd.DataFrame(
            {
                "Topic": topics,
                "Count": [self.topics_.count(t) for t in topics],
                "Name": [f"topic_{t}" for t in topics],
                "Representation": [["word"] for _ in topics],
            }
        )

    def reduce_topics(self, documents, nr_topics):
        assert nr_topics == 2  # One real topic, plus the excluded outlier category.
        self.topics_ = [-1, 0, 0, 0]
        if self.fail:
            raise ValueError("reduction failed after mutation")


class TopicReductionTests(unittest.TestCase):
    def state(self, fail=False):
        model = SmallModel(fail)
        state = AnalysisState(
            TrainingResult(
                model,
                model.get_topic_info(),
                np.eye(4),
                ["noise", "a", "b", "c"],
                TrainingConfig(ENGLISH_MODEL, "Englisch"),
            ),
            [1, 2, 3, 4],
        )
        state.original_topics = [-1, 0, 1, 2]
        state.set_topic_names({0: "Name A", 1: "Name B", 2: "Name C"}, "test-model")
        return state

    def test_target_excludes_outliers_and_clears_names_and_old_restore(self):
        state = self.state()
        state.reduce_topics(1)
        self.assertEqual(state.result.model.topics_, [-1, 0, 0, 0])
        self.assertEqual(state.topic_reductions, [{"from": 3, "to": 1}])
        self.assertIsNone(state.original_topics)
        self.assertFalse(state.restore_outliers())
        self.assertEqual(state.topic_names, {})
        self.assertTrue(state.names_need_refresh)

    def test_failed_reduction_does_not_change_results_or_metadata(self):
        state = self.state(fail=True)
        model = state.result.model
        with self.assertRaisesRegex(ValueError, "failed"):
            state.reduce_topics(1)
        self.assertIs(state.result.model, model)
        self.assertEqual(model.topics_, [-1, 0, 1, 2])
        self.assertEqual(state.topic_names[0], "Name A")
        self.assertEqual(state.topic_reductions, [])
        self.assertFalse(state.names_need_refresh)

    def test_invalid_targets_do_not_mutate_the_model(self):
        state = self.state()
        for target in (0, -1, True, 1.5, 3, 10):
            with self.subTest(target=target), self.assertRaises(ValueError):
                state.reduce_topics(target)
        self.assertEqual(state.result.model.topics_, [-1, 0, 1, 2])
