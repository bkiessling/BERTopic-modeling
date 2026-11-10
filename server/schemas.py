"""Validated HTTP request schemas, separate from domain configuration."""

from typing import Annotated
from pydantic import BaseModel, Field, SecretStr
from server.services.analysis.topic_naming import DEFAULT_NAMING_MODEL


class CleanRequest(BaseModel):
    text_columns: list[str]
    id_column: str = "ID generieren"
    sample_percentage: int = Field(100, ge=1, le=100)
    custom_stopwords: str = Field("", max_length=10000)


class WebVectorizer(BaseModel):
    # Web sliders are proportions. JSON has no integer/float distinction:
    # JavaScript serializes 1.0 as 1, while sklearn interprets int(1) as a count.
    ngram_range: tuple[int, int] = (1, 2)
    min_df: float = Field(0.001, gt=0, le=1)
    max_df: float = Field(1.0, gt=0, le=1)


class TrainRequest(BaseModel):
    params: dict


class NamingRequest(BaseModel):
    model: str = DEFAULT_NAMING_MODEL


class OutlierRequest(BaseModel):
    threshold: float = Field(0.05, ge=0, le=0.5)


class SessionKeyRequest(BaseModel):
    key: SecretStr


class TopicReductionRequest(BaseModel):
    target: int = Field(ge=1, strict=True)


class TopicMergeRequest(BaseModel):
    topics: list[Annotated[int, Field(strict=True, ge=0)]] = Field(min_length=2)


class TopicLabelRequest(BaseModel):
    topic: int = Field(ge=0, strict=True)
    label: str = Field(min_length=1, max_length=120)
