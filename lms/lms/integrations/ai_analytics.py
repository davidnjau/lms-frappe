"""AI Analytics (§7.6) — completion/dropout risk signal, scoped to Phase 3's
MVP plan: a simple engagement-recency heuristic, not an LLM call or trained
model. Validate this adds value before reaching for anything heavier."""

import frappe
from frappe import _
from frappe.utils import date_diff, nowdate

from lms.lms.utils import can_modify_course, get_course_progress


def _risk_label(days_since_activity: int | None, completion_percent: float) -> str:
	if completion_percent >= 100:
		return "Completed"
	if days_since_activity is None or days_since_activity > 21:
		return "High"
	if days_since_activity > 7 or completion_percent < 25:
		return "Medium"
	return "Low"


@frappe.whitelist()
def get_completion_risk(course: str) -> list[dict]:
	if not can_modify_course(course):
		frappe.throw(_("You do not have permission to view analytics for this course."), frappe.PermissionError)

	members = frappe.get_all(
		"LMS Enrollment", filters={"course": course}, fields=["member", "member_name"]
	)

	report = []
	for member in members:
		last_activity = frappe.db.get_value(
			"LMS Course Progress",
			{"course": course, "member": member.member},
			"modified",
			order_by="modified desc",
		)
		days_since_activity = date_diff(nowdate(), last_activity) if last_activity else None
		completion_percent = get_course_progress(course, member.member)

		report.append(
			{
				"member": member.member,
				"member_name": member.member_name,
				"completion_percent": completion_percent,
				"days_since_activity": days_since_activity,
				"risk": _risk_label(days_since_activity, completion_percent),
			}
		)

	return report
