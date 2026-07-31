# Copyright (c) 2026, Frappe and Contributors
# See license.txt

from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from lms.lms.doctype.lms_scorm_package.lms_scorm_package import record_version

# On IntegrationTestCase, the doctype test records and all
# link-field test record depdendencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


class TestLMSSCORMPackage(UnitTestCase):
	"""
	Unit tests for LMSSCORMPackage.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestRecordVersion(UnitTestCase):
	@patch("lms.lms.doctype.lms_scorm_package.lms_scorm_package.frappe.get_doc")
	@patch("lms.lms.doctype.lms_scorm_package.lms_scorm_package.frappe.db.get_value")
	@patch("lms.lms.doctype.lms_scorm_package.lms_scorm_package.frappe.db.set_value")
	def test_first_upload_is_version_one(self, mock_set_value, mock_get_value, mock_get_doc):
		mock_get_value.return_value = None
		mock_doc = MagicMock()
		mock_get_doc.return_value = mock_doc

		record_version(
			"course-1",
			"chapter-1",
			"file-1",
			{"scorm_package_path": "/path", "manifest_file": "/m", "launch_file": "/l"},
		)

		inserted = mock_get_doc.call_args[0][0]
		self.assertEqual(inserted["version"], 1)
		self.assertEqual(inserted["is_current"], 1)
		mock_doc.insert.assert_called_once_with(ignore_permissions=True)

	@patch("lms.lms.doctype.lms_scorm_package.lms_scorm_package.frappe.get_doc")
	@patch("lms.lms.doctype.lms_scorm_package.lms_scorm_package.frappe.db.get_value")
	@patch("lms.lms.doctype.lms_scorm_package.lms_scorm_package.frappe.db.set_value")
	def test_reupload_increments_version_and_demotes_previous(
		self, mock_set_value, mock_get_value, mock_get_doc
	):
		mock_get_value.return_value = 2

		record_version("course-1", "chapter-1", "file-2", {})

		mock_set_value.assert_called_once_with(
			"LMS SCORM Package",
			{"chapter": "chapter-1", "is_current": 1},
			"is_current",
			0,
			update_modified=False,
		)
		inserted = mock_get_doc.call_args[0][0]
		self.assertEqual(inserted["version"], 3)
