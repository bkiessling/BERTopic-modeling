"""Exercise the real encoder stack with tiny, local Safetensors weights."""
import tempfile
from pathlib import Path
import unittest
import numpy as np
from transformers import BertConfig, BertModel, BertTokenizerFast, Qwen3Config, Qwen3Model
from sentence_transformers import SentenceTransformer, models


class LocalEncoderTests(unittest.TestCase):
    def _encode_local(self, config, model_type, pooling='mean'):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tokens = ['[PAD]', '[UNK]', '[CLS]', '[SEP]', '[MASK]', 'cat', 'dog', 'computer', 'software']
            (root / 'vocab.txt').write_text('\n'.join(tokens), encoding='utf-8')
            BertTokenizerFast(vocab_file=str(root / 'vocab.txt')).save_pretrained(root)
            model_type(config).save_pretrained(root, safe_serialization=True)
            transformer = models.Transformer(
                str(root), model_kwargs={'use_safetensors': True, 'local_files_only': True},
                config_kwargs={'local_files_only': True}, processor_kwargs={'local_files_only': True},
            )
            encoder = SentenceTransformer(modules=[transformer, models.Pooling(16, pooling_mode=pooling)], device='cpu')
            embeddings = encoder.encode(['cat dog', 'computer software'], show_progress_bar=False)
            self.assertEqual(embeddings.shape, (2, 16))
            self.assertTrue(np.isfinite(embeddings).all())

    def test_safetensors_encoder_runs_without_model_download(self):
        config = BertConfig(vocab_size=9, hidden_size=16, num_hidden_layers=1,
                            num_attention_heads=2, intermediate_size=32, max_position_embeddings=32)
        self._encode_local(config, BertModel)

    def test_qwen3_architecture_runs_on_supported_torch_versions(self):
        config = Qwen3Config(vocab_size=9, hidden_size=16, num_hidden_layers=1,
                             num_attention_heads=2, num_key_value_heads=2, head_dim=8,
                             intermediate_size=32, max_position_embeddings=32,
                             bos_token_id=2, eos_token_id=3, pad_token_id=0)
        self._encode_local(config, Qwen3Model, pooling='lasttoken')
