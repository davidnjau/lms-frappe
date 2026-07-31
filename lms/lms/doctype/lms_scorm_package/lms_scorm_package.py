# Copyright (c) 2026, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from lms.lms.utils import can_modify_course


class LMSSCORMPackage(Document):
	pass


def has_permission(doc, ptype="read", user=None):
	user = user or frappe.session.user
	roles = frappe.get_roles(user)
	if "System Manager" in roles or "Moderator" in roles:
		return True

	original_user = frappe.session.user
	try:
		frappe.session.user = user
		return can_modify_course(doc.course)
	finally:
		frappe.session.user = original_user


def record_version(course: str, chapter: str, scorm_package: str, values: dict) -> None:
	"""Insert-only version history for a SCORM upload — additive alongside the
	existing Course Chapter fields (scorm_package/manifest_file/launch_file), which
	keep the "current" pointer used by the render/extraction pipeline unchanged.
	"""
	frappe.db.set_value(
		"LMS SCORM Package", {"chapter": chapter, "is_current": 1}, "is_current", 0, update_modified=False
	)

	last_version = frappe.db.get_value(
		"LMS SCORM Package", {"chapter": chapter}, "version", order_by="version desc"
	)

	frappe.get_doc(
		{
			"doctype": "LMS SCORM Package",
			"course": course,
			"chapter": chapter,
			"version": (last_version or 0) + 1,
			"is_current": 1,
			"scorm_package": scorm_package,
			"scorm_package_path": values.get("scorm_package_path"),
			"manifest_file": values.get("manifest_file"),
			"launch_file": values.get("launch_file"),
		}
	).insert(ignore_permissions=True)
