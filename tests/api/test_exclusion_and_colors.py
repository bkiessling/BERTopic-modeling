"""Visibility must be consistent across all outputs; colors must not cycle after six topics."""

import io
import json
import unittest
import zipfile
from unittest.mock import Mock
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient
from server.app import app
from server.runtime import spaces
from server.services.analysis.state import AnalysisState
from server.services.modeling.train_model import TrainingResult
from server.services.modeling.configuration import TrainingConfig, ENGLISH_MODEL
from server.services.viz.colors import topic_colors


class ExclusionAndColorTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.token = self.client.post("/api/workspaces").json()["id"]
        self.headers = {"X-Workspace-ID": self.token}
        topics = [-1, *range(32)]
        info = pd.DataFrame(
            {
                "Topic": topics,
                "Name": [f"topic_{t}" for t in topics],
                "Count": [1] * 33,
                "Representation": [[f"word{t}"] for t in topics],
            }
        )
        model = Mock(topics_=topics, topic_embeddings_=np.eye(33), representative_docs_={})
        model.get_topic_info.return_value = info
        model.get_topic.side_effect = lambda topic: [(f"word{topic}", 1.0)]
        self.analysis = AnalysisState(
            TrainingResult(
                model,
                info,
                np.eye(33),
                [f"text {t}" for t in topics],
                TrainingConfig(ENGLISH_MODEL, "Englisch"),
            ),
            list(range(33)),
        )
        spaces[self.token].analysis = self.analysis
        spaces[self.token].coordinates = np.arange(66).reshape(33, 2)

    def tearDown(self):
        spaces.pop(self.token, None)
        self.client.close()

    def test_more_than_six_unique_stable_network_colors(self):
        chart = self.client.get("/api/charts/network", headers=self.headers).json()
        colors = [trace["marker"]["color"] for trace in chart["data"]]
        self.assertEqual(len(colors), 33)
        self.assertEqual(len(set(colors)), 33)
        self.assertEqual(chart["data"][0]["marker"]["color"], "#8A94A6")
        self.assertEqual(chart["data"][0]["visible"], "legendonly")
        all_colors = topic_colors(range(100))
        self.assertEqual(len(set(all_colors.values())), 100)
        self.assertEqual(topic_colors([4, 20]), {topic: all_colors[topic] for topic in (4, 20)})

    def test_exclusion_filters_every_output_and_can_be_restored(self):
        original = list(self.analysis.result.model.topics_)
        self.analysis.set_manual_topic_name(4, "Hidden topic label")
        response = self.client.post(
            "/api/topics/exclude", headers=self.headers, json={"topics": [4]}
        )
        self.assertEqual(response.status_code, 200, response.text)
        value = self.client.get("/api/results", headers=self.headers).json()
        self.assertEqual(value["stats"]["documents"], 32)
        self.assertEqual(value["stats"]["topics"], 31)
        self.assertEqual(value["excluded_topics"][0]["Topic"], 4)
        self.assertNotIn(4, [row["Thema"] for row in value["topics"]])
        docs = self.client.get("/api/documents", headers=self.headers).json()
        self.assertEqual(docs["total"], 32)
        self.assertTrue(all(row["Thema"] != 4 for row in docs["rows"]))
        self.assertEqual(list(docs["rows"][0])[:4], ["ID", "Thema", "Themenname", "Textbeitrag"])
        network = self.client.get("/api/charts/network", headers=self.headers).json()
        self.assertEqual(len(network["data"]), 32)
        self.assertTrue(all(not trace["name"].startswith("4 ·") for trace in network["data"]))
        self.assertEqual(
            self.client.get("/api/charts/bars?topics=4", headers=self.headers).status_code, 400
        )
        similarity = self.client.get("/api/charts/similarity", headers=self.headers).json()
        self.assertTrue(all(not name.startswith("4_") for name in similarity["data"][0]["x"]))
        with zipfile.ZipFile(
            io.BytesIO(self.client.get("/api/export", headers=self.headers).content)
        ) as archive:
            self.assertEqual(len(json.loads(archive.read("documents.json"))), 32)
            self.assertNotIn("Hidden topic label", archive.read("manifest.json").decode())
            self.assertEqual(
                json.loads(archive.read("manifest.json"))["metadata"]["excluded_topics"], [4]
            )
        for route, body in (
            ("/api/topics/reduce", {"target": 2}),
            ("/api/topics/merge", {"topics": [0, 1]}),
            ("/api/outliers", {}),
        ):
            self.assertEqual(
                self.client.post(route, headers=self.headers, json=body).status_code, 409
            )
        self.assertEqual(self.analysis.result.model.topics_, original)
        self.assertEqual(
            self.client.post("/api/topics/include-all", headers=self.headers, json={}).status_code,
            200,
        )
        self.assertEqual(
            self.client.get("/api/documents", headers=self.headers).json()["total"], 33
        )
        self.assertEqual(self.analysis.excluded_topics, set())

    def test_reject_invalid_or_all_topic_exclusion(self):
        for topics in ([999], [-1, *range(32)]):
            self.assertEqual(
                self.client.post(
                    "/api/topics/exclude", headers=self.headers, json={"topics": topics}
                ).status_code,
                400,
            )
        self.assertEqual(self.analysis.excluded_topics, set())
