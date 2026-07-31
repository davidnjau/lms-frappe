"""AI Tutor (§7.6) — answers a learner's question grounded in the lesson/course
they're currently viewing. Single-turn per call; the frontend carries
conversation history in `history` and resends it, so no server-side chat
storage is needed for this MVP."""

import frappe
from frappe import _

from lms.lms.integrations.ai_client import MODEL, enforce_enabled_and_budget, get_client, log_usage
from lms.lms.permissions import can_access_lesson
from lms.lms.utils import can_modify_course, get_membership

MAX_CONTEXT_CHARS = 6000

SYSTEM_PROMPT = (
	"You are an AI tutor embedded in an online learning platform. Answer the "
	"learner's question clearly and pedagogically, grounded in the lesson/course "
	"context provided. If the context doesn't cover the question, say so rather "
	"than guessing. Keep answers focused — a few short paragraphs, not an essay. "
	"Never write answer keys for graded quizzes or assignments; explain concepts, "
	"don't hand over graded answers."
)


def _check_context_permission(course: str | None, lesson: str | None):
	if lesson:
		if not can_access_lesson(lesson):
			frappe.throw(_("You do not have access to this lesson."), frappe.PermissionError)
	elif course:
		if not (get_membership(course) or can_modify_course(course)):
			frappe.throw(_("You do not have access to this course."), frappe.PermissionError)


def _build_context(course: str | None, lesson: str | None) -> str:
	if lesson:
		details = frappe.db.get_value("Course Lesson", lesson, ["title", "body", "course"], as_dict=True)
		if details:
			course_title = frappe.db.get_value("LMS Course", details.course, "title")
			body = (details.body or "")[:MAX_CONTEXT_CHARS]
			return f"Course: {course_title}\nLesson: {details.title}\n\n{body}"

	if course:
		details = frappe.db.get_value("LMS Course", course, ["title", "description"], as_dict=True)
		if details:
			return f"Course: {details.title}\n\n{(details.description or '')[:MAX_CONTEXT_CHARS]}"

	return ""


@frappe.whitelist()
def ask_tutor(
	question: str,
	course: str | None = None,
	lesson: str | None = None,
	history: list | None = None,
) -> dict:
	if not isinstance(question, str) or not question.strip():
		frappe.throw(_("question is required"))

	_check_context_permission(course, lesson)
	enforce_enabled_and_budget()

	context = _build_context(course, lesson)
	messages = list(history or [])
	user_content = f"Context:\n{context}\n\nQuestion: {question}" if context else question
	messages.append({"role": "user", "content": user_content})

	client = get_client()
	with client.messages.stream(
		model=MODEL,
		max_tokens=2048,
		system=SYSTEM_PROMPT,
		thinking={"type": "adaptive"},
		messages=messages,
	) as stream:
		message = stream.get_final_message()

	log_usage("Tutor", message.usage)
	answer = "".join(block.text for block in message.content if block.type == "text")
	return {"answer": answer}
