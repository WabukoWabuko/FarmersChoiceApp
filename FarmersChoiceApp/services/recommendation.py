from __future__ import annotations

import csv
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
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


class FarmModel:
    """Simple in-memory representation of a farm's current digital twin state."""

    def __init__(self, farm_id: str, field_name: str) -> None:
        self.farm_id = farm_id
        self.field_name = field_name
        self.current_crop: str | None = None
        self.recommendation_history: list[dict[str, object]] = []
        self.alerts: list[str] = [
            "Conditions are becoming suitable for planting.",
            "A brief dry spell remains possible in the coming week.",
        ]

    def add_recommendation(self, recommendation: dict[str, object]) -> dict[str, object]:
        self.recommendation_history.append(recommendation)
        self.current_crop = str(recommendation.get("crop", self.current_crop))
        return recommendation


class CropRecommender:
    def __init__(self, csv_path: str | Path) -> None:
        self.data_manager = DataManager()
        self.rows: list[dict[str, float | str]] = []
        self.farms: dict[str, FarmModel] = {}
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

    def record_recommendation(self, values: dict[str, float], farm_id: str, field_name: str, reason: str | None = None) -> dict[str, object]:
        recommendation = self.recommend(values)
        explanation = self.explain_recommendation(values)
        record = {
            "farm_id": farm_id,
            "field_name": field_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "crop": recommendation.crop,
            "suitability": recommendation.suitability,
            "confidence": recommendation.confidence,
            "sample_count": recommendation.sample_count,
            "reason": reason or explanation.summary,
            "reasons": explanation.reasons,
            "data_confidence": explanation.data_confidence,
        }
        if farm_id not in self.farms:
            self.farms[farm_id] = FarmModel(farm_id, field_name)
        self.farms[farm_id].add_recommendation(record)
        return record

    def get_recommendation_history(self, farm_id: str) -> list[dict[str, object]]:
        return self.farms.get(farm_id, FarmModel(farm_id, "default")).recommendation_history

    def get_data_freshness(self) -> dict[str, dict[str, object]]:
        return {
            "Weather": {"updated_minutes_ago": 37, "status": "fresh", "confidence": 94},
            "Satellite": {"updated_days_ago": 2, "status": "fresh", "confidence": 88},
            "Market": {"updated_hours_ago": 5, "status": "fresh", "confidence": 77},
            "Soil": {"dataset_revision": "2026-03", "status": "periodic", "confidence": 81},
            "Elevation": {"status": "static", "confidence": 98},
            "Crop knowledge": {"version": "2026.09", "status": "versioned", "confidence": 92},
        }

    def generate_alerts(self, values: dict[str, float], crop_name: str) -> list[dict[str, str]]:
        alerts: list[dict[str, str]] = []
        rainfall = float(values.get("rainfall", 0.0))
        temperature = float(values.get("temperature", 0.0))
        if rainfall < 200:
            alerts.append({
                "severity": "warning",
                "title": "Dry spell risk",
                "message": "Rainfall is below the preferred range for the current recommendation.",
            })
        if temperature > 32:
            alerts.append({
                "severity": "advisory",
                "title": "Heat stress watch",
                "message": "Higher-than-normal temperatures may affect crop development during the growing window.",
            })
        if rainfall > 300 and temperature > 25:
            alerts.append({
                "severity": "informational",
                "title": "Moisture surplus",
                "message": "Moisture and warmth suggest a need for drainage monitoring.",
            })
        if not alerts:
            alerts.append({
                "severity": "informational",
                "title": "Conditions stable",
                "message": f"Current conditions remain favourable for {crop_name}.",
            })
        return alerts

    def calculate_planting_window(self, values: dict[str, float], crop_name: str) -> dict[str, str]:
        rainfall = float(values.get("rainfall", 0.0))
        temperature = float(values.get("temperature", 0.0))
        if crop_name.lower() == "rice":
            return {
                "start": "14 October",
                "end": "28 October",
                "best_window": "18–22 October",
                "confidence": "82%",
                "reason": "Rainfall and temperature show a suitable start to the growing cycle.",
            }
        if crop_name.lower() == "maize":
            return {
                "start": "8 October",
                "end": "20 October",
                "best_window": "12–16 October",
                "confidence": "80%",
                "reason": "Temperatures are supportive, with moderate rainfall for establishment.",
            }
        if rainfall < 200:
            return {
                "start": "15 October",
                "end": "30 October",
                "best_window": "20–24 October",
                "confidence": "74%",
                "reason": "A slightly later planting window reduces moisture stress risk.",
            }
        return {
            "start": "10 October",
            "end": "22 October",
            "best_window": "14–18 October",
            "confidence": "81%",
            "reason": "Conditions are generally suitable for early planting across the season.",
        }

    def simulate_crop(self, values: dict[str, float], crop_name: str) -> dict[str, object]:
        rainfall = float(values.get("rainfall", 0.0))
        temperature = float(values.get("temperature", 0.0))
        humidity = float(values.get("humidity", 0.0))
        crop_key = crop_name.lower()

        if crop_key == "maize":
            suitability = 82 if rainfall > 180 and temperature < 32 else 74
            growing_period = "~4 months"
            water_requirement = "Medium–high"
            weather_risk = "Moderate"
            main_risk = "Late-season rainfall decline"
        elif crop_key == "sorghum":
            suitability = 91 if rainfall >= 150 and temperature < 35 else 85
            growing_period = "~3–4 months"
            water_requirement = "Low"
            weather_risk = "Low"
            main_risk = "Heat stress during very dry periods"
        elif crop_key == "rice":
            suitability = 88 if rainfall > 220 and humidity > 75 else 79
            growing_period = "~4–5 months"
            water_requirement = "High"
            weather_risk = "Moderate"
            main_risk = "Flooding or excessive waterlogging"
        else:
            suitability = 76
            growing_period = "~3–4 months"
            water_requirement = "Medium"
            weather_risk = "Moderate"
            main_risk = "Seasonal rainfall variability"

        return {
            "crop": crop_name.title(),
            "suitability": suitability,
            "growing_period": growing_period,
            "water_requirement": water_requirement,
            "weather_risk": weather_risk,
            "estimated_yield": "1,000–1,400 kg",
            "estimated_revenue": "KSh 60,000–140,000",
            "main_risk": main_risk,
            "soil_score": max(60, min(95, int((rainfall / 3) + (humidity / 2) - 20))),
            "temperature_score": max(50, min(96, int(temperature * 2 + 30))),
        }

    def build_season_plan(self, values: dict[str, float], crop_name: str) -> dict[str, str]:
        window = self.calculate_planting_window(values, crop_name)
        crop_key = crop_name.lower()
        if crop_key == "rice":
            return {
                "planting": "14–28 October",
                "emergence": "29 Oct–12 Nov",
                "development": "Nov–Jan",
                "fertilizer": "Late Oct and mid-Dec",
                "monitoring": "Weekly from emergence",
                "harvest": "March–April",
                "post_harvest": "Drying and storage",
            }
        if crop_key == "maize":
            return {
                "planting": "8–20 October",
                "emergence": "18 Oct–02 Nov",
                "development": "Nov–Jan",
                "fertilizer": "Early Nov and early Jan",
                "monitoring": "Every 10 days",
                "harvest": "Feb–Mar",
                "post_harvest": "Shelling and drying",
            }
        return {
            "planting": window["start"] + "–" + window["end"],
            "emergence": "2–3 weeks after planting",
            "development": "One month to maturity",
            "fertilizer": "At planting and mid-cycle",
            "monitoring": "Fortnightly",
            "harvest": "Late season",
            "post_harvest": "Storage and market check",
        }


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
    "FarmModel",
    "CropRecommender",
    "Recommendation",
    "RecommendationExplanation",
]