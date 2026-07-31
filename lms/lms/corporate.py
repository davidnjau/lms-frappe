import frappe
from frappe.utils import flt

from lms.lms.utils import get_course_progress


@frappe.whitelist()
def get_corporate_account_summary(corporate_account: str) -> dict:
	frappe.has_permission("LMS Corporate Account", doc=corporate_account, ptype="read", throw=True)

	members = frappe.get_all(
		"LMS Corporate Member",
		filters={"parent": corporate_account},
		fields=["member", "full_name", "role"],
	)

	return {
		"corporate_account": corporate_account,
		"member_count": len(members),
		"batch_count": frappe.db.count("LMS Batch", {"corporate_account": corporate_account}),
		"program_count": frappe.db.count("LMS Program", {"corporate_account": corporate_account}),
		"members": members,
	}


@frappe.whitelist()
def get_corporate_learner_progress(corporate_account: str) -> list[dict]:
	frappe.has_permission("LMS Corporate Account", doc=corporate_account, ptype="read", throw=True)

	members = frappe.get_all(
		"LMS Corporate Member",
		filters={"parent": corporate_account},
		fields=["member", "full_name"],
	)
	courses = get_corporate_account_courses(corporate_account)

	report = []
	for member in members:
		course_progress = {course: get_course_progress(course, member.member) for course in courses}
		average_progress = flt(sum(course_progress.values()) / len(course_progress)) if course_progress else 0
		report.append(
			{
				"member": member.member,
				"full_name": member.full_name,
				"course_progress": course_progress,
				"average_progress": average_progress,
			}
		)

	return report


def get_corporate_account_courses(corporate_account: str) -> list[str]:
	batch_names = frappe.get_all("LMS Batch", filters={"corporate_account": corporate_account}, pluck="name")
	program_names = frappe.get_all(
		"LMS Program", filters={"corporate_account": corporate_account}, pluck="name"
	)

	courses = set()
	if batch_names:
		courses.update(frappe.get_all("Batch Course", filters={"parent": ["in", batch_names]}, pluck="course"))
	if program_names:
		courses.update(
			frappe.get_all("LMS Program Course", filters={"parent": ["in", program_names]}, pluck="course")
		)

	return list(courses)
