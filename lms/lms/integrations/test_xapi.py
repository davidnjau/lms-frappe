from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import UnitTestCase

from lms.lms.integrations.xapi import _first_text, get_statements, record_statement


class TestFirstText(UnitTestCase):
	def test_extracts_from_langmap(self):
		self.assertEqual(_first_text({"en-US": "Completed"}), "Completed")

	def test_passes_through_bare_string(self):
		self.assertEqual(_first_text("Completed"), "Completed")

	def test_returns_none_for_none(self):
		self.assertIsNone(_first_text(None))


class TestRecordStatement(UnitTestCase):
	def test_rejects_non_dict_statement(self):
		with self.assertRaises(frappe.ValidationError):
			record_statement("not-a-dict")

	def test_rejects_missing_verb(self):
		with self.assertRaises(frappe.ValidationError):
			record_statement({"object": {"id": "http://example.com/activity"}})

	def test_rejects_missing_object_id(self):
		with self.assertRaises(frappe.ValidationError):
			record_statement({"verb": {"display": {"en-US": "completed"}}, "object": {}})

	@patch("lms.lms.integrations.xapi.frappe.get_doc")
	def test_stores_statement_under_session_user_not_client_actor(self, mock_get_doc):
		mock_doc = MagicMock()
		mock_doc.name = "STMT-0001"
		mock_get_doc.return_value = mock_doc
		frappe.session.user = "student@example.test"

		record_statement(
			{
				"actor": {"mbox": "mailto:someone-else@example.com"},
				"verb": {"display": {"en-US": "completed"}},
				"object": {"id": "http://example.com/activity/1"},
				"result": {"completion": True, "success": True, "score": {"scaled": 0.9}},
			},
			course="course-1",
		)

		payload = mock_get_doc.call_args[0][0]
		self.assertEqual(payload["member"], "student@example.test")
		self.assertEqual(payload["verb"], "completed")
		self.assertEqual(payload["object_id"], "http://example.com/activity/1")
		self.assertEqual(payload["completion"], 1)
		self.assertEqual(payload["success"], "True")
		self.assertEqual(payload["score_scaled"], 0.9)
		mock_doc.insert.assert_called_once()


class TestGetStatements(UnitTestCase):
	def setUp(self):
		frappe.session.user = "student@example.test"

	@patch("lms.lms.integrations.xapi.frappe.get_list")
	def test_defaults_to_session_user(self, mock_get_list):
		mock_get_list.return_value = []
		get_statements(course="course-1")
		filters = mock_get_list.call_args.kwargs["filters"]
		self.assertEqual(filters["member"], "student@example.test")

	@patch("lms.lms.integrations.xapi.can_modify_course")
	@patch("lms.lms.integrations.xapi.frappe.get_roles")
	def test_rejects_cross_member_query_without_permission(self, mock_get_roles, mock_can_modify):
		mock_get_roles.return_value = ["LMS Student"]
		mock_can_modify.return_value = False
		with self.assertRaises(frappe.PermissionError):
			get_statements(course="course-1", member="other@example.test")

	@patch("lms.lms.integrations.xapi.frappe.get_list")
	@patch("lms.lms.integrations.xapi.can_modify_course")
	@patch("lms.lms.integrations.xapi.frappe.get_roles")
	def test_allows_instructor_to_query_another_member(
		self, mock_get_roles, mock_can_modify, mock_get_list
	):
		mock_get_roles.return_value = ["Course Creator"]
		mock_can_modify.return_value = True
		mock_get_list.return_value = []

		get_statements(course="course-1", member="other@example.test")

		filters = mock_get_list.call_args.kwargs["filters"]
		self.assertEqual(filters["member"], "other@example.test")
