from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import UnitTestCase

from lms.lms.integrations.ai_translation import _content_hash, translate_content


class TestContentHash(UnitTestCase):
	def test_same_text_same_hash(self):
		self.assertEqual(_content_hash("hello"), _content_hash("hello"))

	def test_different_text_different_hash(self):
		self.assertNotEqual(_content_hash("hello"), _content_hash("world"))


class TestTranslateContent(UnitTestCase):
	def test_rejects_unsupported_language(self):
		with self.assertRaises(frappe.ValidationError):
			translate_content("Course Lesson", "lesson-1", "body", "de")

	@patch("lms.lms.integrations.ai_translation.frappe.has_permission")
	@patch("lms.lms.integrations.ai_translation.frappe.db.get_value")
	def test_returns_empty_for_blank_source(self, mock_get_value, mock_has_permission):
		mock_get_value.return_value = None
		result = translate_content("Course Lesson", "lesson-1", "body", "sw")
		self.assertEqual(result, "")

	@patch("lms.lms.integrations.ai_translation._translate_text")
	@patch("lms.lms.integrations.ai_translation.enforce_enabled_and_budget")
	@patch("lms.lms.integrations.ai_translation.frappe.get_doc")
	@patch("lms.lms.integrations.ai_translation.frappe.db.exists")
	@patch("lms.lms.integrations.ai_translation.frappe.db.get_value")
	@patch("lms.lms.integrations.ai_translation.frappe.has_permission")
	def test_cache_hit_skips_translation_call(
		self, mock_has_permission, mock_get_value, mock_exists, mock_get_doc, mock_enforce, mock_translate
	):
		# First get_value call returns source text, second (cache lookup) returns cached translation
		mock_get_value.side_effect = ["Hello world", "Habari dunia"]

		result = translate_content("Course Lesson", "lesson-1", "body", "sw")

		self.assertEqual(result, "Habari dunia")
		mock_translate.assert_not_called()
		mock_enforce.assert_not_called()

	@patch("lms.lms.integrations.ai_translation._translate_text")
	@patch("lms.lms.integrations.ai_translation.enforce_enabled_and_budget")
	@patch("lms.lms.integrations.ai_translation.frappe.get_doc")
	@patch("lms.lms.integrations.ai_translation.frappe.db.exists")
	@patch("lms.lms.integrations.ai_translation.frappe.db.get_value")
	@patch("lms.lms.integrations.ai_translation.frappe.has_permission")
	def test_cache_miss_translates_and_inserts(
		self, mock_has_permission, mock_get_value, mock_exists, mock_get_doc, mock_enforce, mock_translate
	):
		mock_get_value.side_effect = ["Hello world", None]
		mock_exists.return_value = None
		mock_translate.return_value = "Habari dunia"
		mock_doc = MagicMock()
		mock_get_doc.return_value = mock_doc

		result = translate_content("Course Lesson", "lesson-1", "body", "sw")

		self.assertEqual(result, "Habari dunia")
		mock_enforce.assert_called_once()
		mock_doc.insert.assert_called_once_with(ignore_permissions=True)
