import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from services.auth import AuthError, AuthService
from services.data_pipeline import DataSourceRegistry, DataValidationError, Observation
from services.recommendation import CropRecommender


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.auth = AuthService(Path(self.temp_dir.name) / "users.db")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_registration_and_login_use_hashed_passwords(self):
        user = self.auth.register("Ada Farmer", "ADA@example.com", "strongpass", "North field", "Spring")
        self.assertEqual(self.auth.login("ada@example.com", "strongpass").id, user.id)
        with self.assertRaises(AuthError):
            self.auth.login("ada@example.com", "wrongpass")

    def test_duplicate_email_is_rejected(self):
        self.auth.register("Ada", "ada@example.com", "strongpass", "Field", "Spring")
        with self.assertRaises(AuthError):
            self.auth.register("Another Ada", "ADA@example.com", "strongpass", "Field", "Spring")

    def test_reset_token_changes_password_once(self):
        self.auth.register("Ada", "ada@example.com", "strongpass", "Field", "Spring")
        token = self.auth.create_reset_token("ada@example.com")
        self.auth.reset_password(token, "newstrongpass")
        self.assertEqual(self.auth.login("ada@example.com", "newstrongpass").email, "ada@example.com")
        with self.assertRaises(AuthError):
            self.auth.reset_password(token, "anotherpass")


class RecommendationTests(unittest.TestCase):
    def test_data_source_registry_has_replaceable_kenya_sources(self):
        registry = DataSourceRegistry()
        keys = {source.key for source in registry.list()}
        self.assertIn("weather_kmd", keys)
        self.assertIn("weather_open_meteo", keys)
        self.assertIn("satellite_sentinel2", keys)
        self.assertIn("soil_soilgrids", keys)

    def test_observation_validation_rejects_untrusted_metadata(self):
        registry = DataSourceRegistry()
        now = datetime.now(timezone.utc)
        observation = Observation("weather_kmd", "Wrong provider", "temperature", 24, "C", now, now, "station", 0.9)
        with self.assertRaises(DataValidationError):
            registry.validate_observation(observation)

    def test_recommendation_uses_dataset_nearest_neighbors(self):
        recommender = CropRecommender(Path(__file__).parent / "Crop_recommendation.csv")
        result = recommender.recommend({"N": 90, "P": 42, "K": 43, "temperature": 20.88, "humidity": 82, "ph": 6.5, "rainfall": 203})
        self.assertEqual(result.crop, "Rice")

    def test_recommendation_rejects_invalid_observations(self):
        recommender = CropRecommender(Path(__file__).parent / "Crop_recommendation.csv")
        values = {"N": 90, "P": 42, "K": 43, "temperature": 20.88, "humidity": 82, "ph": 6.5, "rainfall": 203}
        values["humidity"] = 101
        with self.assertRaises(ValueError):
            recommender.recommend(values)

    def test_explainable_recommendation_includes_context_and_confidence(self):
        recommender = CropRecommender(Path(__file__).parent / "Crop_recommendation.csv")
        explanation = recommender.explain_recommendation({"N": 90, "P": 42, "K": 43, "temperature": 20.88, "humidity": 82, "ph": 6.5, "rainfall": 203})
        self.assertIn("Rice", explanation.crop)
        self.assertGreaterEqual(explanation.suitability, 0)
        self.assertLessEqual(explanation.suitability, 100)
        self.assertGreater(len(explanation.reasons), 0)
        self.assertGreater(len(explanation.data_confidence), 0)
        self.assertIn("why", explanation.summary.lower())

    def test_data_manager_exposes_provider_abstraction(self):
        recommender = CropRecommender(Path(__file__).parent / "Crop_recommendation.csv")
        self.assertTrue(hasattr(recommender.data_manager, "get_weather"))
        self.assertTrue(hasattr(recommender.data_manager, "get_soil"))

    def test_recommendation_history_tracks_changes_over_time(self):
        recommender = CropRecommender(Path(__file__).parent / "Crop_recommendation.csv")
        values = {"N": 90, "P": 42, "K": 43, "temperature": 20.88, "humidity": 82, "ph": 6.5, "rainfall": 203}
        record = recommender.record_recommendation(values, farm_id="farm-001", field_name="North field")
        history = recommender.get_recommendation_history("farm-001")
        self.assertEqual(record["farm_id"], "farm-001")
        self.assertGreater(len(history), 0)
        self.assertIn("crop", history[0])

    def test_recommendation_history_can_be_persisted_and_reloaded(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "recommendations.db"
            csv_path = Path(__file__).parent / "Crop_recommendation.csv"
            values = {"N": 90, "P": 42, "K": 43, "temperature": 20.88, "humidity": 82, "ph": 6.5, "rainfall": 203}
            first = CropRecommender(csv_path, database_path)
            first.record_recommendation(values, farm_id="farm-persistent", field_name="North field")
            second = CropRecommender(csv_path, database_path)
            history = second.get_recommendation_history("farm-persistent")
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["farm_id"], "farm-persistent")

    def test_alert_planning_and_freshness_are_available(self):
        recommender = CropRecommender(Path(__file__).parent / "Crop_recommendation.csv")
        values = {"N": 90, "P": 42, "K": 43, "temperature": 20.88, "humidity": 82, "ph": 6.5, "rainfall": 203}
        recommendation = recommender.recommend(values)
        alerts = recommender.generate_alerts(values, recommendation.crop)
        planting = recommender.calculate_planting_window(values, recommendation.crop)
        freshness = recommender.get_data_freshness()
        self.assertGreater(len(alerts), 0)
        self.assertIn("start", planting)
        self.assertIn("Weather", freshness)
        self.assertIn("severity", alerts[0])

    def test_crop_simulation_and_season_plan_are_available(self):
        recommender = CropRecommender(Path(__file__).parent / "Crop_recommendation.csv")
        values = {"N": 90, "P": 42, "K": 43, "temperature": 20.88, "humidity": 82, "ph": 6.5, "rainfall": 203}
        maize = recommender.simulate_crop(values, "maize")
        sorghum = recommender.simulate_crop(values, "sorghum")
        season = recommender.build_season_plan(values, "maize")
        self.assertIn("suitability", maize)
        self.assertIn("growing_period", maize)
        self.assertIn("planting", season)
        self.assertIn("harvest", season)
        self.assertGreater(maize["suitability"], 0)
        self.assertGreater(sorghum["suitability"], 0)

    def test_farm_health_score_and_risk_layer_are_available(self):
        recommender = CropRecommender(Path(__file__).parent / "Crop_recommendation.csv")
        values = {"N": 90, "P": 42, "K": 43, "temperature": 20.88, "humidity": 82, "ph": 6.5, "rainfall": 203}
        health = recommender.assess_farm_health(values, "rice")
        self.assertIn("overall_health", health)
        self.assertIn("water_stress", health)
        self.assertIn("risk_level", health)
        self.assertGreaterEqual(health["overall_health"], 0)
        self.assertLessEqual(health["overall_health"], 100)
        self.assertGreater(len(health["recommendations"]), 0)

    def test_operations_plan_prioritizes_field_actions(self):
        recommender = CropRecommender(Path(__file__).parent / "Crop_recommendation.csv")
        values = {"N": 90, "P": 42, "K": 43, "temperature": 20.88, "humidity": 82, "ph": 6.5, "rainfall": 203}
        plan = recommender.build_operations_plan(values, "rice")
        self.assertIn("irrigation", plan)
        self.assertIn("fertilization", plan)
        self.assertIn("pest_monitoring", plan)
        self.assertIn("yield_risk", plan)
        self.assertIn("priority", plan["irrigation"])
        self.assertGreater(len(plan["tasks"]), 0)


if __name__ == "__main__":
    unittest.main()
