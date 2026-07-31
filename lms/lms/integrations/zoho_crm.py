"""Syncs LMS Corporate Account records to Zoho CRM (Accounts module).

Credentials live on the LMS Zoho CRM Settings single doctype (Client ID/Secret and
Refresh Token are Password fields, encrypted at rest by Frappe) rather than in
site_config, matching the LMS Zoom/Google Meet Settings pattern already used in
this app. Sync is a no-op whenever the integration isn't enabled/configured, so it
never blocks a Corporate Account save when Zoho isn't set up (e.g. in development).
"""

import frappe
import requests

CACHE_KEY = "zoho_crm_access_token"
TOKEN_URL = "https://accounts.zoho.com/oauth/v2/token"


def get_settings():
	return frappe.get_single("LMS Zoho CRM Settings")


def is_enabled() -> bool:
	settings = get_settings()
	has_client_secret = settings.get_password("client_secret", raise_exception=False)
	has_refresh_token = settings.get_password("refresh_token", raise_exception=False)
	return bool(settings.enabled and settings.client_id and has_client_secret and has_refresh_token)


def get_access_token() -> str | None:
	cached = frappe.cache().get_value(CACHE_KEY)
	if cached:
		return cached

	settings = get_settings()
	try:
		response = requests.post(
			TOKEN_URL,
			data={
				"grant_type": "refresh_token",
				"client_id": settings.client_id,
				"client_secret": settings.get_password("client_secret"),
				"refresh_token": settings.get_password("refresh_token"),
			},
			timeout=10,
		)
		response.raise_for_status()
		data = response.json()
	except requests.RequestException as e:
		frappe.log_error(title="Zoho CRM token refresh failed", message=str(e))
		return None

	access_token = data.get("access_token")
	if access_token:
		frappe.cache().set_value(CACHE_KEY, access_token, expires_in_sec=data.get("expires_in", 3600) - 60)
	return access_token


def sync_corporate_account(doc, method=None):
	"""doc_event hook (after_insert/on_update) for LMS Corporate Account."""
	if not is_enabled():
		return
	frappe.enqueue(
		"lms.lms.integrations.zoho_crm.sync_corporate_account_job",
		queue="short",
		corporate_account=doc.name,
	)


def sync_corporate_account_job(corporate_account: str):
	account = frappe.get_doc("LMS Corporate Account", corporate_account)
	payload = {
		"Account_Name": account.company_name,
		"Industry": account.industry,
		"LMS_Status": account.status,
		"LMS_Member_Count": account.member_count,
		"Email": account.primary_contact_email,
		"LMS_Corporate_Account_ID": account.name,
	}
	upsert_account(payload)


def upsert_account(payload: dict) -> dict | None:
	access_token = get_access_token()
	if not access_token:
		return None

	settings = get_settings()
	try:
		response = requests.post(
			f"{settings.api_domain}/crm/v2/Accounts/upsert",
			headers={"Authorization": f"Zoho-oauthtoken {access_token}"},
			json={"data": [payload], "duplicate_check_fields": ["LMS_Corporate_Account_ID"]},
			timeout=10,
		)
		response.raise_for_status()
		return response.json()
	except requests.RequestException as e:
		frappe.log_error(
			title="Zoho CRM account sync failed",
			message=f"Corporate Account {payload.get('LMS_Corporate_Account_ID')}: {e}",
		)
		return None
