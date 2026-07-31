"""Shared Claude API client/usage-tracking helpers for the AI Tutor, AI
Translation, and AI Course Author features (Phase 3 of
centop_lms_implementation.md).

Credentials are never stored in a Frappe doctype: `anthropic.Anthropic()`
with no arguments resolves ANTHROPIC_API_KEY from the process environment,
matching this codebase's "use environment variables for secrets" convention
for infrastructure-level (not per-tenant) credentials.
"""

import anthropic
import frappe
from frappe import _

MODEL = "claude-opus-4-8"


def get_settings():
	return frappe.get_single("LMS AI Settings")


def get_client() -> anthropic.Anthropic:
	return anthropic.Anthropic()


def enforce_enabled_and_budget():
	"""Kill switch + daily cost cap, checked before every AI feature call."""
	settings = get_settings()
	if not settings.enabled:
		frappe.throw(_("AI features are currently disabled."))

	if not settings.daily_token_budget:
		return

	used = (
		frappe.db.sql(
			"""select coalesce(sum(input_tokens + output_tokens), 0)
			from `tabLMS AI Usage Log`
			where date(creation) = curdate()"""
		)[0][0]
		or 0
	)
	if used >= settings.daily_token_budget:
		frappe.throw(_("The daily AI usage budget has been reached. Please try again tomorrow."))


def log_usage(feature: str, usage, model: str = MODEL):
	frappe.get_doc(
		{
			"doctype": "LMS AI Usage Log",
			"member": frappe.session.user,
			"feature": feature,
			"model": model,
			"input_tokens": usage.input_tokens,
			"output_tokens": usage.output_tokens,
		}
	).insert(ignore_permissions=True)
