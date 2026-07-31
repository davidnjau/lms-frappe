# Copyright (c) 2026, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class LMSCorporateAccount(Document):
	def validate(self):
		self.validate_corporate_members()
		self.update_member_count()

	def validate_corporate_members(self):
		members = [row.member for row in self.corporate_members]
		duplicates = {member for member in members if members.count(member) > 1}
		if len(duplicates):
			frappe.throw(
				frappe._("Member {0} has already been added to this corporate account.").format(
					frappe.bold(next(iter(duplicates)))
				)
			)

	def update_member_count(self):
		member_count = len(self.corporate_members)
		if self.member_count != member_count:
			self.member_count = member_count


def has_permission(doc, ptype="read", user=None):
	user = user or frappe.session.user
	roles = frappe.get_roles(user)
	if "System Manager" in roles or "Moderator" in roles:
		return True

	is_member = frappe.db.exists("LMS Corporate Member", {"parent": doc.name, "member": user})
	if not is_member:
		return False

	if ptype in ("read", "select", "print"):
		return True

	is_admin = frappe.db.exists(
		"LMS Corporate Member", {"parent": doc.name, "member": user, "role": "Admin"}
	)
	return bool(is_admin)


def get_permission_query_conditions(user=None):
	user = user or frappe.session.user
	roles = frappe.get_roles(user)
	if "System Manager" in roles or "Moderator" in roles:
		return None

	return f"""(`tabLMS Corporate Account`.name in
		(select parent from `tabLMS Corporate Member` where member = {frappe.db.escape(user)}))"""
