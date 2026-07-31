# Not runnable in an environment without python3-saml and a Frappe site installed
# (see module docstring in saml_sso.py) — kept as executable documentation of the
# expected behavior; run for real once both are available.

from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import UnitTestCase

from lms.lms.integrations.saml_sso import _first, _resolve_user, is_enabled


def fake_settings(**overrides):
	defaults = {
		"enabled": 1,
		"idp_entity_id": "https://idp.example.com/metadata",
		"idp_sso_url": "https://idp.example.com/sso",
		"idp_x509_cert": "-----BEGIN CERTIFICATE-----",
		"email_attribute": "email",
		"auto_provision_users": 0,
		"default_role": None,
	}
	defaults.update(overrides)
	return frappe._dict(defaults)


class TestIsEnabled(UnitTestCase):
	@patch("lms.lms.integrations.saml_sso.get_settings")
	def test_disabled_when_not_configured(self, mock_get_settings):
		mock_get_settings.return_value = fake_settings(enabled=0)
		self.assertFalse(is_enabled())

	@patch("lms.lms.integrations.saml_sso.get_settings")
	def test_disabled_without_idp_cert(self, mock_get_settings):
		mock_get_settings.return_value = fake_settings(idp_x509_cert=None)
		self.assertFalse(is_enabled())

	@patch("lms.lms.integrations.saml_sso.get_settings")
	def test_enabled_when_fully_configured(self, mock_get_settings):
		mock_get_settings.return_value = fake_settings()
		self.assertTrue(is_enabled())


class TestFirst(UnitTestCase):
	def test_returns_first_of_list(self):
		self.assertEqual(_first(["a@example.com", "b@example.com"]), "a@example.com")

	def test_returns_none_for_empty_list(self):
		self.assertIsNone(_first([]))

	def test_passes_through_scalar(self):
		self.assertEqual(_first("a@example.com"), "a@example.com")


class TestResolveUser(UnitTestCase):
	@patch("lms.lms.integrations.saml_sso.frappe.db.exists")
	def test_returns_existing_user(self, mock_exists):
		mock_exists.return_value = True
		self.assertEqual(_resolve_user("a@example.com", fake_settings()), "a@example.com")

	@patch("lms.lms.integrations.saml_sso.frappe.db.exists")
	def test_rejects_unknown_user_without_auto_provision(self, mock_exists):
		mock_exists.return_value = False
		with self.assertRaises(frappe.AuthenticationError):
			_resolve_user("new@example.com", fake_settings(auto_provision_users=0))

	@patch("lms.lms.integrations.saml_sso.frappe.get_doc")
	@patch("lms.lms.integrations.saml_sso.frappe.db.exists")
	def test_auto_provisions_new_user(self, mock_exists, mock_get_doc):
		mock_exists.return_value = False
		mock_doc = MagicMock()
		mock_doc.name = "new@example.com"
		mock_get_doc.return_value = mock_doc

		result = _resolve_user("new@example.com", fake_settings(auto_provision_users=1, default_role="LMS Student"))

		mock_doc.insert.assert_called_once()
		self.assertEqual(result, "new@example.com")
