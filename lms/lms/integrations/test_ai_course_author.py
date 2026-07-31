from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import UnitTestCase

from lms.lms.integrations.ai_course_author import (
	CourseOutlineDraft,
	QuizDraft,
	draft_course_outline,
	draft_quiz_questions,
)


class TestDraftCourseOutline(UnitTestCase):
	def test_rejects_blank_topic(self):
		with self.assertRaises(frappe.ValidationError):
			draft_course_outline("   ")

	@patch("lms.lms.integrations.ai_course_author.has_moderator_role")
	@patch("lms.lms.integrations.ai_course_author.has_course_instructor_role")
	def test_rejects_non_instructor(self, mock_instructor_role, mock_moderator_role):
		mock_instructor_role.return_value = False
		mock_moderator_role.return_value = False
		with self.assertRaises(frappe.PermissionError):
			draft_course_outline("Credit Risk Management")

	@patch("lms.lms.integrations.ai_course_author.log_usage")
	@patch("lms.lms.integrations.ai_course_author.get_client")
	@patch("lms.lms.integrations.ai_course_author.enforce_enabled_and_budget")
	@patch("lms.lms.integrations.ai_course_author.has_moderator_role")
	def test_returns_parsed_outline(self, mock_moderator_role, mock_enforce, mock_get_client, mock_log):
		mock_moderator_role.return_value = True
		parsed = CourseOutlineDraft(
			title="Credit Risk 101",
			learning_objectives=["Understand credit risk basics"],
			chapters=[{"title": "Intro", "lessons": ["What is credit risk?"]}],
		)
		mock_message = MagicMock()
		mock_message.parsed_output = parsed
		mock_message.usage = MagicMock()
		mock_client = MagicMock()
		mock_client.messages.parse.return_value = mock_message
		mock_get_client.return_value = mock_client

		result = draft_course_outline("Credit Risk Management")

		self.assertEqual(result["title"], "Credit Risk 101")
		self.assertEqual(len(result["chapters"]), 1)
		mock_log.assert_called_once()

	@patch("lms.lms.integrations.ai_course_author.get_client")
	@patch("lms.lms.integrations.ai_course_author.enforce_enabled_and_budget")
	@patch("lms.lms.integrations.ai_course_author.has_moderator_role")
	def test_throws_when_output_not_parsed(self, mock_moderator_role, mock_enforce, mock_get_client):
		mock_moderator_role.return_value = True
		mock_message = MagicMock()
		mock_message.parsed_output = None
		mock_client = MagicMock()
		mock_client.messages.parse.return_value = mock_message
		mock_get_client.return_value = mock_client

		with self.assertRaises(frappe.ValidationError):
			draft_course_outline("Credit Risk Management")


class TestDraftQuizQuestions(UnitTestCase):
	@patch("lms.lms.integrations.ai_course_author.frappe.db.get_value")
	def test_missing_lesson_throws(self, mock_get_value):
		mock_get_value.return_value = None
		with self.assertRaises(frappe.ValidationError):
			draft_quiz_questions("bad-lesson")

	@patch("lms.lms.integrations.ai_course_author.can_modify_course")
	@patch("lms.lms.integrations.ai_course_author.frappe.db.get_value")
	def test_rejects_non_course_editor(self, mock_get_value, mock_can_modify):
		mock_get_value.return_value = frappe._dict(
			{"title": "Lesson 1", "body": "content", "course": "course-1"}
		)
		mock_can_modify.return_value = False
		with self.assertRaises(frappe.PermissionError):
			draft_quiz_questions("lesson-1")

	@patch("lms.lms.integrations.ai_course_author.log_usage")
	@patch("lms.lms.integrations.ai_course_author.get_client")
	@patch("lms.lms.integrations.ai_course_author.enforce_enabled_and_budget")
	@patch("lms.lms.integrations.ai_course_author.can_modify_course")
	@patch("lms.lms.integrations.ai_course_author.frappe.db.get_value")
	def test_returns_parsed_quiz(
		self, mock_get_value, mock_can_modify, mock_enforce, mock_get_client, mock_log
	):
		mock_get_value.return_value = frappe._dict(
			{"title": "Lesson 1", "body": "content", "course": "course-1"}
		)
		mock_can_modify.return_value = True
		parsed = QuizDraft(
			questions=[
				{
					"question": "What is NPV?",
					"options": ["A", "B", "C", "D"],
					"correct_option_index": 0,
					"explanation": "...",
				}
			]
		)
		mock_message = MagicMock()
		mock_message.parsed_output = parsed
		mock_message.usage = MagicMock()
		mock_client = MagicMock()
		mock_client.messages.parse.return_value = mock_message
		mock_get_client.return_value = mock_client

		result = draft_quiz_questions("lesson-1", count=1)

		self.assertEqual(len(result["questions"]), 1)
		mock_log.assert_called_once()
