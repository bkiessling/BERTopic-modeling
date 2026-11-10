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

    def merge_topics(self, documents, topics_to_merge):
        self.topics_ = [-1, 1, 1, 0]  # BERTopic may renumber the untouched topic.
        if self.fail:
            raise ValueError("merge failed after mutation")


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


class TopicEditingTests(unittest.TestCase):
    state = TopicReductionTests.state

    def test_manual_merge_preserves_other_names_after_renumbering(self):
        state = self.state()
        state.set_manual_topic_name(2, "Unverändertes Thema")
        state.merge_topics([0, 1])
        self.assertEqual(state.result.model.topics_, [-1, 1, 1, 0])
        self.assertEqual(state.manual_topic_names, {0: "Unverändertes Thema"})
        self.assertEqual(state.topic_names, {0: "Name C"})
        names = state.named_topic_info().set_index("Topic").CustomName.to_dict()
        self.assertEqual(names[-1], "Outlier")
        self.assertEqual(names[0], "Unverändertes Thema")
        self.assertTrue(state.names_need_refresh)
        state.set_manual_topic_name(1, "Neue gemeinsame Gruppe")
        self.assertFalse(state.names_need_refresh)
        state.set_topic_names({0: "KI-Name A", 1: "KI-Name B"}, "test-model")
        self.assertEqual(
            state.named_topic_info().set_index("Topic").loc[1, "CustomName"],
            "Neue gemeinsame Gruppe",
        )
        self.assertIsNone(state.original_topics)

    def test_failed_merge_preserves_model_and_names(self):
        state = self.state(fail=True)
        state.set_manual_topic_name(2, "Manuell")
        original = state.result.model
        with self.assertRaisesRegex(ValueError, "merge failed"):
            state.merge_topics([0, 1])
        self.assertIs(state.result.model, original)
        self.assertEqual(original.topics_, [-1, 0, 1, 2])
        self.assertEqual(state.manual_topic_names, {2: "Manuell"})
        self.assertEqual(state.topic_merges, [])

    def test_invalid_merge_and_outlier_names_are_rejected(self):
        state = self.state()
        for selection in ([0], [0, 0], [-1, 0], [0, 99], [True, 1]):
            with self.subTest(selection=selection), self.assertRaises(ValueError):
                state.merge_topics(selection)
        for topic, label in ((-1, "Kein Outlier"), (99, "Fehlt"), (0, "  "), (0, "x" * 121)):
            with self.subTest(topic=topic), self.assertRaises(ValueError):
                state.set_manual_topic_name(topic, label)
        state.topic_names[-1] = "Ignorierter Name"
        self.assertEqual(
            state.named_topic_info().set_index("Topic").loc[-1, "CustomName"], "Outlier"
        )
