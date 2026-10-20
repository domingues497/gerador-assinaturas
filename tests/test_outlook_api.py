import os
import unittest
from unittest.mock import patch

from app import criar_app


class OutlookApiTests(unittest.TestCase):
    def setUp(self):
        self.app = criar_app()
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()

    def test_health_does_not_expose_sensitive_settings(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("GERADOR_ENTRA_TENANT_ID", None)
            os.environ.pop("GERADOR_ENTRA_CLIENT_ID", None)
            os.environ.pop("GERADOR_ENTRA_AUDIENCE", None)
            response = self.client.get("/api/outlook/health")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["status"], "configuration_required")
        self.assertNotIn("tenant_id", payload)
        self.assertNotIn("client_id", payload)

    def test_signature_requires_bearer_token(self):
        response = self.client.get("/api/outlook/signature")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()["error"], "unauthorized")

    def test_distribution_page_loads(self):
        response = self.client.get("/distribuicao-outlook/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Distribuição remota para Outlook".encode(), response.data)


if __name__ == "__main__":
    unittest.main()
