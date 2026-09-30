import unittest
from pathlib import Path
from app.services.settings_service import SettingsService, _mask_key

class TestSettingsService(unittest.TestCase):

    def setUp(self):
        self.test_storage = Path(__file__).parent / "test_settings.json"
        if self.test_storage.exists():
            self.test_storage.unlink()
        self.service = SettingsService(storage_path=self.test_storage)

    def tearDown(self):
        if self.test_storage.exists():
            self.test_storage.unlink()

    def test_mask_key(self):
        self.assertEqual(_mask_key(""), "")
        self.assertEqual(_mask_key("short"), "****")
        self.assertEqual(_mask_key("AIzaSy1234567890abcdef"), "AIzaSy...cdef")

    def test_get_and_update_settings(self):
        settings = self.service.get_settings()
        self.assertIn("chat_provider", settings)
        self.assertIn("gemini_model", settings)

        updated = self.service.update_settings({
            "chat_provider": "openai",
            "openai_model": "gpt-4o-mini",
            "openai_api_key": "sk-1234567890abcdefghij",
            "temperature": 0.7,
            "top_k": 8,
        })
        self.assertEqual(updated["chat_provider"], "openai")
        self.assertEqual(updated["openai_model"], "gpt-4o-mini")
        self.assertEqual(updated["temperature"], 0.7)
        self.assertEqual(updated["top_k"], 8)
        self.assertTrue(updated["has_openai_key"])
        self.assertEqual(updated["openai_api_key_masked"], "sk-123...ghij")

if __name__ == "__main__":
    unittest.main()
