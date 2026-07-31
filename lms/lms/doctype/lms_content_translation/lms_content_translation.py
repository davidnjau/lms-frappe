# Copyright (c) 2026, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class LMSContentTranslation(Document):
	pass


def has_permission(doc, ptype="read", user=None):
	"""A cached translation must never be more visible than the source content
	it was translated from — re-check permission on the reference doc rather
	than relying on the blanket LMS Student read grant on this doctype."""
	user = user or frappe.session.user
	roles = frappe.get_roles(user)
	if "System Manager" in roles or "Moderator" in roles:
		return True

	return frappe.has_permission(
		doc.reference_doctype, doc=doc.reference_name, ptype="read", user=user
	)
