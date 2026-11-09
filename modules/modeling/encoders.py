"""Build encoders with task prompts shared by training and BERTopic representations."""

from sentence_transformers import SentenceTransformer
from modules.modeling.configuration import embedding_settings


def build_encoder(model_name, device="cpu"):
    prompt = embedding_settings(model_name)["prompt"]
    options = (
        {"prompts": {"clustering": prompt}, "default_prompt_name": "clustering"} if prompt else {}
    )
    return SentenceTransformer(
        model_name,
        device=device,
        trust_remote_code=False,
        model_kwargs={"use_safetensors": True},
        **options,
    )
