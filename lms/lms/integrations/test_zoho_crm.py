from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import UnitTestCase

from lms.lms.integrations.zoho_crm import (
	get_access_token,
	is_enabled,
	sync_corporate_account,
	upsert_account,
)


def fake_settings(**overrides):
	defaults = {
		"enabled": 1,
		"client_id": "client-id",
		"api_domain": "https://www.zohoapis.com",
	}
	defaults.update(overrides)
	settings = frappe._dict(defaults)
	settings.get_password = MagicMock(side_effect=lambda field, raise_exception=True: defaults.get(field))
	return settings


class TestIsEnabled(UnitTestCase):
	@patch("lms.lms.integrations.zoho_crm.get_settings")
	def test_disabled_when_not_configured(self, mock_get_settings):
		mock_get_settings.return_value = fake_settings(enabled=0)
		self.assertFalse(is_enabled())

	@patch("lms.lms.integrations.zoho_crm.get_settings")
	def test_disabled_when_missing_secret(self, mock_get_settings):
		mock_get_settings.return_value = fake_settings(client_secret=None, refresh_token="token")
		self.assertFalse(is_enabled())

	@patch("lms.lms.integrations.zoho_crm.get_settings")
	def test_enabled_when_fully_configured(self, mock_get_settings):
		mock_get_settings.return_value = fake_settings(client_secret="secret", refresh_token="token")
		self.assertTrue(is_enabled())


class TestSyncCorporateAccount(UnitTestCase):
	@patch("lms.lms.integrations.zoho_crm.frappe.enqueue")
	@patch("lms.lms.integrations.zoho_crm.is_enabled")
	def test_skips_enqueue_when_disabled(self, mock_is_enabled, mock_enqueue):
		mock_is_enabled.return_value = False
		sync_corporate_account(frappe._dict({"name": "Acme Inc"}))
		mock_enqueue.assert_not_called()

	@patch("lms.lms.integrations.zoho_crm.frappe.enqueue")
	@patch("lms.lms.integrations.zoho_crm.is_enabled")
	def test_enqueues_job_when_enabled(self, mock_is_enabled, mock_enqueue):
		mock_is_enabled.return_value = True
		sync_corporate_account(frappe._dict({"name": "Acme Inc"}))
		mock_enqueue.assert_called_once()
		self.assertEqual(mock_enqueue.call_args.kwargs["corporate_account"], "Acme Inc")


class TestUpsertAccount(UnitTestCase):
	@patch("lms.lms.integrations.zoho_crm.get_access_token")
	def test_returns_none_without_access_token(self, mock_get_token):
		mock_get_token.return_value = None
		self.assertIsNone(upsert_account({"Account_Name": "Acme Inc"}))

	@patch("lms.lms.integrations.zoho_crm.requests.post")
	@patch("lms.lms.integrations.zoho_crm.get_settings")
	@patch("lms.lms.integrations.zoho_crm.get_access_token")
	def test_posts_with_bearer_token(self, mock_get_token, mock_get_settings, mock_post):
		mock_get_token.return_value = "token-123"
		mock_get_settings.return_value = fake_settings()
		mock_post.return_value = MagicMock(json=lambda: {"data": []})
		mock_post.return_value.raise_for_status = MagicMock()

		upsert_account({"Account_Name": "Acme Inc"})

		call_kwargs = mock_post.call_args.kwargs
		self.assertEqual(call_kwargs["headers"]["Authorization"], "Zoho-oauthtoken token-123")


class TestGetAccessToken(UnitTestCase):
	@patch("lms.lms.integrations.zoho_crm.frappe.cache")
	def test_returns_cached_token(self, mock_cache):
		mock_cache.return_value.get_value.return_value = "cached-token"
		self.assertEqual(get_access_token(), "cached-token")
