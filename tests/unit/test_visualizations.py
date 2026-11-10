"""Regression tests for the analysis charts, without remote model downloads."""

import unittest
import numpy as np
import pandas as pd
from server.services.viz.topic_similarity import plot_topic_similarity
from server.services.viz.topic_network import plot_topic_network


class TopicModel:
    def __init__(self, topics=(-1, 0, 1)):
        self.ids = list(topics)
        self.topic_embeddings_ = np.eye(len(topics), 4)

    def get_topic_info(self):
        return pd.DataFrame(
            {
                "Topic": self.ids,
                "Count": [5] * len(self.ids),
                "Name": [f"{t}_thema" for t in self.ids],
            }
        )

    def get_topic(self, topic):
        return [("wort", 0.5), ("thema", 0.2)]


class VisualizationTests(unittest.TestCase):
    def test_similarity_supports_current_plotly(self):
        fig = plot_topic_similarity(TopicModel())
        self.assertEqual(np.asarray(fig.data[0].z).shape, (2, 2))

    def test_similarity_with_only_outliers(self):
        fig = plot_topic_similarity(TopicModel((-1,)))
        self.assertEqual(len(fig.data), 0)
        self.assertTrue(fig.layout.annotations)

    def test_similarity_uses_topic_ids_instead_of_dataframe_indices(self):
        model = TopicModel((0, 1))
        model.topic_embeddings_ = np.array([[1.0, 0.0], [0.0, 1.0]])
        original_info = model.get_topic_info()
        model.get_topic_info = lambda: original_info.iloc[::-1].set_axis([99, 42])
        fig = plot_topic_similarity(model)
        np.testing.assert_allclose(fig.data[0].z, [[0.0, 1.0], [1.0, 0.0]])

    def test_network_rejects_misaligned_data(self):
        with self.assertRaisesRegex(ValueError, "gleich viele Zeilen"):
            plot_topic_network(TopicModel((0,)), [0], ["a", "b"], np.eye(2))

    def test_network_small_samples(self):
        for count in (1, 2, 3):
            with self.subTest(count=count):
                fig = plot_topic_network(
                    TopicModel((0,)),
                    [0] * count,
                    ["text"] * count,
                    np.arange(count * 4).reshape(count, 4),
                )
                self.assertEqual(sum(len(t.x) for t in fig.data), count)


if __name__ == "__main__":
    unittest.main()
