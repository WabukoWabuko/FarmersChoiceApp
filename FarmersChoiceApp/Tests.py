import tempfile
import unittest
from pathlib import Path

from services.auth import AuthError, AuthService
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
    def test_recommendation_uses_dataset_nearest_neighbors(self):
        recommender = CropRecommender(Path(__file__).parent / "Crop_recommendation.csv")
        result = recommender.recommend({"N": 90, "P": 42, "K": 43, "temperature": 20.88, "humidity": 82, "ph": 6.5, "rainfall": 203})
        self.assertEqual(result.crop, "Rice")


if __name__ == "__main__":
    unittest.main()
