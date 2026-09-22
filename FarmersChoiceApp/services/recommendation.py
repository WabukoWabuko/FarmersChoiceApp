from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

FEATURES = ("N", "P", "K", "temperature", "humidity", "ph", "rainfall")


@dataclass(frozen=True)
class Recommendation:
    crop: str
    confidence: float
    sample_count: int


class CropRecommender:
    def __init__(self, csv_path: str | Path) -> None:
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
        return Recommendation(crop.title(), round(confidence * 100, 1), len(nearest))