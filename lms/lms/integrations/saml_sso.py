"""SAML 2.0 SP integration (login-only, SP-initiated) using python3-saml
(OneLogin's toolkit) for all XML signature/assertion validation — this module
never parses or verifies SAML XML itself, only builds the settings/request
dicts the library needs and maps a verified identity onto a Frappe session.

NOT YET VERIFIED against a live bench or a real IdP (no Frappe install is
available in the environment this was written in). Before using this in
production, at minimum:
  - Confirm _create_session_for_user() against the installed Frappe version
    (login-manager internals have shifted across versions).
  - Confirm guest POSTs to acs() aren't blocked by CSRF checks on this bench's
    configuration.
  - Run a full SP-initiated login against a real IdP (Okta/Azure AD/
    SimpleSAMLphp) in a test environment.
"""

import frappe
from frappe import _
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.settings import OneLogin_Saml2_Settings


def get_settings():
	return frappe.get_single("LMS SAML Settings")


def is_enabled() -> bool:
	settings = get_settings()
	return bool(settings.enabled and settings.idp_entity_id and settings.idp_sso_url and settings.idp_x509_cert)


def _acs_url() -> str:
	return frappe.utils.get_url("/api/method/lms.lms.integrations.saml_sso.acs")


def _metadata_url() -> str:
	return frappe.utils.get_url("/api/method/lms.lms.integrations.saml_sso.metadata")


def _build_saml_settings_dict() -> dict:
	settings = get_settings()
	return {
		"strict": True,
		"sp": {
			"entityId": settings.sp_entity_id or _metadata_url(),
			"assertionConsumerService": {
				"url": _acs_url(),
				"binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
			},
			"NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
		},
		"idp": {
			"entityId": settings.idp_entity_id,
			"singleSignOnService": {
				"url": settings.idp_sso_url,
				"binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
			},
			"x509cert": settings.idp_x509_cert,
		},
	}


def _build_request_data() -> dict:
	"""python3-saml wants a WSGI-shaped dict, not the Werkzeug request object
	Frappe exposes — this is the (thin) adapter between the two."""
	request = frappe.local.request
	is_https = request.scheme == "https"
	default_port = "443" if is_https else "80"
	return {
		"https": "on" if is_https else "off",
		"http_host": request.host.split(":")[0],
		"server_port": request.host.split(":")[1] if ":" in request.host else default_port,
		"script_name": request.path,
		"get_data": request.args.to_dict(),
		"post_data": request.form.to_dict(),
	}


def _get_auth() -> OneLogin_Saml2_Auth:
	return OneLogin_Saml2_Auth(_build_request_data(), _build_saml_settings_dict())


@frappe.whitelist(allow_guest=True)
def login():
	if not is_enabled():
		frappe.throw(_("SAML SSO is not configured."))

	auth = _get_auth()
	redirect_url = auth.login(return_to=frappe.utils.get_url("/lms"))
	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = redirect_url


@frappe.whitelist(allow_guest=True)
def metadata():
	saml_settings = OneLogin_Saml2_Settings(_build_saml_settings_dict(), sp_validation_only=True)
	frappe.local.response["type"] = "binary"
	frappe.local.response["filename"] = "metadata.xml"
	frappe.local.response["filecontent"] = saml_settings.get_sp_metadata()
	frappe.local.response["content_type"] = "text/xml"


@frappe.whitelist(allow_guest=True)
def acs():
	if not is_enabled():
		frappe.throw(_("SAML SSO is not configured."))

	auth = _get_auth()
	auth.process_response()

	errors = auth.get_errors()
	if errors:
		frappe.logger("lms.security").warning("SAML ACS rejected: %s", errors)
		frappe.throw(_("SAML authentication failed."), frappe.AuthenticationError)

	if not auth.is_authenticated():
		frappe.throw(_("SAML authentication failed."), frappe.AuthenticationError)

	settings = get_settings()
	attributes = auth.get_attributes()
	email = _first(attributes.get(settings.email_attribute)) or auth.get_nameid()
	if not email:
		frappe.throw(_("SAML assertion did not include an email address."))

	user = _resolve_user(email, settings)
	_create_session_for_user(user)

	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = "/lms"


def _first(value):
	if isinstance(value, list):
		return value[0] if value else None
	return value


def _resolve_user(email: str, settings) -> str:
	if frappe.db.exists("User", email):
		return email

	if not settings.auto_provision_users:
		frappe.throw(_("No account found for {0}.").format(email), frappe.AuthenticationError)

	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": email.split("@")[0],
			"send_welcome_email": 0,
			"roles": [{"role": settings.default_role}] if settings.default_role else [],
		}
	)
	user.flags.ignore_permissions = True
	user.insert()
	return user.name


def _create_session_for_user(user: str):
	"""Logs `user` in without a password, since the IdP already authenticated
	them. UNVERIFIED against the installed Frappe version — login_manager's
	internals (the exact attribute/method names below) have changed across
	Frappe releases; confirm this against the actual site before relying on it."""
	frappe.local.login_manager.user = user
	frappe.local.login_manager.post_login()
