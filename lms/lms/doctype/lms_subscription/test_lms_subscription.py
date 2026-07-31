# Copyright (c) 2026, Frappe and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from lms.lms.doctype.lms_subscription.lms_subscription import (
	send_renewal_invoice_mail,
	send_subscription_renewal_reminders,
)

# On IntegrationTestCase, the doctype test records and all
# link-field test record depdendencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


class TestLMSSubscription(UnitTestCase):
	"""
	Unit tests for LMSSubscription.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestSubscriptionRenewalReminders(UnitTestCase):
	@patch("lms.lms.doctype.lms_subscription.lms_subscription.send_renewal_invoice_mail")
	@patch("lms.lms.doctype.lms_subscription.lms_subscription.frappe.get_all")
	@patch("lms.lms.doctype.lms_subscription.lms_subscription.frappe.conf")
	@patch("lms.lms.doctype.lms_subscription.lms_subscription.frappe.get_cached_value")
	def test_skips_when_no_outgoing_email_account(self, mock_cached_value, mock_conf, mock_get_all, mock_send):
		mock_cached_value.return_value = None
		mock_conf.get.return_value = None

		send_subscription_renewal_reminders()

		mock_get_all.assert_not_called()
		mock_send.assert_not_called()

	@patch("lms.lms.doctype.lms_subscription.lms_subscription.send_renewal_invoice_mail")
	@patch("lms.lms.doctype.lms_subscription.lms_subscription.frappe.get_all")
	@patch("lms.lms.doctype.lms_subscription.lms_subscription.frappe.get_cached_value")
	def test_sends_reminder_for_each_due_subscription(self, mock_cached_value, mock_get_all, mock_send):
		mock_cached_value.return_value = "Support"
		mock_get_all.return_value = [{"name": "SUB-0001", "corporate_account": "Acme Inc"}]

		send_subscription_renewal_reminders()

		mock_send.assert_called_once_with({"name": "SUB-0001", "corporate_account": "Acme Inc"})


class TestSendRenewalInvoiceMail(UnitTestCase):
	@patch("lms.lms.doctype.lms_subscription.lms_subscription.frappe.sendmail")
	@patch("lms.lms.doctype.lms_subscription.lms_subscription.frappe.get_all")
	@patch("lms.lms.doctype.lms_subscription.lms_subscription.frappe.db.get_value")
	def test_skips_when_no_primary_contact_email(self, mock_get_value, mock_get_all, mock_sendmail):
		mock_get_value.return_value = {"company_name": "Acme Inc", "primary_contact_email": None}

		send_renewal_invoice_mail(frappe._dict({"corporate_account": "Acme Inc"}))

		mock_sendmail.assert_not_called()

	@patch("lms.lms.doctype.lms_subscription.lms_subscription.frappe.sendmail")
	@patch("lms.lms.doctype.lms_subscription.lms_subscription.frappe.get_all")
	@patch("lms.lms.doctype.lms_subscription.lms_subscription.frappe.db.get_value")
	def test_sends_mail_to_primary_contact_and_admins(self, mock_get_value, mock_get_all, mock_sendmail):
		mock_get_value.return_value = {
			"company_name": "Acme Inc",
			"primary_contact_email": "contact@acme.test",
		}
		mock_get_all.return_value = ["admin@acme.test"]

		send_renewal_invoice_mail(
			frappe._dict(
				{
					"corporate_account": "Acme Inc",
					"plan_tier": "Enterprise",
					"seat_count": 50,
					"billing_cycle": "Annual",
					"renewal_date": "2026-08-30",
					"amount": 5000,
					"currency": "USD",
				}
			)
		)

		mock_sendmail.assert_called_once()
		call_kwargs = mock_sendmail.call_args.kwargs
		self.assertEqual(call_kwargs["recipients"], "contact@acme.test")
		self.assertEqual(call_kwargs["cc"], ["admin@acme.test"])
		self.assertEqual(call_kwargs["template"], "subscription_renewal_reminder")
