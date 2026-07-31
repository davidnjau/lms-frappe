from unittest.mock import patch

import frappe
from frappe.tests import UnitTestCase

from lms.lms.corporate import (
	get_corporate_account_courses,
	get_corporate_account_summary,
	get_corporate_learner_progress,
)


class TestCorporateAccountSummary(UnitTestCase):
	@patch("lms.lms.corporate.frappe.has_permission")
	def test_blocked_without_permission(self, mock_has_permission):
		mock_has_permission.side_effect = frappe.PermissionError
		with self.assertRaises(frappe.PermissionError):
			get_corporate_account_summary("Acme Inc")

	@patch("lms.lms.corporate.frappe.db.count")
	@patch("lms.lms.corporate.frappe.get_all")
	@patch("lms.lms.corporate.frappe.has_permission")
	def test_returns_member_and_program_counts(self, mock_has_permission, mock_get_all, mock_count):
		mock_get_all.return_value = [
			{"member": "a@example.com", "full_name": "A", "role": "Admin"},
			{"member": "b@example.com", "full_name": "B", "role": "Learner"},
		]
		mock_count.side_effect = [3, 1]  # batch_count, program_count

		result = get_corporate_account_summary("Acme Inc")

		self.assertEqual(result["member_count"], 2)
		self.assertEqual(result["batch_count"], 3)
		self.assertEqual(result["program_count"], 1)


class TestCorporateLearnerProgress(UnitTestCase):
	@patch("lms.lms.corporate.get_course_progress")
	@patch("lms.lms.corporate.get_corporate_account_courses")
	@patch("lms.lms.corporate.frappe.get_all")
	@patch("lms.lms.corporate.frappe.has_permission")
	def test_averages_progress_across_courses(
		self, mock_has_permission, mock_get_all, mock_get_courses, mock_get_progress
	):
		mock_get_all.return_value = [{"member": "a@example.com", "full_name": "A"}]
		mock_get_courses.return_value = ["course-1", "course-2"]
		mock_get_progress.side_effect = [40, 60]

		report = get_corporate_learner_progress("Acme Inc")

		self.assertEqual(report[0]["average_progress"], 50)
		self.assertEqual(report[0]["course_progress"], {"course-1": 40, "course-2": 60})

	@patch("lms.lms.corporate.get_corporate_account_courses")
	@patch("lms.lms.corporate.frappe.get_all")
	@patch("lms.lms.corporate.frappe.has_permission")
	def test_no_courses_reports_zero_average(self, mock_has_permission, mock_get_all, mock_get_courses):
		mock_get_all.return_value = [{"member": "a@example.com", "full_name": "A"}]
		mock_get_courses.return_value = []

		report = get_corporate_learner_progress("Acme Inc")

		self.assertEqual(report[0]["average_progress"], 0)
		self.assertEqual(report[0]["course_progress"], {})


class TestGetCorporateAccountCourses(UnitTestCase):
	@patch("lms.lms.corporate.frappe.get_all")
	def test_collects_courses_from_batches_and_programs(self, mock_get_all):
		mock_get_all.side_effect = [
			["Batch A"],  # LMS Batch names
			["Program A"],  # LMS Program names
			["course-1"],  # Batch Course pluck
			["course-1", "course-2"],  # LMS Program Course pluck
		]

		courses = get_corporate_account_courses("Acme Inc")

		self.assertEqual(set(courses), {"course-1", "course-2"})

	@patch("lms.lms.corporate.frappe.get_all")
	def test_no_batches_or_programs_returns_empty(self, mock_get_all):
		mock_get_all.side_effect = [[], []]

		courses = get_corporate_account_courses("Acme Inc")

		self.assertEqual(courses, [])
