from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import UnitTestCase

from lms.lms.integrations.mpesa import (
	_callback_amount_matches,
	_normalize_phone_number,
	is_enabled,
)


def fake_settings(**overrides):
	defaults = {
		"enabled": 1,
		"environment": "Sandbox",
		"shortcode": "174379",
		"consumer_key": "key",
		"consumer_secret": "secret",
		"passkey": "passkey",
	}
	defaults.update(overrides)
	settings = frappe._dict(defaults)
	settings.get_password = MagicMock(side_effect=lambda field, raise_exception=True: defaults.get(field))
	return settings


class TestIsEnabled(UnitTestCase):
	@patch("lms.lms.integrations.mpesa.get_settings")
	def test_disabled_when_not_configured(self, mock_get_settings):
		mock_get_settings.return_value = fake_settings(enabled=0)
		self.assertFalse(is_enabled())

	@patch("lms.lms.integrations.mpesa.get_settings")
	def test_disabled_without_passkey(self, mock_get_settings):
		mock_get_settings.return_value = fake_settings(passkey=None)
		self.assertFalse(is_enabled())

	@patch("lms.lms.integrations.mpesa.get_settings")
	def test_enabled_when_fully_configured(self, mock_get_settings):
		mock_get_settings.return_value = fake_settings()
		self.assertTrue(is_enabled())


class TestNormalizePhoneNumber(UnitTestCase):
	def test_local_leading_zero(self):
		self.assertEqual(_normalize_phone_number("0712345678"), "254712345678")

	def test_already_international(self):
		self.assertEqual(_normalize_phone_number("254712345678"), "254712345678")

	def test_plus_prefixed(self):
		self.assertEqual(_normalize_phone_number("+254712345678"), "254712345678")

	def test_bare_leading_seven(self):
		self.assertEqual(_normalize_phone_number("712345678"), "254712345678")


class TestCallbackAmountMatches(UnitTestCase):
	def test_matches_within_tolerance(self):
		stk_callback = {"CallbackMetadata": {"Item": [{"Name": "Amount", "Value": 500.0}]}}
		self.assertTrue(_callback_amount_matches(stk_callback, 500))

	def test_rejects_mismatched_amount(self):
		stk_callback = {"CallbackMetadata": {"Item": [{"Name": "Amount", "Value": 1.0}]}}
		self.assertFalse(_callback_amount_matches(stk_callback, 500))

	def test_rejects_missing_metadata(self):
		self.assertFalse(_callback_amount_matches({}, 500))
