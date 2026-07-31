from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import UnitTestCase

from lms.lms.integrations.ai_tutor import _build_context, _check_context_permission, ask_tutor


class TestCheckContextPermission(UnitTestCase):
	@patch("lms.lms.integrations.ai_tutor.can_access_lesson")
	def test_denies_inaccessible_lesson(self, mock_can_access):
		mock_can_access.return_value = False
		with self.assertRaises(frappe.PermissionError):
			_check_context_permission(None, "lesson-1")

	@patch("lms.lms.integrations.ai_tutor.can_modify_course")
	@patch("lms.lms.integrations.ai_tutor.get_membership")
	def test_denies_course_without_membership(self, mock_membership, mock_can_modify):
		mock_membership.return_value = None
		mock_can_modify.return_value = False
		with self.assertRaises(frappe.PermissionError):
			_check_context_permission("course-1", None)

	@patch("lms.lms.integrations.ai_tutor.can_modify_course")
	@patch("lms.lms.integrations.ai_tutor.get_membership")
	def test_allows_enrolled_member(self, mock_membership, mock_can_modify):
		mock_membership.return_value = {"member": "student@example.test"}
		mock_can_modify.return_value = False
		_check_context_permission("course-1", None)  # should not raise


class TestBuildContext(UnitTestCase):
	@patch("lms.lms.integrations.ai_tutor.frappe.db.get_value")
	def test_builds_lesson_context(self, mock_get_value):
		mock_get_value.side_effect = [
			frappe._dict({"title": "Intro", "body": "Lesson body", "course": "course-1"}),
			"Finance 101",
		]
		context = _build_context(None, "lesson-1")
		self.assertIn("Finance 101", context)
		self.assertIn("Lesson body", context)


class TestAskTutor(UnitTestCase):
	def test_rejects_blank_question(self):
		with self.assertRaises(frappe.ValidationError):
			ask_tutor("   ")

	@patch("lms.lms.integrations.ai_tutor.log_usage")
	@patch("lms.lms.integrations.ai_tutor.get_client")
	@patch("lms.lms.integrations.ai_tutor._build_context")
	@patch("lms.lms.integrations.ai_tutor.enforce_enabled_and_budget")
	@patch("lms.lms.integrations.ai_tutor._check_context_permission")
	def test_returns_answer_text(
		self, mock_check_perm, mock_enforce, mock_context, mock_get_client, mock_log
	):
		mock_context.return_value = "Course: Finance 101"
		mock_message = MagicMock()
		mock_message.content = [frappe._dict({"type": "text", "text": "Here is the answer."})]
		mock_message.usage = MagicMock()

		mock_stream_cm = MagicMock()
		mock_stream_cm.__enter__.return_value.get_final_message.return_value = mock_message
		mock_client = MagicMock()
		mock_client.messages.stream.return_value = mock_stream_cm
		mock_get_client.return_value = mock_client

		result = ask_tutor("What is NPV?", course="course-1")

		self.assertEqual(result, {"answer": "Here is the answer."})
		mock_log.assert_called_once()
