from typing import Literal

from pydantic import BaseModel, Field


class StoreDesign(BaseModel):
    store_name: str = Field(min_length=2, max_length=100)
    store_description: str = Field(min_length=10, max_length=1000)
    hero_title: str = Field(min_length=2, max_length=100)
    footer_tagline: str = Field(min_length=2, max_length=200)
    primary_color: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    secondary_color: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    style: str = Field(min_length=2, max_length=150)


class ProductAnalysis(BaseModel):
    suggested_category: str = Field(
        min_length=2,
        max_length=100,
    )
    description: str = Field(
        min_length=10,
        max_length=1500,
    )
    key_features: list[str] = Field(
        max_length=10,
    )
    search_keywords: list[str] = Field(
        max_length=15,
    )
    missing_information: list[str] = Field(
        max_length=10,
    )
    clarification_questions: list[str] = Field(
        max_length=5,
    )
    relevance_status: Literal[
        "relevant",
        "irrelevant",
        "needs_review",
    ]
    relevance_reason: str = Field(
        min_length=2,
        max_length=500,
    )
    relevance_confidence: Literal[
        "high",
        "medium",
        "low",
    ]
