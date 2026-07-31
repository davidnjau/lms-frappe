"""AI Learning Assistant (§7.6) — progress nudges for stalled learners. No LLM
call for this MVP: reuses the existing daily-reminder scheduled-job pattern
(see send_batch_start_reminder in lms/lms/doctype/lms_batch/lms_batch.py) —
an actual personalized/AI-generated nudge message is a natural follow-up once
this plain version is in place."""

import frappe
from frappe import _
from frappe.utils import add_days, nowdate

NUDGE_AFTER_DAYS = 7


def send_learning_nudges():
	outgoing_email_account = frappe.get_cached_value(
		"Email Account", {"default_outgoing": 1, "enable_outgoing": 1}, "name"
	)
	if not (outgoing_email_account or frappe.conf.get("mail_login")):
		return

	stalled_date = add_days(nowdate(), -NUDGE_AFTER_DAYS)
	stalled_members = frappe.db.sql(
		"""
		select e.member, e.member_name, e.course, c.title as course_title
		from `tabLMS Enrollment` e
		join `tabLMS Course` c on c.name = e.course
		where (e.progress is null or e.progress < 100)
		and date(
			(select max(modified) from `tabLMS Course Progress` p
				where p.course = e.course and p.member = e.member)
		) = %(stalled_date)s
		""",
		{"stalled_date": stalled_date},
		as_dict=True,
	)

	for enrollment in stalled_members:
		send_nudge_mail(enrollment)


def send_nudge_mail(enrollment):
	frappe.sendmail(
		recipients=enrollment.member,
		subject=_("Keep going with {0}").format(enrollment.course_title),
		template="learning_nudge",
		args={
			"student_name": enrollment.member_name,
			"course_title": enrollment.course_title,
			"course": enrollment.course,
		},
		header=[_("You're close — keep learning"), "blue"],
		retry=3,
	)
