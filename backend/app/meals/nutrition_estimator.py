import base64
import json
from typing import Optional, Protocol

import anthropic

from ..config import settings
from .models import PhotoEstimateOut

ESTIMATE_PROMPT = (
    "You are a nutrition estimation assistant. Look at this photo of a meal and "
    "estimate its nutritional content. Respond with ONLY a JSON object with keys: "
    "calories (number), protein_g (number), carbs_g (number), fat_g (number), "
    "confidence (number between 0 and 1), description (a short string describing "
    "what you see). No prose, no markdown fences — just the JSON object."
)

TEXT_ESTIMATE_PROMPT = (
    "You are a nutrition estimation assistant. A user described a meal they ate. "
    "Estimate its nutritional content from the description alone. Respond with "
    "ONLY a JSON object with keys: calories (number), protein_g (number), "
    "carbs_g (number), fat_g (number), confidence (number between 0 and 1 — be "
    "conservative, text descriptions are less precise than photos), description "
    "(a short string restating what you estimated). No prose, no markdown fences "
    "— just the JSON object.\n\nMeal description: "
)


class NutritionEstimator(Protocol):
    async def estimate(self, image_bytes: bytes, content_type: str) -> PhotoEstimateOut: ...
    async def estimate_from_text(self, description: str) -> PhotoEstimateOut: ...


class ClaudeVisionEstimator:
    def __init__(self, api_key: str, model: str):
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model

    async def estimate(self, image_bytes: bytes, content_type: str) -> PhotoEstimateOut:
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": content_type,
                                "data": base64.b64encode(image_bytes).decode("ascii"),
                            },
                        },
                        {"type": "text", "text": ESTIMATE_PROMPT},
                    ],
                }
            ],
        )
        data = json.loads(response.content[0].text)
        return PhotoEstimateOut(**data)

    async def estimate_from_text(self, description: str) -> PhotoEstimateOut:
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=300,
            messages=[{"role": "user", "content": TEXT_ESTIMATE_PROMPT + description}],
        )
        data = json.loads(response.content[0].text)
        return PhotoEstimateOut(**data)


class FakeNutritionEstimator:
    """Dev/test double: returns a fixed plausible estimate regardless of input."""

    async def estimate(self, image_bytes: bytes, content_type: str) -> PhotoEstimateOut:
        return PhotoEstimateOut(
            calories=450, protein_g=30, carbs_g=40, fat_g=15,
            confidence=0.5, description="fake estimate used because no ANTHROPIC_API_KEY is configured",
        )

    async def estimate_from_text(self, description: str) -> PhotoEstimateOut:
        return PhotoEstimateOut(
            calories=450, protein_g=30, carbs_g=40, fat_g=15,
            confidence=0.5, description="fake estimate used because no ANTHROPIC_API_KEY is configured",
        )


_estimator: Optional[NutritionEstimator] = None


def get_nutrition_estimator() -> NutritionEstimator:
    global _estimator
    if _estimator is None:
        _estimator = (
            ClaudeVisionEstimator(settings.anthropic_api_key, settings.anthropic_model)
            if settings.anthropic_api_key
            else FakeNutritionEstimator()
        )
    return _estimator
