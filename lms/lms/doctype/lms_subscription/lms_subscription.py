# Copyright (c) 2026, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, getdate, nowdate

from lms.lms.utils import get_lms_route


class LMSSubscription(Document):
	def validate(self):
		if getdate(self.renewal_date) <= getdate(self.start_date):
			frappe.throw(_("Renewal Date must be after Start Date."))


def has_permission(doc, ptype="read", user=None):
	user = user or frappe.session.user
	roles = frappe.get_roles(user)
	if "System Manager" in roles or "Moderator" in roles:
		return True

	is_member = frappe.db.exists("LMS Corporate Member", {"parent": doc.corporate_account, "member": user})
	if not is_member:
		return False

	if ptype in ("read", "select", "print"):
		return True

	is_admin = frappe.db.exists(
		"LMS Corporate Member", {"parent": doc.corporate_account, "member": user, "role": "Admin"}
	)
	return bool(is_admin)


def get_permission_query_conditions(user=None):
	user = user or frappe.session.user
	roles = frappe.get_roles(user)
	if "System Manager" in roles or "Moderator" in roles:
		return None

	return f"""(`tabLMS Subscription`.corporate_account in
		(select parent from `tabLMS Corporate Member` where member = {frappe.db.escape(user)}))"""


def send_subscription_renewal_reminders(days_before: int = 30):
	"""Emails the corporate account's admins/primary contact when a subscription
	is due for renewal in `days_before` days, with an invoice-style summary."""
	outgoing_email_account = frappe.get_cached_value(
		"Email Account", {"default_outgoing": 1, "enable_outgoing": 1}, "name"
	)
	if not (outgoing_email_account or frappe.conf.get("mail_login")):
		return

	target_date = add_days(nowdate(), days_before)
	subscriptions = frappe.get_all(
		"LMS Subscription",
		{"status": "Active", "renewal_date": target_date},
		["name", "corporate_account", "plan_tier", "seat_count", "billing_cycle", "renewal_date", "amount", "currency"],
	)

	for subscription in subscriptions:
		send_renewal_invoice_mail(subscription)


def send_renewal_invoice_mail(subscription):
	account = frappe.db.get_value(
		"LMS Corporate Account",
		subscription.corporate_account,
		["company_name", "primary_contact_email"],
		as_dict=True,
	)
	if not account or not account.primary_contact_email:
		return

	admins = frappe.get_all(
		"LMS Corporate Member",
		{"parent": subscription.corporate_account, "role": "Admin"},
		pluck="member",
	)

	args = {
		"company_name": account.company_name,
		"plan_tier": subscription.plan_tier,
		"seat_count": subscription.seat_count,
		"billing_cycle": subscription.billing_cycle,
		"renewal_date": subscription.renewal_date,
		"amount": subscription.amount,
		"currency": subscription.currency,
		"link": get_lms_route(f"corporate/{subscription.corporate_account}"),
	}

	frappe.sendmail(
		recipients=account.primary_contact_email,
		cc=admins,
		subject=_("Upcoming renewal for your {0} subscription").format(subscription.plan_tier),
		template="subscription_renewal_reminder",
		args=args,
		header=[_("Subscription Renewal"), "blue"],
		retry=3,
	)
