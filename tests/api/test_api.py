"""Real HTTP workflow with local embeddings; no external models or API costs."""

import io
import json
import time
import unittest
import tempfile
import os
from pathlib import Path
import zipfile
from unittest.mock import patch, Mock
import numpy as np
import pandas as pd
from bertopic.backend import BaseEmbedder
from fastapi.testclient import TestClient
from server.app import app
from server.runtime import spaces
from server.settings import key_binding
from server.services.modeling.configuration import TrainingConfig, ENGLISH_MODEL
from server.services.modeling.train_model import TrainingResult


class OfflineEncoder(BaseEmbedder):
    def encode(self, documents, **kwargs):
        rng = np.random.default_rng(42)
        return np.vstack(
            [np.eye(3)[i // 20] + rng.normal(0, 0.03, 3) for i in range(len(documents))]
        )


class WebApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.token = self.client.post("/api/workspaces").json()["id"]
        self.headers = {"X-Workspace-ID": self.token}

    def tearDown(self):
        spaces.pop(self.token, None)
        self.client.close()

    def upload(self, text, name="texts.csv"):
        return self.client.post(
            "/api/import", headers=self.headers, files={"file": (name, text, "text/csv")}
        )

    def wait(self):
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            value = self.client.get("/api/job", headers=self.headers).json()
            if value["status"] in ("completed", "failed"):
                return value
            time.sleep(0.05)
        self.fail("Job did not complete")

    def test_csv_cleaning_and_workspace_restoration(self):
        imported = self.upload(
            "id;text;extra\n1;Hallo Welt 123!;Weitere Wörter\n2; ;Noch ein Text\n"
        )
        self.assertEqual(imported.status_code, 200)
        self.assertEqual(imported.json()["delimiter"], ";")
        value = self.client.post(
            "/api/clean",
            headers=self.headers,
            json={
                "text_columns": ["text", "extra"],
                "id_column": "id",
                "custom_stopwords": "welt",
                "sample_percentage": 100,
            },
        )
        self.assertEqual(value.status_code, 200, value.text)
        self.assertEqual(value.json()["rows"], 3)
        self.assertEqual(value.json()["preview"][0]["text"], "hallo")
        restored = self.client.get("/api/workspace", headers=self.headers).json()
        self.assertEqual(restored["clean_result"]["rows"], 3)
        self.assertEqual(restored["text_columns"], ["text", "extra"])

    def test_xlsx_and_invalid_inputs(self):
        output = io.BytesIO()
        pd.DataFrame({"Text": ["Hallo Welt"]}).to_excel(output, index=False)
        value = self.client.post(
            "/api/import", headers=self.headers, files={"file": ("input.xlsx", output.getvalue())}
        )
        self.assertEqual(value.status_code, 200, value.text)
        self.assertEqual(value.json()["rows"], 1)
        self.assertEqual(
            self.client.post(
                "/api/clean", headers=self.headers, json={"text_columns": []}
            ).status_code,
            400,
        )
        self.assertEqual(self.client.get("/api/results", headers=self.headers).status_code, 409)
        self.assertEqual(
            self.client.get("/api/workspace", headers={"X-Workspace-ID": "unknown"}).status_code,
            404,
        )
        self.assertEqual(self.upload("x", "input.exe").status_code, 400)

    def test_credentials_stay_server_side(self):
        with patch(
            "server.routes.system.key_binding",
            return_value=("test-only-credential", "test-source"),
        ):
            value = self.client.get("/api/capabilities")
            self.assertTrue(value.json()["key_present"])
            self.assertNotIn("test-only-credential", value.text)
        self.assertEqual(
            self.client.post("/api/openai/check", json={"model": "gpt-4.1-mini"}).status_code, 422
        )

    def test_session_key_is_private_scoped_and_used_for_access_check(self):
        secret = "test-only-session-credential"
        with patch("server.routes.system.key_binding", return_value=("", "")):
            response = self.client.post(
                "/api/openai/key", headers=self.headers, json={"key": secret}
            )
            self.assertEqual(response.status_code, 200)
            self.assertNotIn(secret, response.text)
            own = self.client.get("/api/capabilities", headers=self.headers)
            self.assertTrue(own.json()["key_present"])
            self.assertNotIn(secret, own.text)
            self.assertFalse(self.client.get("/api/capabilities").json()["key_present"])
            self.assertNotIn(secret, self.client.get("/api/workspace", headers=self.headers).text)
            self.assertNotIn(secret, repr(spaces[self.token]))
            with patch("server.routes.system.check_model_access") as check:
                self.client.post(
                    "/api/openai/check", headers=self.headers, json={"model": "gpt-4.1-mini"}
                )
                check.assert_called_once_with(secret, "gpt-4.1-mini")
        invalid = self.client.post(
            "/api/openai/key", headers=self.headers, json={"key": "test key with spaces"}
        )
        self.assertEqual(invalid.status_code, 400)
        self.assertNotIn("test key with spaces", invalid.text)
        self.assertEqual(spaces[self.token].openai_key, secret)
        self.assertEqual(self.client.post("/api/openai/key", json={"key": secret}).status_code, 422)

    def test_project_credentials_override_global_and_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project, home = root / "project", root / "home"
            for folder in (project, home):
                (folder / ("config" if folder == project else ".config/bertopic-workbench")).mkdir(
                    parents=True
                )
            (project / "config/secrets.toml").write_text('OPENAI_API_KEY = "local-test-key"')
            (home / ".config/bertopic-workbench/secrets.toml").write_text(
                'BERTOPIC_OPENAI_API_KEY = "global-test-key"'
            )
            with (
                patch("server.settings.ROOT", project),
                patch("server.settings.Path.home", return_value=home),
                patch.dict(os.environ, {"BERTOPIC_OPENAI_API_KEY": "environment-test-key"}),
            ):
                self.assertEqual(key_binding()[0], "local-test-key")

    def test_javascript_integer_one_remains_a_proportion_on_large_corpus(self):
        text = pd.DataFrame({"text": ["katze hund tier"] * 1001}).to_csv(index=False)
        self.upload(text)
        self.client.post("/api/clean", headers=self.headers, json={"text_columns": ["text"]})
        params = TrainingConfig(ENGLISH_MODEL, "Englisch", representation_models=()).to_dict()
        params["vectorizer"]["max_df"] = 1  # exactly what JSON.stringify(1.0) sends

        def train_result(documents, config, encoder, on_progress):
            self.assertIsInstance(config.max_df, float)
            self.assertEqual(config.max_df, 1.0)
            self.assertEqual(config.validate(documents), [])
            model = Mock()
            model.topics_ = [0] * len(documents)
            info = pd.DataFrame(
                {
                    "Topic": [0],
                    "Count": [len(documents)],
                    "Name": ["0_tier"],
                    "Representation": [["tier"]],
                }
            )
            return TrainingResult(model, info, np.ones((len(documents), 3)), documents, config)

        with (
            patch("server.routes.modeling.encoder", return_value=Mock()),
            patch("server.routes.modeling.train_bertopic_model", side_effect=train_result),
        ):
            start = self.client.post("/api/train", headers=self.headers, json={"params": params})
            self.assertEqual(start.status_code, 200, start.text)
            self.assertEqual(self.wait()["status"], "completed")

    def test_training_charts_documents_export_and_failure_preservation(self):
        docs = [
            text + " " + str(i)
            for text in (
                "katze hund tier futter",
                "fussball sport stadion tor",
                "computer software daten technik",
            )
            for i in range(20)
        ]
        text = pd.DataFrame({"id": [i // 2 for i in range(60)], "text": docs}).to_csv(index=False)
        self.assertEqual(self.upload(text).status_code, 200)
        self.assertEqual(
            self.client.post(
                "/api/clean",
                headers=self.headers,
                json={"text_columns": ["text"], "id_column": "id"},
            ).status_code,
            200,
        )
        params = TrainingConfig(
            ENGLISH_MODEL,
            "Englisch",
            n_neighbors=5,
            n_components=2,
            min_cluster_size=5,
            ngram_range=(1, 1),
            min_df=0.001,
            max_df=1.0,
            representation_models=(),
        ).to_dict()
        with patch("server.routes.modeling.encoder", return_value=OfflineEncoder()):
            start = self.client.post("/api/train", headers=self.headers, json={"params": params})
            self.assertEqual(start.status_code, 200, start.text)
            self.assertEqual(start.json()["status"], "queued")
            job = self.wait()
        self.assertEqual(job["status"], "completed", job)
        result = self.client.get("/api/results", headers=self.headers).json()
        self.assertEqual(result["stats"]["documents"], 60)
        self.assertGreaterEqual(result["stats"]["topics"], 2)
        for kind in ("similarity", "bars", "network"):
            chart = self.client.get("/api/charts/" + kind, headers=self.headers)
            self.assertEqual(chart.status_code, 200, chart.text[:300])
            self.assertTrue(chart.json()["data"])
        selected_topic = result["topics"][0]["Thema"]
        filtered = self.client.get(
            f"/api/documents?topic={selected_topic}&sort=Textbeitrag&descending=true",
            headers=self.headers,
        ).json()
        self.assertTrue(filtered["rows"])
        self.assertTrue(all(row["Thema"] == selected_topic for row in filtered["rows"]))
        texts = [row["Textbeitrag"] for row in filtered["rows"]]
        self.assertEqual(texts, sorted(texts, reverse=True))
        examples = self.client.get(
            "/api/documents?representative=true", headers=self.headers
        ).json()
        self.assertGreater(examples["total"], 0)
        self.assertTrue(all(row["Repräsentativ"] for row in examples["rows"]))
        empty = self.client.get(
            "/api/documents?topic=999999&grouped=true", headers=self.headers
        ).json()
        self.assertEqual(empty["total"], 0)
        self.assertEqual(empty["rows"], [])
        self.assertEqual(
            self.client.get("/api/documents?sort=unknown", headers=self.headers).status_code, 400
        )
        bars = self.client.get(
            f"/api/charts/bars?topics={selected_topic}&top_words=3", headers=self.headers
        ).json()
        self.assertLessEqual(len(bars["data"][0]["x"]), 3)
        self.assertEqual(bars["data"][0]["marker"]["color"], "#0C1754")
        network = self.client.get("/api/charts/network", headers=self.headers).json()
        self.assertGreaterEqual(network["layout"]["height"], 700)
        grouped = self.client.get("/api/documents?grouped=true", headers=self.headers).json()
        self.assertEqual(grouped["total"], 30)
        searched = self.client.get("/api/documents?search=computer", headers=self.headers).json()
        self.assertEqual(searched["total"], 20)
        exported = self.client.get("/api/export", headers=self.headers)
        with zipfile.ZipFile(io.BytesIO(exported.content)) as archive:
            self.assertEqual(len(json.loads(archive.read("documents.json"))), 60)
        with patch(
            "server.routes.modeling.encoder", side_effect=ValueError("test encoder failure")
        ):
            self.client.post("/api/train", headers=self.headers, json={"params": params})
            self.assertEqual(self.wait()["status"], "failed")
        self.assertEqual(
            self.client.get("/api/results", headers=self.headers).json()["stats"]["documents"], 60
        )
        params["umap"]["n_components"] = 100
        self.assertEqual(
            self.client.post(
                "/api/train", headers=self.headers, json={"params": params}
            ).status_code,
            400,
        )


if __name__ == "__main__":
    unittest.main()
