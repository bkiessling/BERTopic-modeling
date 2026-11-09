"""Exercise the real encoder stack with tiny, local Safetensors weights."""
import tempfile
from pathlib import Path
import unittest
import numpy as np
from transformers import BertConfig, BertModel, BertTokenizerFast
from sentence_transformers import SentenceTransformer, models


class LocalEncoderTests(unittest.TestCase):
    def test_safetensors_encoder_runs_without_model_download(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tokens = ['[PAD]', '[UNK]', '[CLS]', '[SEP]', '[MASK]', 'cat', 'dog', 'computer', 'software']
            (root / 'vocab.txt').write_text('\n'.join(tokens), encoding='utf-8')
            BertTokenizerFast(vocab_file=str(root / 'vocab.txt')).save_pretrained(root)
            config = BertConfig(vocab_size=len(tokens), hidden_size=16,
                                num_hidden_layers=1, num_attention_heads=2,
                                intermediate_size=32, max_position_embeddings=32)
            BertModel(config).save_pretrained(root, safe_serialization=True)
            transformer = models.Transformer(
                str(root), model_kwargs={'use_safetensors': True, 'local_files_only': True},
                config_kwargs={'local_files_only': True}, processor_kwargs={'local_files_only': True},
            )
            encoder = SentenceTransformer(modules=[transformer, models.Pooling(16)], device='cpu')
            embeddings = encoder.encode(['cat dog', 'computer software'], show_progress_bar=False)
            self.assertEqual(embeddings.shape, (2, 16))
            self.assertTrue(np.isfinite(embeddings).all())
