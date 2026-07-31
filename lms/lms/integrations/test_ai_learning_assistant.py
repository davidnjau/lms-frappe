from unittest.mock import patch

import frappe
from frappe.tests import UnitTestCase

from lms.lms.integrations.ai_learning_assistant import send_learning_nudges


class TestSendLearningNudges(UnitTestCase):
	@patch("lms.lms.integrations.ai_learning_assistant.send_nudge_mail")
	@patch("lms.lms.integrations.ai_learning_assistant.frappe.db.sql")
	@patch("lms.lms.integrations.ai_learning_assistant.frappe.conf")
	@patch("lms.lms.integrations.ai_learning_assistant.frappe.get_cached_value")
	def test_skips_when_no_outgoing_email_account(
		self, mock_cached_value, mock_conf, mock_sql, mock_send
	):
		mock_cached_value.return_value = None
		mock_conf.get.return_value = None

		send_learning_nudges()

		mock_sql.assert_not_called()
		mock_send.assert_not_called()

	@patch("lms.lms.integrations.ai_learning_assistant.send_nudge_mail")
	@patch("lms.lms.integrations.ai_learning_assistant.frappe.db.sql")
	@patch("lms.lms.integrations.ai_learning_assistant.frappe.get_cached_value")
	def test_sends_nudge_for_each_stalled_enrollment(self, mock_cached_value, mock_sql, mock_send):
		mock_cached_value.return_value = "Support"
		mock_sql.return_value = [
			frappe._dict(
				{
					"member": "student@example.test",
					"member_name": "Student",
					"course": "course-1",
					"course_title": "Finance 101",
				}
			)
		]

		send_learning_nudges()

		mock_send.assert_called_once()
