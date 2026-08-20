from uuid import UUID

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class SuggestionRequest(BaseModel):
    request: str | None = Field(default=None, max_length=500)
    source: Literal["pantry", "search", "hybrid"] = "pantry"
    number: int = Field(default=3, ge=1, le=3)
    candidate_count: int = Field(default=10, ge=1, le=20)

    @model_validator(mode="after")
    def require_request_for_search(self) -> "SuggestionRequest":
        if self.request is not None:
            self.request = self.request.strip() or None
        if self.source in {"search", "hybrid"} and not self.request:
            raise ValueError(f"request is required when source is '{self.source}'")
        return self


class MacroBudget(BaseModel):
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float


class SuggestedRecipe(BaseModel):
    recipe_id: UUID
    spoonacular_id: int
    title: str
    recipe_url: str
    image_url: str | None = None
    coverage_pct: float
    missing_ingredients: list[str]
    calories: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    macro_fit: bool
    macro_note: str
    reason: str


class SuggestionResponse(BaseModel):
    message: str
    source: Literal["pantry", "search", "hybrid"]
    remaining_budget: MacroBudget
    suggestions: list[SuggestedRecipe]


class LLMSelectedSuggestion(BaseModel):
    recipe_id: UUID
    reason: str = Field(min_length=1, max_length=500)


class LLMSelectionResponse(BaseModel):
    selections: list[LLMSelectedSuggestion]
