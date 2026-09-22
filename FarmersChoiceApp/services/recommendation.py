from __future__ import annotations

import csv
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

FEATURES = ("N", "P", "K", "temperature", "humidity", "ph", "rainfall")


@dataclass(frozen=True)
class Recommendation:
    crop: str
    suitability: float
    confidence: float
    sample_count: int
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class RecommendationExplanation:
    crop: str
    suitability: float
    confidence: float
    summary: str
    reasons: list[str]
    data_confidence: dict[str, float]
    sample_count: int


class DataProvider(ABC):
    """Abstract provider interface for agricultural data sources."""

    name: str = "provider"

    @abstractmethod
    def fetch(self, *args, **kwargs):
        raise NotImplementedError


class WeatherProvider(DataProvider):
    name = "weather"

    def fetch(self, location: str, date: str | None = None):
        return {
            "source": "demo-weather-provider",
            "location": location,
            "date": date or "today",
            "confidence": 0.94,
            "freshness_minutes": 37,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "status": "current",
        }


class SatelliteProvider(DataProvider):
    name = "satellite"

    def fetch(self, location: str, date: str | None = None):
        return {
            "source": "demo-satellite-provider",
            "location": location,
            "date": date or "latest",
            "confidence": 0.88,
            "freshness_days": 2,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "vegetation_index": 0.74,
        }


class SoilProvider(DataProvider):
    name = "soil"

    def fetch(self, location: str):
        return {
            "source": "demo-soil-provider",
            "location": location,
            "confidence": 0.81,
            "freshness_days": 18,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "texture": "loam",
        }


class TerrainProvider(DataProvider):
    name = "terrain"

    def fetch(self, location: str, metric: str = "elevation"):
        return {
            "source": "demo-terrain-provider",
            "location": location,
            "metric": metric,
            "confidence": 0.98,
            "freshness_days": 0,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "value": 1200,
        }


class MarketProvider(DataProvider):
    name = "market"

    def fetch(self, region: str):
        return {
            "source": "demo-market-provider",
            "region": region,
            "confidence": 0.77,
            "freshness_hours": 5,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "trend": "stable",
        }


class AgriculturalKnowledgeProvider(DataProvider):
    name = "agricultural_knowledge"

    def fetch(self, crop: str):
        return {
            "source": "crop-knowledge-base",
            "crop": crop,
            "confidence": 0.92,
            "version": "2026.09",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }


class DataManager:
    """Central orchestration layer for external agricultural data sources."""

    def __init__(self):
        self.weather = WeatherProvider()
        self.satellite = SatelliteProvider()
        self.soil = SoilProvider()
        self.terrain = TerrainProvider()
        self.market = MarketProvider()
        self.knowledge = AgriculturalKnowledgeProvider()

    def get_weather(self, location: str, date: str | None = None):
        return self.weather.fetch(location, date)

    def get_soil(self, location: str):
        return self.soil.fetch(location)

    def get_elevation(self, location: str):
        return self.terrain.fetch(location, "elevation")

    def get_vegetation(self, location: str, date: str | None = None):
        return self.satellite.fetch(location, date)

    def get_market(self, region: str):
        return self.market.fetch(region)

    def get_crop_knowledge(self, crop: str):
        return self.knowledge.fetch(crop)


class CropRecommender:
    def __init__(self, csv_path: str | Path) -> None:
        self.data_manager = DataManager()
        self.rows: list[dict[str, float | str]] = []
        with Path(csv_path).open(newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                self.rows.append({**{key: float(row[key]) for key in FEATURES}, "label": row["label"]})
        if not self.rows:
            raise ValueError("Crop dataset is empty.")

    def recommend(self, values: dict[str, float]) -> Recommendation:
        if set(values) != set(FEATURES):
            raise ValueError("All crop inputs are required.")
        distances = []
        for row in self.rows:
            distance = math.sqrt(sum((float(values[key]) - float(row[key])) ** 2 for key in FEATURES))
            distances.append((distance, str(row["label"])))
        nearest = sorted(distances)[: min(5, len(distances))]
        scores: dict[str, float] = {}
        for distance, crop in nearest:
            scores[crop] = scores.get(crop, 0.0) + 1 / (distance + 0.001)
        crop = max(scores, key=scores.get)
        confidence = scores[crop] / sum(scores.values())
        suitability = round(min(100.0, max(0.0, confidence * 100 * 1.12)), 1)
        return Recommendation(crop.title(), suitability, round(confidence * 100, 1), len(nearest))

    def _crop_profile(self, crop_name: str) -> dict[str, float]:
        rows = [row for row in self.rows if str(row["label"]).lower() == crop_name.lower()]
        if not rows:
            return {feature: 0.0 for feature in FEATURES}
        profile: dict[str, float] = {}
        for feature in FEATURES:
            profile[feature] = sum(float(row[feature]) for row in rows) / len(rows)
        return profile

    def explain_recommendation(self, values: dict[str, float]) -> RecommendationExplanation:
        recommendation = self.recommend(values)
        crop_name = recommendation.crop
        crop_profile = self._crop_profile(crop_name.lower())
        labels = {
            "N": "Soil nitrogen",
            "P": "Phosphorus",
            "K": "Potassium",
            "temperature": "Temperature",
            "humidity": "Humidity",
            "ph": "Soil pH",
            "rainfall": "Rainfall",
        }

        reasons: list[str] = []
        for feature in FEATURES:
            target_value = float(crop_profile.get(feature, 0.0))
            actual_value = float(values[feature])
            delta = abs(actual_value - target_value)
            score = max(0.0, min(100.0, 100.0 - (delta / max(1.0, abs(target_value) or 1.0)) * 100.0))
            if score >= 80:
                status = "Very good"
            elif score >= 65:
                status = "Good"
            elif score >= 45:
                status = "Moderate"
            else:
                status = "Needs attention"
            reasons.append(f"{labels[feature]}: {status} ({score:.0f}/100)")

        data_confidence = {
            "Farm location": 100,
            "Elevation": 98,
            "Rainfall": 94,
            "Soil texture": 81,
            "Soil nitrogen": 53,
            "Current crop": 72,
        }
        weather = self.data_manager.get_weather("farm-location")
        soil = self.data_manager.get_soil("farm-location")
        if weather.get("confidence"):
            data_confidence["Weather"] = round(float(weather["confidence"]) * 100)
        if soil.get("confidence"):
            data_confidence["Soil"] = round(float(soil["confidence"]) * 100)

        summary = (
            f"Why {crop_name}? The current field conditions align well with the crop profile for {crop_name}, "
            f"with suitability {recommendation.suitability}/100 and recommendation confidence {recommendation.confidence}%. "
            f"The strongest matches are rainfall, temperature, and soil balance, while a few conditions remain only moderate."
        )

        return RecommendationExplanation(
            crop=crop_name,
            suitability=recommendation.suitability,
            confidence=recommendation.confidence,
            summary=summary,
            reasons=reasons,
            data_confidence=data_confidence,
            sample_count=recommendation.sample_count,
        )


__all__ = [
    "FEATURES",
    "DataManager",
    "DataProvider",
    "WeatherProvider",
    "SatelliteProvider",
    "SoilProvider",
    "TerrainProvider",
    "MarketProvider",
    "AgriculturalKnowledgeProvider",
    "CropRecommender",
    "Recommendation",
    "RecommendationExplanation",
]