
from pydantic import BaseModel, Field, field_validator


class SuggestedCategory(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(default="", max_length=300)

    @field_validator("name", "description")
    @classmethod
    def strip_whitespace(cls, value):
        return value.strip()


class CategorySuggestions(BaseModel):
    categories: list[SuggestedCategory] = Field(
        default_factory=list,
        max_length=10,
    )

    @field_validator("categories")
    @classmethod
    def validate_unique_names(cls, categories):
        names = [category.name.casefold() for category in categories]

        if len(names) != len(set(names)):
            raise ValueError("Category names must be unique.")

        return categories
