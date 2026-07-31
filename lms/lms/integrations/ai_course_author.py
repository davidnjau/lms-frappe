"""AI Course Author (§7.6) — drafts course outlines and quiz questions for a
course instructor to review and edit. Never writes LMS Course/Chapter/Lesson/
Quiz records directly: everything returned here is a draft the frontend shows
for human review before anything is actually created, per this feature's
explicit non-goal of auto-publishing content."""

import frappe
from frappe import _
from pydantic import BaseModel

from lms.lms.integrations.ai_client import MODEL, enforce_enabled_and_budget, get_client, log_usage
from lms.lms.utils import can_modify_course, has_course_instructor_role, has_moderator_role


class ChapterDraft(BaseModel):
	title: str
	lessons: list[str]


class CourseOutlineDraft(BaseModel):
	title: str
	learning_objectives: list[str]
	chapters: list[ChapterDraft]


class QuizQuestionDraft(BaseModel):
	question: str
	options: list[str]
	correct_option_index: int
	explanation: str


class QuizDraft(BaseModel):
	questions: list[QuizQuestionDraft]


def _require_course_author_role():
	if not (has_course_instructor_role() or has_moderator_role()):
		frappe.throw(_("You do not have permission to draft course content."), frappe.PermissionError)


@frappe.whitelist()
def draft_course_outline(topic: str, level: str = "Beginner") -> dict:
	if not isinstance(topic, str) or not topic.strip():
		frappe.throw(_("topic is required"))

	_require_course_author_role()
	enforce_enabled_and_budget()

	client = get_client()
	message = client.messages.parse(
		model=MODEL,
		max_tokens=4096,
		thinking={"type": "adaptive"},
		system=(
			"You draft course outlines for a professional/executive-education "
			"platform. Produce a coherent, well-sequenced outline — this is a "
			"draft for a human course author to edit, not a final course."
		),
		messages=[
			{
				"role": "user",
				"content": f"Draft a course outline on '{topic}' for a {level} audience.",
			}
		],
		output_format=CourseOutlineDraft,
	)

	log_usage("Course Author", message.usage)
	if not message.parsed_output:
		frappe.throw(_("Could not generate a course outline. Please try again."))
	return message.parsed_output.model_dump()


@frappe.whitelist()
def draft_quiz_questions(lesson: str, count: int = 5) -> dict:
	lesson_details = frappe.db.get_value("Course Lesson", lesson, ["title", "body", "course"], as_dict=True)
	if not lesson_details:
		frappe.throw(_("Lesson not found."))
	if not can_modify_course(lesson_details.course):
		frappe.throw(_("You do not have permission to draft quiz questions for this course."), frappe.PermissionError)

	enforce_enabled_and_budget()
	count = max(1, min(int(count), 20))

	client = get_client()
	message = client.messages.parse(
		model=MODEL,
		max_tokens=4096,
		thinking={"type": "adaptive"},
		system=(
			"You draft multiple-choice quiz questions from lesson content, for a "
			"course instructor to review and edit before publishing. Each question "
			"must have exactly one correct option."
		),
		messages=[
			{
				"role": "user",
				"content": (
					f"Draft {count} multiple-choice questions (4 options each) testing "
					f"comprehension of this lesson, titled '{lesson_details.title}':\n\n"
					f"{(lesson_details.body or '')[:6000]}"
				),
			}
		],
		output_format=QuizDraft,
	)

	log_usage("Course Author", message.usage)
	if not message.parsed_output:
		frappe.throw(_("Could not generate quiz questions. Please try again."))
	return message.parsed_output.model_dump()
