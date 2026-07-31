"""M-Pesa (Safaricom Daraja API) payments via STK Push.

Doesn't plug into the frappe/payments app's gateway-controller abstraction that
lms/lms/payments.py uses for Razorpay/Stripe/PayPal-style gateways: that
abstraction assumes a hosted-checkout redirect URL
(controller.get_payment_url(...) -> a page the browser is sent to), which STK
Push has no equivalent of — the customer approves the payment on their phone,
and the result arrives later via callback(). Reuses the same LMS Payment
record model and completion logic (record_payment, complete_enrollment) as the
existing gateway flow instead, so enrollment behavior stays identical once a
payment is confirmed either way.
"""

import base64
from datetime import datetime

import frappe
import requests
from frappe import _

from lms.lms.payments import record_payment
from lms.lms.utils import complete_enrollment, get_order_summary

SANDBOX_BASE_URL = "https://sandbox.safaricom.co.ke"
PRODUCTION_BASE_URL = "https://api.safaricom.co.ke"
CACHE_KEY = "mpesa_access_token"


def get_settings():
	return frappe.get_single("LMS M-Pesa Settings")


def is_enabled() -> bool:
	settings = get_settings()
	has_secret = settings.get_password("consumer_secret", raise_exception=False)
	has_passkey = settings.get_password("passkey", raise_exception=False)
	return bool(settings.enabled and settings.shortcode and settings.consumer_key and has_secret and has_passkey)


def _base_url(settings) -> str:
	return PRODUCTION_BASE_URL if settings.environment == "Production" else SANDBOX_BASE_URL


def _callback_url() -> str:
	return frappe.utils.get_url("/api/method/lms.lms.integrations.mpesa.callback")


def get_access_token(settings) -> str | None:
	cached = frappe.cache().get_value(CACHE_KEY)
	if cached:
		return cached

	try:
		response = requests.get(
			f"{_base_url(settings)}/oauth/v1/generate?grant_type=client_credentials",
			auth=(settings.consumer_key, settings.get_password("consumer_secret")),
			timeout=10,
		)
		response.raise_for_status()
		data = response.json()
	except requests.RequestException as e:
		frappe.log_error(title="M-Pesa token request failed", message=str(e))
		return None

	access_token = data.get("access_token")
	if access_token:
		expires_in = int(data.get("expires_in", 3599)) - 60
		frappe.cache().set_value(CACHE_KEY, access_token, expires_in_sec=expires_in)
	return access_token


def _normalize_phone_number(phone_number: str) -> str:
	"""Accepts 07.., 01.., +2547.., 2547.. and returns Daraja's 2547XXXXXXXX form."""
	digits = "".join(ch for ch in phone_number if ch.isdigit())
	if digits.startswith("0"):
		digits = "254" + digits[1:]
	elif digits.startswith("7") or digits.startswith("1"):
		digits = "254" + digits
	return digits


@frappe.whitelist()
def initiate_payment(
	doctype: str,
	docname: str,
	phone_number: str,
	address: dict,
	payment_for_certificate: int = 0,
	coupon_code: str | None = None,
	country: str | None = None,
) -> dict:
	if not is_enabled():
		frappe.throw(_("M-Pesa payments are not configured."))

	details = frappe._dict(get_order_summary(doctype, docname, coupon=coupon_code, country=country))
	original_amount = details.original_amount
	discount_amount = details.get("discount_amount", 0)
	amount = original_amount - discount_amount

	payment_doc = record_payment(
		address,
		doctype,
		docname,
		amount,
		original_amount,
		details.currency,
		discount_amount=discount_amount,
		payment_for_certificate=payment_for_certificate,
		coupon_code=coupon_code,
		coupon=details.get("coupon"),
	)

	if amount <= 0:
		frappe.db.set_value("LMS Payment", payment_doc.name, "payment_received", 1)
		complete_enrollment(payment_doc.name, doctype, docname)
		return {"status": "completed", "payment": payment_doc.name}

	settings = get_settings()
	checkout_request_id = _initiate_stk_push(settings, amount, phone_number, payment_doc.name)
	if not checkout_request_id:
		frappe.throw(_("Could not initiate M-Pesa payment. Please try again."))

	# order_id already exists on LMS Payment for exactly this (gateway
	# transaction reference) — reused rather than adding a new field.
	frappe.db.set_value("LMS Payment", payment_doc.name, "order_id", checkout_request_id)
	return {"status": "pending", "payment": payment_doc.name}


def _initiate_stk_push(settings, amount: float, phone_number: str, payment_name: str) -> str | None:
	access_token = get_access_token(settings)
	if not access_token:
		return None

	phone = _normalize_phone_number(phone_number)
	timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
	password = base64.b64encode(
		f"{settings.shortcode}{settings.get_password('passkey')}{timestamp}".encode()
	).decode()

	try:
		response = requests.post(
			f"{_base_url(settings)}/mpesa/stkpush/v1/processrequest",
			headers={"Authorization": f"Bearer {access_token}"},
			json={
				"BusinessShortCode": settings.shortcode,
				"Password": password,
				"Timestamp": timestamp,
				"TransactionType": "CustomerPayBillOnline",
				"Amount": int(round(amount)),
				"PartyA": phone,
				"PartyB": settings.shortcode,
				"PhoneNumber": phone,
				"CallBackURL": _callback_url(),
				"AccountReference": payment_name,
				"TransactionDesc": "LMS Payment",
			},
			timeout=15,
		)
		response.raise_for_status()
		data = response.json()
	except requests.RequestException as e:
		frappe.log_error(title="M-Pesa STK push failed", message=str(e))
		return None

	return data.get("CheckoutRequestID")


@frappe.whitelist(allow_guest=True)
def callback():
	stk_callback = ((frappe.form_dict.get("Body") or {}).get("stkCallback")) or {}
	checkout_request_id = stk_callback.get("CheckoutRequestID")
	if not checkout_request_id:
		return {"ResultCode": 0, "ResultDesc": "Accepted"}

	payment = frappe.db.get_value(
		"LMS Payment",
		{"order_id": checkout_request_id},
		["name", "member", "payment_for_document_type", "payment_for_document", "payment_received", "amount"],
		as_dict=True,
	)
	if not payment or payment.payment_received:
		return {"ResultCode": 0, "ResultDesc": "Accepted"}

	if stk_callback.get("ResultCode") == 0 and _callback_amount_matches(stk_callback, payment.amount):
		frappe.db.set_value("LMS Payment", payment.name, "payment_received", 1)
		_complete_enrollment_as_member(
			payment.name, payment.payment_for_document_type, payment.payment_for_document, payment.member
		)
	else:
		frappe.logger("lms.security").warning(
			"M-Pesa payment %s not confirmed: %s", payment.name, stk_callback.get("ResultDesc")
		)

	return {"ResultCode": 0, "ResultDesc": "Accepted"}


def _callback_amount_matches(stk_callback: dict, expected_amount: float) -> bool:
	"""Defense in depth beyond the (already hard-to-guess) CheckoutRequestID
	match — reject a callback whose confirmed amount doesn't match what was
	actually requested."""
	items = ((stk_callback.get("CallbackMetadata") or {}).get("Item")) or []
	for item in items:
		if item.get("Name") == "Amount":
			return abs(float(item.get("Value", 0)) - float(expected_amount)) < 1
	return False


def _complete_enrollment_as_member(payment_name: str, doctype: str, docname: str, member: str):
	"""complete_enrollment()/enroll_in_course() read frappe.session.user rather
	than taking the member explicitly — fine when called synchronously in the
	paying user's own request, but this callback runs as Safaricom's server, not
	the student. Scoped session swap, same pattern as can_access_lesson() in
	lms/lms/permissions.py."""
	original_user = frappe.session.user
	try:
		frappe.session.user = member
		complete_enrollment(payment_name, doctype, docname)
	finally:
		frappe.session.user = original_user


@frappe.whitelist()
def get_payment_status(payment: str) -> dict:
	payment_doc = frappe.db.get_value("LMS Payment", payment, ["member", "payment_received"], as_dict=True)
	if not payment_doc or payment_doc.member != frappe.session.user:
		frappe.throw(_("Payment not found."), frappe.PermissionError)
	return {"payment_received": bool(payment_doc.payment_received)}
