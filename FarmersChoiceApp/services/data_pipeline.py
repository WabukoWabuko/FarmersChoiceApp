from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any


@dataclass(frozen=True)
class SourceSpec:
    key: str
    intelligence: str
    provider: str
    update_frequency: str
    resolution: str
    cost: str
    default_confidence: float
    stale_after: timedelta
    environment_variable: str | None = None


@dataclass(frozen=True)
class Observation:
    source: str
    provider: str
    variable: str
    value: float
    unit: str
    observed_at: datetime
    fetched_at: datetime
    resolution: str
    confidence: float
    quality_flags: tuple[str, ...] = ()
    geometry: dict[str, Any] | None = None

    @property
    def freshness(self) -> str:
        age = datetime.now(timezone.utc) - self.fetched_at
        return "fresh" if age <= timedelta(days=1) else "stale"


class DataValidationError(ValueError):
    pass


class DataSourceRegistry:
    """Central catalog for replaceable Kenya-first intelligence sources."""

    def __init__(self) -> None:
        self._sources = {
            spec.key: spec
            for spec in (
                SourceSpec("weather_kmd", "Weather", "Kenya Meteorological Department", "15 min", "station/grid", "contract", 0.9, timedelta(hours=3), "KMD_API_KEY"),
                SourceSpec("weather_open_meteo", "Weather", "Open-Meteo", "hourly", "1-11 km grid", "free tier", 0.75, timedelta(hours=6)),
                SourceSpec("rainfall_chirps", "Rainfall", "CHIRPS", "daily", "5 km grid", "open", 0.8, timedelta(days=3)),
                SourceSpec("satellite_sentinel2", "Satellite", "Copernicus Sentinel-2", "3-5 days", "10 m", "open", 0.88, timedelta(days=10)),
                SourceSpec("soil_soilgrids", "Soil", "ISRIC SoilGrids", "versioned", "250 m", "open", 0.65, timedelta(days=365)),
                SourceSpec("terrain_copernicus_dem", "Terrain", "Copernicus DEM", "static", "30 m", "open", 0.9, timedelta(days=3650)),
                SourceSpec("market_kamis", "Market", "KAMIS", "daily", "market/commodity", "verify", 0.7, timedelta(days=3), "KAMIS_API_KEY"),
                SourceSpec("knowledge_kalro", "Agronomy", "KALRO and county extension", "versioned", "county/crop", "partner", 0.8, timedelta(days=365), "KALRO_API_KEY"),
            )
        }

    def get(self, key: str) -> SourceSpec:
        try:
            return self._sources[key]
        except KeyError as error:
            raise KeyError(f"Unknown data source: {key}") from error

    def list(self) -> list[SourceSpec]:
        return list(self._sources.values())

    def status(self, key: str, fetched_at: datetime | None = None) -> dict[str, object]:
        source = self.get(key)
        timestamp = fetched_at or datetime.now(timezone.utc)
        age = datetime.now(timezone.utc) - timestamp
        return {
            "source": source.key,
            "provider": source.provider,
            "status": "stale" if age > source.stale_after else "fresh",
            "confidence": source.default_confidence,
            "resolution": source.resolution,
            "age_seconds": max(0, int(age.total_seconds())),
        }

    def validate_observation(self, observation: Observation) -> Observation:
        source = self.get(observation.source)
        if observation.provider != source.provider:
            raise DataValidationError("Observation provider does not match its source catalog entry.")
        if not observation.variable.strip() or not observation.unit.strip():
            raise DataValidationError("Observation variable and unit are required.")
        if not 0 <= observation.confidence <= 1:
            raise DataValidationError("Observation confidence must be between 0 and 1.")
        if observation.observed_at.tzinfo is None or observation.fetched_at.tzinfo is None:
            raise DataValidationError("Observation timestamps must include timezone information.")
        return observation


__all__ = ["DataSourceRegistry", "DataValidationError", "Observation", "SourceSpec"]