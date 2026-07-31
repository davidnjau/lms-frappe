# CENTOP Academy — LMS Implementation Plan
## Phased Build Scope (grounded in current repo state)

> Companion to `CENTOP_ACADEMY_IMPLEMENTATION.md` (the converted ToR spec). That document defines *what* was asked for; this document defines *what to actually build in this repo, in what order*, based on what already exists today. Doctype/file names below use this repo's real naming conventions — verify against `lms/lms/doctype/` before implementing, since schemas evolve.

---

## 0. Current-State Inventory (baseline, as of this plan)

**Already solid — extend, don't rebuild:**
- Course/chapter/lesson structure: `lms_course`, `course_chapter`, `course_lesson`, `lms_category`, `lms_course_review`, `lms_course_progress`
- Batches/cohorts: `lms_batch`, `lms_batch_enrollment`, `lms_batch_feedback`, `lms_batch_timetable`
- Programs (learning paths): `lms_program`, `lms_program_course`, `lms_program_member`
- Assessments: `lms_quiz` (+questions/results/submissions), `lms_assignment` (+submissions), `lms_programming_exercise` (+test cases)
- Certification: `lms_certificate`, `lms_certificate_request`, `lms_certificate_evaluation` (`certification` doctype has an `organization` field — closest existing concept to a corporate account, but scoped to certifying bodies)
- Instructors/evaluators: `course_instructor`, `course_evaluator`, `lms_course_mentor_mapping`
- Badges/gamification: `lms_badge`, `lms_badge_assignment`
- Live classes: `lms_live_class` (+Zoom/Google Meet settings)
- Payments: `lms/lms/payments.py` is gateway-agnostic (delegates to `frappe/payments` app), plus `lms_payment`, `lms_coupon`
- Permissions: `lms/lms/permissions.py` + `has_permission`/`permission_query_conditions` hooks on Live Class, Batch, Program, Certificate, Course Lesson, File — a real, working access-control layer
- SCORM: `lms.page_renderers.SCORMRenderer` + `SCORMChapter.vue` (disk-based package resolution, no dedicated doctype)
- Search: `lms/sqlite.py` `LearningSearch` — indexes Course and Batch only

**Confirmed gaps (nothing to extend — genuinely new work):**
- No corporate-account, subscription, or membership doctype (payments model is one-time/per-course only)
- No CRM integration of any kind (no Zoho, no generic CRM sync)
- No AI/LLM integration anywhere in the codebase (zero matches for openai/anthropic/bedrock/llm)
- No SCORM-package doctype (disk-based only); no xAPI/H5P support
- Search index covers Course/Batch only — lessons, quizzes, assignments aren't searchable
- No SAML SP (Social Login Keys cover OAuth2 social login only, not SAML federation)
- No corporate-admin frontend surface (`frontend/src/pages/` has no Organization/Corporate pages; `frontend/src/stores/` has no org/subscription store)

This inventory is what makes the phasing below realistic: Phases 1–2 close gaps in an already-strong core; Phases 3–4 are closer to greenfield.

---

## Phase 1 — Core Platform Gap-Closing

**Goal:** make the existing course/batch/program/certificate system corporate-account-aware, since almost nothing here currently models "an organization with multiple learners" as a first-class concept.

| Task | Detail |
|---|---|
| New doctype: `LMS Corporate Account` | Org name, industry, primary contact, billing details, seat count/license type, status (active/suspended) |
| New doctype: `LMS Corporate Member` | Links `User` ↔ `LMS Corporate Account`, role within org (admin/learner), department/branch/team fields per §7.1 org hierarchy |
| Extend `lms_program`/`lms_batch` | Optional `corporate_account` link field so a program/batch can be scoped to one client — needed before any corporate reporting is possible |
| New permission hook | `has_permission`/`permission_query_conditions` for `LMS Corporate Account` in `lms/lms/permissions.py` + wire into `lms/hooks.py`, following the existing pattern for Batch/Program |
| Corporate reporting API | New whitelisted endpoints in `lms/lms/api.py` (or a new `lms/lms/corporate.py` module, given `api.py` is already 2,583 lines) — org-level completion/progress rollups |
| Search index extension | Add Lesson/Quiz/Assignment to `lms/sqlite.py` `LearningSearch` — currently Course/Batch only, and content search is a stated FR (§7.3) |

**Dependency:** this phase must land before Phase 4 (Corporate/CRM), since CRM sync and corporate portals need `LMS Corporate Account` to exist first.

---

## Phase 2 — Stack Gaps (§8.7 reconciliation items)

**Goal:** close the technical gaps flagged in `CENTOP_ACADEMY_IMPLEMENTATION.md` §8.7 that block specific BR/FR items.

| Task | Detail |
|---|---|
| SAML SSO | No first-party SAML SP in Frappe core. Evaluate a 3rd-party Frappe SAML app vs. custom `Social Login Key`-style implementation. Needed for enterprise/corporate client SSO (§7.1, §9). |
| SCORM package doctype | Promote the current disk-based SCORM handling to a proper `LMS SCORM Package` doctype (versioning, re-upload, per-course association) — needed before xAPI/H5P can be added consistently. |
| xAPI (Tin Can) support | New renderer analogous to `SCORMRenderer`; requires an LRS (Learning Record Store) — start with a minimal internal xAPI statement store, don't build a full LRS product. |
| H5P support | New markdown macro renderer in `lms/plugins.py` (alongside `Quiz`, `Video`, `Assignment`) + frontend component, following the existing `lms_markdown_macro_renderers` pattern. |
| M-Pesa gateway | `lms/lms/payments.py` already delegates to `frappe/payments` app's gateway abstraction — add an M-Pesa controller following that same interface; no core payments.py rework needed. |
| S3 file offload | Only needed if file volume/backup strategy requires it — evaluate against actual video/content storage volume before building; default local-disk storage may be sufficient at the ~500–5,000 user scale (§8.5). |
| PWA (mobile) | Add service worker + web manifest to the existing Vite build in `frontend/`; this is additive to the current Vue 3 SPA, not a rebuild. |

**Sequencing note:** SCORM-package doctype should land before xAPI/H5P (shared content-package patterns); M-Pesa and PWA are independent and can run in parallel with anything else.

---

## Phase 3 — AI Functional Requirements (§7.6)

**Goal:** none of this exists yet — this is genuinely greenfield. Scope conservatively; don't build a generic "AI platform," build the five specific capabilities the spec asks for.

| Module | Concrete scope (MVP) |
|---|---|
| **AI Tutor** | Whitelisted API endpoint that takes a lesson/course context + learner question, calls an LLM API (via Python from Frappe — no AWS lock-in required per §8.7), returns an answer. Start scoped to one course as a pilot before rolling out platform-wide. |
| **AI Learning Assistant** | Builds on Tutor's context plumbing — scheduled job (via existing `scheduler_events` pattern in `hooks.py`) that generates progress nudges/reminders, reusing the existing daily-reminder job infra already in `hooks.py`. |
| **AI Course Author** | Admin-facing tool (desk or frontend) that drafts course outlines/quiz questions from a prompt — writes into existing `lms_course`/`lms_quiz` doctypes as drafts for human review, never auto-publishes. |
| **AI Analytics** | Batch job over existing `lms_course_progress`/`lms_quiz_result`/`lms_batch_enrollment` data for completion/dropout prediction — start with simple heuristics (e.g. engagement-recency scoring) before reaching for ML models; validate the heuristic adds value before investing in a model. |
| **AI Translation** | Lowest-risk starting point — call an LLM/translation API to translate lesson content into Swahili/French/Arabic/Portuguese, store as translated copies. Can reuse Frappe's existing translation infrastructure (`lms/translations/`) as the storage pattern. |

**Recommended build order within Phase 3:** Translation → Tutor → Analytics → Course Author → Learning Assistant, ordered by risk/complexity, not spec order. Translation and Tutor are self-contained and low-risk; Course Author and Learning Assistant depend on patterns proven by the earlier two.

**Cross-cutting requirement:** every AI feature needs a kill switch (config flag) and cost/usage logging from day one — LLM API calls are the one part of this stack with real per-request cost and latency variance.

---

## Phase 4 — Corporate/CRM & Revenue (BR2/BR3)

**Goal:** the B2B/revenue side of the platform. Entirely new — depends on Phase 1's `LMS Corporate Account` doctype existing first.

| Task | Detail |
|---|---|
| Corporate portal (frontend) | New `frontend/src/pages/Corporate/` section — org dashboard, member management, org-level progress reporting. Mirrors the existing `Programs/`/`Batches/` page structure. |
| Corporate admin store | New Pinia store (`frontend/src/stores/corporate.js`) alongside existing `user.js`/`settings.js`. |
| Subscriptions/licensing | New `LMS Subscription` doctype — plan tier, seat count, renewal date, billing cycle. No recurring-billing concept exists today; `lms_payment`/`lms_coupon` are one-time-purchase only. |
| Corporate invoicing | Extend `lms/lms/payments.py` or add a sibling module for invoice generation against `LMS Corporate Account` + `LMS Subscription`. |
| Zoho CRM integration | New integration module (e.g. `lms/lms/integrations/zoho_crm.py`) — sync corporate account creation/updates to Zoho via webhook or scheduled job, following the existing `scheduler_events` pattern in `hooks.py`. No CRM integration exists today to build on. |
| Renewal management | Scheduled job (same pattern as existing payment-reminder job in `hooks.py`) to flag/notify on upcoming `LMS Subscription` renewals. |

---

## Suggested Sequencing Across Phases

1. **Phase 1** (Corporate Account foundation + search extension) — unblocks Phase 4, delivers standalone value (better search) immediately.
2. **Phase 2** (stack gaps) — mostly independent of Phase 1; can run in parallel. Prioritize M-Pesa (revenue-blocking) and SCORM-package doctype (content-blocking) over SAML/xAPI/H5P unless a specific client deal requires them sooner.
3. **Phase 3** (AI) — start after Phase 1 lands, since Analytics needs real progress data and Tutor benefits from a stable course-content shape. Translation can start anytime — no dependency.
4. **Phase 4** (Corporate/CRM) — after Phase 1's `LMS Corporate Account` exists. This is the direct revenue-generation workstream (BR2) — prioritize accordingly if commercial timelines are driving sequencing over technical dependencies.

Testing/hardening (§12 of the ToR spec) applies per-phase, not as a separate final phase — each doctype/endpoint above should ship with its own `test_<name>.py` following this repo's existing convention, not deferred to a end-of-project QA pass.
