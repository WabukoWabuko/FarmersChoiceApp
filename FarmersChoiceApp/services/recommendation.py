from __future__ import annotations

import csv
import json
import math
import sqlite3
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from services.data_pipeline import DataSourceRegistry

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
        self.sources = DataSourceRegistry()
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

    def get_source_status(self) -> list[dict[str, object]]:
        return [self.sources.status(source.key) for source in self.sources.list()]


class RecommendationStore:
    """Durable storage for recommendation history when a database is configured."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS recommendation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    farm_id TEXT NOT NULL,
                    field_name TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    crop TEXT NOT NULL,
                    suitability REAL NOT NULL,
                    confidence REAL NOT NULL,
                    sample_count INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    reasons_json TEXT NOT NULL,
                    data_confidence_json TEXT NOT NULL
                )
            """)

    @contextmanager
    def _connection(self):
        connection = sqlite3.connect(self.database_path)
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def save(self, record: dict[str, object]) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO recommendation_history
                (farm_id, field_name, timestamp, crop, suitability, confidence, sample_count, reason, reasons_json, data_confidence_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["farm_id"], record["field_name"], record["timestamp"], record["crop"],
                    record["suitability"], record["confidence"], record["sample_count"], record["reason"],
                    json.dumps(record["reasons"]), json.dumps(record["data_confidence"]),
                ),
            )

    def list(self, farm_id: str) -> list[dict[str, object]]:
        with self._connection() as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                "SELECT * FROM recommendation_history WHERE farm_id = ? ORDER BY id DESC",
                (farm_id,),
            ).fetchall()
        return [
            {
                "farm_id": row["farm_id"],
                "field_name": row["field_name"],
                "timestamp": row["timestamp"],
                "crop": row["crop"],
                "suitability": row["suitability"],
                "confidence": row["confidence"],
                "sample_count": row["sample_count"],
                "reason": row["reason"],
                "reasons": json.loads(row["reasons_json"]),
                "data_confidence": json.loads(row["data_confidence_json"]),
            }
            for row in rows
        ]


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
    def __init__(self, csv_path: str | Path, storage_path: str | Path | None = None) -> None:
        self.data_manager = DataManager()
        self.rows: list[dict[str, float | str]] = []
        self.farms: dict[str, FarmModel] = {}
        self.store = RecommendationStore(storage_path) if storage_path else None
        with Path(csv_path).open(newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                self.rows.append({**{key: float(row[key]) for key in FEATURES}, "label": row["label"]})
        if not self.rows:
            raise ValueError("Crop dataset is empty.")

    def recommend(self, values: dict[str, float]) -> Recommendation:
        if set(values) != set(FEATURES):
            raise ValueError("All crop inputs are required.")
        limits = {
            "N": (0, 200),
            "P": (0, 200),
            "K": (0, 250),
            "temperature": (-20, 60),
            "humidity": (0, 100),
            "ph": (0, 14),
            "rainfall": (0, 5000),
        }
        for feature, (minimum, maximum) in limits.items():
            try:
                value = float(values[feature])
            except (TypeError, ValueError) as error:
                raise ValueError(f"{feature} must be a number.") from error
            if not math.isfinite(value) or not minimum <= value <= maximum:
                raise ValueError(f"{feature} must be between {minimum} and {maximum}.")
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
        if self.store:
            self.store.save(record)
        return record

    def get_recommendation_history(self, farm_id: str) -> list[dict[str, object]]:
        if self.store:
            return self.store.list(farm_id)
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

    def assess_farm_health(self, values: dict[str, float], crop_name: str) -> dict[str, object]:
        rainfall = float(values.get("rainfall", 0.0))
        temperature = float(values.get("temperature", 0.0))
        humidity = float(values.get("humidity", 0.0))
        ph = float(values.get("ph", 6.5))
        nitrogen = float(values.get("N", 0.0))
        phosphorus = float(values.get("P", 0.0))
        potassium = float(values.get("K", 0.0))

        rainfall_score = max(0.0, min(100.0, 100.0 - abs(rainfall - 220.0) * 0.3))
        temp_score = max(0.0, min(100.0, 100.0 - abs(temperature - 25.0) * 4.0))
        humidity_score = max(0.0, min(100.0, 100.0 - abs(humidity - 70.0) * 0.65))
        ph_score = max(0.0, min(100.0, 100.0 - abs(ph - 6.5) * 25.0))
        nutrient_score = max(0.0, min(100.0, (nitrogen + phosphorus + potassium) / 3.0))

        overall_health = round((rainfall_score + temp_score + humidity_score + ph_score + nutrient_score) / 5.0, 1)

        if rainfall_score < 60:
            water_stress = "High"
        elif rainfall_score < 75:
            water_stress = "Moderate"
        else:
            water_stress = "Low"

        if overall_health >= 80:
            risk_level = "Low"
        elif overall_health >= 65:
            risk_level = "Moderate"
        else:
            risk_level = "High"

        recommendations: list[str] = []
        if water_stress != "Low":
            recommendations.append("Increase soil moisture monitoring and prepare irrigation support during the next dry spell.")
        if ph_score < 70:
            recommendations.append("Adjust pH balance before planting to improve nutrient uptake and root establishment.")
        if nutrient_score < 70:
            recommendations.append("Plan a nutrient top-up to correct nitrogen, phosphorus, or potassium imbalance.")
        if not recommendations:
            recommendations.append(f"Current field conditions are well aligned with {crop_name.title()} and require only routine monitoring.")

        return {
            "overall_health": overall_health,
            "water_stress": water_stress,
            "risk_level": risk_level,
            "rainfall_score": round(rainfall_score, 1),
            "temperature_score": round(temp_score, 1),
            "humidity_score": round(humidity_score, 1),
            "soil_ph_score": round(ph_score, 1),
            "nutrient_score": round(nutrient_score, 1),
            "recommendations": recommendations,
        }

    def build_operations_plan(self, values: dict[str, float], crop_name: str) -> dict[str, object]:
        health = self.assess_farm_health(values, crop_name)
        rainfall = float(values.get("rainfall", 0.0))
        temperature = float(values.get("temperature", 0.0))
        humidity = float(values.get("humidity", 0.0))
        nitrogen = float(values.get("N", 0.0))

        irrigation_priority = "high" if health["water_stress"] == "High" else "medium" if health["water_stress"] == "Moderate" else "low"
        irrigation = {
            "priority": irrigation_priority,
            "action": "Inspect irrigation and water the field within 24 hours." if irrigation_priority == "high" else "Check soil moisture before the next irrigation cycle.",
            "reason": "Rainfall is below the field's preferred moisture range." if rainfall < 200 else "Maintain a regular moisture check to avoid water stress.",
        }

        fertilizer_priority = "high" if health["nutrient_score"] < 55 else "medium" if health["nutrient_score"] < 70 else "low"
        fertilization = {
            "priority": fertilizer_priority,
            "action": "Apply a measured nutrient top-up after confirming the soil test." if fertilizer_priority != "low" else "Review the nutrient plan at the next field visit.",
            "reason": f"Average NPK signal is {health['nutrient_score']}/100.",
        }

        pest_priority = "high" if humidity >= 85 and temperature >= 25 else "medium" if humidity >= 75 else "low"
        pest_monitoring = {
            "priority": pest_priority,
            "action": "Scout leaves and stems for fungal or insect pressure this week." if pest_priority != "low" else "Continue weekly pest scouting.",
            "reason": "Warm, humid conditions can increase disease pressure." if pest_priority == "high" else "Current conditions support routine monitoring.",
        }

        yield_risk = "high" if health["overall_health"] < 60 else "moderate" if health["overall_health"] < 78 else "low"
        yield_risk_detail = {
            "level": yield_risk,
            "score": round(max(0.0, 100.0 - float(health["overall_health"])), 1),
            "reason": "Yield outlook is sensitive to unresolved water, temperature, or nutrient stress." if yield_risk != "low" else "Yield outlook is stable if the current field conditions persist.",
        }

        tasks = [
            {"category": "Irrigation", "priority": irrigation["priority"], "action": irrigation["action"]},
            {"category": "Fertilization", "priority": fertilization["priority"], "action": fertilization["action"]},
            {"category": "Pest monitoring", "priority": pest_monitoring["priority"], "action": pest_monitoring["action"]},
        ]
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda task: priority_order[task["priority"]])
        return {
            "crop": crop_name.title(),
            "irrigation": irrigation,
            "fertilization": fertilization,
            "pest_monitoring": pest_monitoring,
            "yield_risk": yield_risk_detail,
            "tasks": tasks,
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
    "DataSourceRegistry",
    "RecommendationStore",
    "FarmModel",
    "CropRecommender",
    "Recommendation",
    "RecommendationExplanation",
]