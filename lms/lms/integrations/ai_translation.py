"""AI Translation (§7.6 of CENTOP_ACADEMY_IMPLEMENTATION.md) — translates a
single doctype field (lesson body, course description, ...) on demand and
caches the result in LMS Content Translation, keyed by a hash of the source
text so a source edit invalidates the cached translation automatically."""

import hashlib

import frappe
from frappe import _

from lms.lms.integrations.ai_client import MODEL, enforce_enabled_and_budget, get_client, log_usage

SUPPORTED_LANGUAGES = {
	"sw": "Swahili",
	"fr": "French",
	"ar": "Arabic",
	"pt": "Portuguese",
}


def _content_hash(text: str) -> str:
	return hashlib.sha256(text.encode()).hexdigest()


@frappe.whitelist()
def translate_content(doctype: str, docname: str, fieldname: str, language: str) -> str:
	if language not in SUPPORTED_LANGUAGES:
		frappe.throw(_("Unsupported language: {0}").format(language))

	frappe.has_permission(doctype, doc=docname, ptype="read", throw=True)

	source_text = frappe.db.get_value(doctype, docname, fieldname)
	if not source_text:
		return ""

	source_hash = _content_hash(source_text)
	cached = frappe.db.get_value(
		"LMS Content Translation",
		{
			"reference_doctype": doctype,
			"reference_name": docname,
			"fieldname": fieldname,
			"language": language,
			"source_hash": source_hash,
		},
		"translated_text",
	)
	if cached is not None:
		return cached

	enforce_enabled_and_budget()
	translated_text = _translate_text(source_text, SUPPORTED_LANGUAGES[language])

	existing = frappe.db.exists(
		"LMS Content Translation",
		{
			"reference_doctype": doctype,
			"reference_name": docname,
			"fieldname": fieldname,
			"language": language,
		},
	)
	if existing:
		frappe.db.set_value(
			"LMS Content Translation",
			existing,
			{"translated_text": translated_text, "source_hash": source_hash},
		)
	else:
		frappe.get_doc(
			{
				"doctype": "LMS Content Translation",
				"reference_doctype": doctype,
				"reference_name": docname,
				"fieldname": fieldname,
				"language": language,
				"source_hash": source_hash,
				"translated_text": translated_text,
			}
		).insert(ignore_permissions=True)

	return translated_text


def _translate_text(text: str, target_language: str) -> str:
	client = get_client()
	with client.messages.stream(
		model=MODEL,
		max_tokens=8192,
		system=(
			"You are a professional translator for an online learning platform. "
			"Translate the user's message into the target language. Preserve markdown "
			"formatting and technical/finance terminology. Return ONLY the translated "
			"text — no preamble, no explanation, no quotes around it."
		),
		messages=[{"role": "user", "content": f"Target language: {target_language}\n\n{text}"}],
	) as stream:
		message = stream.get_final_message()

	log_usage("Translation", message.usage)
	return "".join(block.text for block in message.content if block.type == "text")
