from unittest.mock import patch

import frappe
from frappe.tests import UnitTestCase

from lms.lms.integrations.ai_analytics import _risk_label, get_completion_risk


class TestRiskLabel(UnitTestCase):
	def test_completed_takes_priority(self):
		self.assertEqual(_risk_label(30, 100), "Completed")

	def test_no_activity_is_high_risk(self):
		self.assertEqual(_risk_label(None, 10), "High")

	def test_long_inactivity_is_high_risk(self):
		self.assertEqual(_risk_label(30, 50), "High")

	def test_moderate_inactivity_is_medium_risk(self):
		self.assertEqual(_risk_label(10, 50), "Medium")

	def test_low_completion_is_medium_risk_even_if_recent(self):
		self.assertEqual(_risk_label(1, 10), "Medium")

	def test_recent_and_progressing_is_low_risk(self):
		self.assertEqual(_risk_label(1, 50), "Low")


class TestGetCompletionRisk(UnitTestCase):
	@patch("lms.lms.integrations.ai_analytics.can_modify_course")
	def test_rejects_non_instructor(self, mock_can_modify):
		mock_can_modify.return_value = False
		with self.assertRaises(frappe.PermissionError):
			get_completion_risk("course-1")

	@patch("lms.lms.integrations.ai_analytics.get_course_progress")
	@patch("lms.lms.integrations.ai_analytics.frappe.db.get_value")
	@patch("lms.lms.integrations.ai_analytics.frappe.get_all")
	@patch("lms.lms.integrations.ai_analytics.can_modify_course")
	def test_builds_report_for_each_member(
		self, mock_can_modify, mock_get_all, mock_get_value, mock_get_progress
	):
		mock_can_modify.return_value = True
		mock_get_all.return_value = [
			frappe._dict({"member": "student@example.test", "member_name": "Student"})
		]
		mock_get_value.return_value = None
		mock_get_progress.return_value = 0

		report = get_completion_risk("course-1")

		self.assertEqual(len(report), 1)
		self.assertEqual(report[0]["risk"], "High")
