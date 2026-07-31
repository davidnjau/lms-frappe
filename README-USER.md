# Courses, Batches, and Programs — What's the Difference?

This app has three related but distinct concepts. They're easy to mix up because
they all involve "learners going through content," but each solves a different
problem. This doc explains what each one is, how they're structured, and how
they connect to each other.

---

## Course — the actual content

A **Course** is the atomic unit of learning content. Everything a learner
actually reads, watches, or does lives inside a course.

**Structure:** Course → Chapters → Lessons. A lesson can contain markdown text,
video, audio, embedded content, quizzes, assignments, or a SCORM/H5P package.

**Key properties:**
- Can be **free or paid** (`paid_course`, with its own price/currency)
- Can require a **certificate on completion** (`enable_certification`)
- Has its own **rating/reviews**, category, and instructor(s)
- Can be **published or draft**

**Enrollment:** A learner can enroll in a course in three ways:
1. Directly, by themselves (self-paced)
2. As part of joining a **Batch** that includes this course
3. As part of joining a **Program** that includes this course

Every enrollment — however it happened — is tracked in one place
(`LMS Enrollment`), which also records progress (`current_lesson`, `progress`)
and whether a certificate was purchased/issued.

**Think of a Course as:** the textbook. It doesn't have a start date or a
teacher attached to a specific run — it's the content itself, reusable across
any number of batches, programs, or standalone learners.

---

## Batch — a scheduled, cohort-based delivery of a course

A **Batch** is a specific, time-boxed *offering* of one or more courses to a
group of learners at the same time — closer to "a semester" or "a live
cohort" than to the content itself.

**Key properties:**
- Has a **start date and end date**, start/end time, and timezone
- Groups one or more **courses** together (a batch isn't limited to one course)
- Can be **Online or Offline**, and can run **live classes** via Zoom or
  Google Meet, with a **timetable**
- Has its own **instructors** and (optionally) a **seat limit**
- Can have its **own pricing**, separate from the courses' individual prices
- Can require an **evaluation** step before certification
- Can be self-enrollable, or admin-added only

**Enrollment:** Joining a batch (`LMS Batch Enrollment`) automatically enrolls
the learner in the batch's courses too — that's what `enrollment_from_batch`
tracks on the underlying `LMS Enrollment` record.

**Think of a Batch as:** a class section. Same textbook (course) as another
batch might use, but a specific group of students, a specific teacher, a
specific schedule, and possibly a different price — e.g. "Credit Risk 101 —
January 2026 Cohort" vs. "Credit Risk 101 — March 2026 Cohort," both delivering
the same underlying course.

---

## Program — a curated multi-course learning path

A **Program** is a *curriculum*: an ordered (or unordered) collection of
courses that together make up a larger learning journey, tracked as one
enrollment.

**Key properties:**
- Contains a list of **courses** (`program_courses`), in a defined sequence
- Can **enforce course order** — a learner must finish course 1 before
  course 2 unlocks (`enforce_course_order`)
- Tracks **program-level progress** across all its courses, not just one
- Has its own **member list** (`program_members`) separate from each
  individual course's enrollment list

**Enrollment:** Joining a program enrolls the learner in all of the program's
courses at once. Unlike a batch, a program has no start/end date, no live
classes, and no pricing of its own — it's a self-paced path through existing
courses.

**Think of a Program as:** a degree plan or certification track — "Complete
these 5 courses, in this order, to become certified in Credit Risk
Management." It doesn't care when you start or whether you're doing it live
with a cohort; it just defines the path and enforces (optionally) the order.

---

## Putting it together

| | Course | Batch | Program |
|---|---|---|---|
| **What it is** | The content itself | A scheduled, live/cohort delivery of course(s) | A curated multi-course path |
| **Contains** | Chapters → Lessons | One or more Courses | One or more Courses (ordered) |
| **Has a schedule?** | No | Yes (start/end date, timetable, live classes) | No |
| **Has its own price?** | Yes (optional) | Yes (optional, separate from course price) | No |
| **Enforces order?** | N/A (chapters are already ordered) | No | Optional (`enforce_course_order`) |
| **Typical use case** | Self-paced learning | "January 2026 live cohort" | "Certification track" / curriculum |

A single course can be used inside many different batches and many different
programs at the same time — that's the whole point of separating the content
(course) from how it's delivered (batch) and how it's sequenced into a bigger
path (program).

**Example:** Centafrique could have one course, *"Introduction to Credit
Risk,"* that is:
- Sold standalone to individual learners,
- Delivered live every quarter as a **Batch** ("Q1 2026 Cohort," "Q2 2026
  Cohort," each with its own instructor and schedule), and
- Included as course #1 in a **Program** called "Credit Risk Management
  Certification," alongside four other courses that must be completed in
  order.

---

## Where to find these in the app

- **Courses:** `/lms/courses`
- **Batches:** `/lms/batches`
- **Programs:** `/lms/programs`

Each has a corresponding Desk doctype for admins: `LMS Course`, `LMS Batch`,
`LMS Program` (plus their child tables: `Course Chapter`/`Course Lesson`,
`Batch Course`, `LMS Program Course`/`LMS Program Member`).
