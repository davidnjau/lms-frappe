# Copyright (c) 2026, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from lms.lms.utils import can_modify_course


class LMSxAPIStatement(Document):
	pass


def has_permission(doc, ptype="read", user=None):
	user = user or frappe.session.user
	roles = frappe.get_roles(user)
	if "System Manager" in roles or "Moderator" in roles:
		return True

	if doc.member == user:
		return ptype in ("read", "select", "print", "create")

	if ptype not in ("read", "select", "print"):
		return False

	if not doc.course:
		return False

	original_user = frappe.session.user
	try:
		frappe.session.user = user
		return can_modify_course(doc.course)
	finally:
		frappe.session.user = original_user
