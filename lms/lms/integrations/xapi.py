"""Minimal internal xAPI (Tin Can) statement store — deliberately not a
general-purpose LRS (no full xAPI query/auth spec, no multi-tenant actor
trust). Accepts a standard-shaped xAPI statement, always attributes it to the
logged-in session user (never the client-supplied actor — this store is for
this site's own learners, not third-party statement federation), and stores
it alongside optional course/lesson context for reporting.

Content hosting: an xAPI activity built with an external authoring tool
(Articulate Storyline, Adapt, iSpring, etc.) already has a player URL that can
be embedded via the existing generic `Embed` markdown macro
(lms/plugins.py:embed_renderer) — no separate xAPI page renderer or package-
extraction pipeline is added here. Self-hosting an xAPI zip package the way
SCORM packages are extracted/served would mean either generalizing or
duplicating lms/page_renderers.py's SCORMRenderer and the extraction path-
safety logic in lms/lms/api.py, both security-reviewed code; that's left as
follow-up work rather than rushed here.
"""

import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime

from lms.lms.utils import can_modify_course


def _first_text(value):
	"""Pulls a display string out of an xAPI langmap ({"en-US": "..."}) or a
	bare string, whichever the statement used."""
	if isinstance(value, dict):
		return next(iter(value.values()), None)
	return value


@frappe.whitelist()
def record_statement(statement: dict, course: str | None = None, lesson: str | None = None) -> str:
	if not isinstance(statement, dict):
		frappe.throw(_("statement must be an object"))

	verb = statement.get("verb") or {}
	verb_label = _first_text(verb.get("display")) or verb.get("id")
	obj = statement.get("object") or {}
	object_id = obj.get("id")

	if not verb_label or not object_id:
		frappe.throw(_("A valid xAPI statement requires verb and object.id."))

	result = statement.get("result") or {}
	score = result.get("score") or {}
	success = result.get("success")

	timestamp = statement.get("timestamp")
	try:
		timestamp = get_datetime(timestamp) if timestamp else now_datetime()
	except Exception:
		timestamp = now_datetime()

	doc = frappe.get_doc(
		{
			"doctype": "LMS xAPI Statement",
			# Always the session user, never statement.actor — this store isn't a
			# federated LRS, so the client-supplied actor identity isn't trusted.
			"member": frappe.session.user,
			"verb": verb_label,
			"object_id": object_id,
			"object_name": _first_text((obj.get("definition") or {}).get("name")),
			"course": course,
			"lesson": lesson,
			"completion": 1 if result.get("completion") else 0,
			"success": "" if success is None else ("True" if success else "False"),
			"score_scaled": score.get("scaled"),
			"statement_timestamp": timestamp,
			"raw_statement": frappe.as_json(statement),
		}
	)
	doc.insert(ignore_permissions=False)
	return doc.name


@frappe.whitelist()
def get_statements(course: str | None = None, member: str | None = None) -> list[dict]:
	filters = {}
	if course:
		filters["course"] = course

	if member and member != frappe.session.user:
		# Explicit check here rather than relying on doctype-level permission
		# propagation through get_list, which isn't guaranteed to filter rows
		# for this kind of cross-member query — this is a permission-sensitive
		# read, so the authorization is enforced directly in this function.
		roles = frappe.get_roles()
		is_moderator = "System Manager" in roles or "Moderator" in roles
		if not is_moderator and not (course and can_modify_course(course)):
			frappe.throw(_("You do not have permission to view this member's statements."), frappe.PermissionError)
		filters["member"] = member
	else:
		filters["member"] = frappe.session.user

	return frappe.get_list(
		"LMS xAPI Statement",
		filters=filters,
		fields=[
			"name",
			"member",
			"verb",
			"object_id",
			"object_name",
			"course",
			"lesson",
			"completion",
			"success",
			"score_scaled",
			"statement_timestamp",
		],
		order_by="statement_timestamp desc",
		ignore_permissions=True,
	)
