# CENTOP Academy — Online Learning Platform
## Implementation Specification

> Converted from *Terms of Reference for Revamping/Developing CENTOP Academy* into an implementation-ready reference. Organized by build workstream so it can drive architecture decisions, sprint planning, and acceptance testing directly.

---

## 1. Context

**Client:** Centafrique Consulting — pan-African consulting firm (HQ Nairobi, Kenya) delivering advisory, research, capacity-building, and technical assistance to governments, DFIs, banks, MFIs, SACCOs, NGOs, development partners, SMEs, and private sector clients across: Financial Services Advisory, Inclusive Finance, SME/Enterprise Development, Business Advisory, Agricultural/Green/Climate Finance, Digital Transformation, Strategy & Organizational Development, Leadership Development, Project Management, MEAL, Research & Analytics, Innovation, Entrepreneurship Development, Capacity Building, and Policy Advisory.

**Goal:** Build "CENTOP Academy" — a secure, scalable, AI-enabled, cloud-native Enterprise Online Learning Platform (OLP) that becomes the firm's flagship digital training arm, replacing/extending classroom-based delivery with self-paced, instructor-led, and blended learning, digital certification, communities of practice, AI-assisted learning, mobile access, analytics, and enterprise integrations — while generating recurring revenue.

**Why now:** Digital transformation of the training/consulting industry (AI, remote work, continuous professional development demand) requires a platform that can scale training delivery, offer recognized certifications, build recurring subscription revenue, and support multilingual delivery across Africa.

---

## 2. Objectives

### 2.1 Business
- Diversify revenue via digital learning; increase regional market penetration.
- Strengthen client retention and post-consulting engagement.
- Expand knowledge products; position firm as regional thought leader.
- Improve operational efficiency and training scalability.

### 2.2 Learning
- High-quality, competency-based professional education and certification.
- Personalized, collaborative learning journeys; improved engagement and completion rates.
- Support for continuous/lifelong professional development.

### 2.3 Technology
- Secure, cloud-native, interoperable platform.
- AI-powered learning experiences; multilingual, mobile-first delivery.
- Enterprise-grade analytics; scalable for future growth (target 100,000+ users long-term).

---

## 3. Expected Deliverables (Product Outcomes)

- [ ] Fully operational enterprise OLP (cloud-hosted, highly available)
- [ ] Integrated payment gateways
- [ ] Integrated CRM and business applications
- [ ] AI-powered learner support
- [ ] Native mobile apps (Android + iOS) or justified PWA
- [ ] Enterprise analytics dashboards
- [ ] Secure digital certification (incl. QR/blockchain-ready verification)
- [ ] Learning communities / discussion forums
- [ ] Corporate client management module
- [ ] Instructor management module
- [ ] Content authoring tools
- [ ] Automated learner communications
- [ ] Modern responsive UI
- [ ] Secure authentication (MFA, SSO, federation)
- [ ] Full system documentation
- [ ] Trained administrators/trainers
- [ ] Maintenance & support arrangement in place
- [ ] Full IP/source-code ownership transferred (subject to agreed 3rd-party licensing)

---

## 4. Project Scope (End-to-End)

Business analysis → requirements → solution architecture & technology assessment → UX/UI design → development/customization → cloud infra design & deployment → AI integration → 3rd-party integrations → data migration → security hardening → performance optimization → functional/non-functional/UAT testing → deployment & go-live → training/knowledge transfer → documentation → warranty support → post-implementation maintenance planning.

---

## 5. Workstreams

### Workstream 1 — Project Inception & Planning
- Kick-off meeting
- Project charter, implementation plan, quality management plan
- Risk management framework, project monitoring framework
- Issue escalation mechanism, defined success indicators

**Deliverables:** Inception Report · Project Charter · Detailed Work Plan · Communication Plan · Risk Register · Quality Assurance Plan

### Workstream 2 — Business Analysis & Requirements Gathering
Document current business model, training operations, consulting processes, customer journey, digital maturity, operational workflows, and strategic growth objectives.

### Workstream 2 (sic, duplicated numbering in source) — Technology Assessment & Solution Recommendation

> **Decision made:** this build extends the existing Frappe Learning (LMS) app in this repository rather than evaluating Options A/B/C from a blank slate — effectively Option B/C (custom/hybrid) with Frappe as the base framework, not Moodle. The comparative evaluation below is retained for traceability against the original ToR, but §8.2–§8.7 should be read through the Frappe-stack mapping in §8.7, not as literal AWS-service requirements.

Independent assessment of three implementation options:

| Option | Description |
|---|---|
| A | Customized Moodle Workplace |
| B | Fully Custom Enterprise LMS |
| C | Hybrid Architecture |

**Evaluation criteria** (comparative matrix required, quantitative + qualitative):

| # | Area | What to assess |
|---|---|---|
| i | Initial Cost | Licensing, development, infrastructure |
| ii | Operational Cost | Annual maintenance |
| iii | Customization | Flexibility |
| iv | Scalability | Ability to support future growth |
| v | Security | Enterprise-grade capabilities |
| vi | Performance | Expected response times |
| vii | AI Readiness | Integration with Generative AI |
| viii | Integration | APIs and enterprise systems |
| ix | Ownership | Source code ownership |
| x | Vendor Lock-in | Risk analysis |
| xi | Upgrade Path | Ease of future enhancements |
| xii | Sustainability | Long-term viability |

→ Output: justified recommendation report.

### Workstream 4 — Enterprise Solution Architecture
- **Business Architecture:** capabilities, org processes, user journeys, operating model
- **Application Architecture:** LMS, CRM integration, AI services, analytics, mobile apps, payments
- **Data Architecture:** master data, metadata, data warehouse, learning records, reporting DB
- **Integration Architecture:** APIs, middleware, auth, messaging, event-driven design
- **Infrastructure Architecture:** AWS cloud, networking, security, monitoring, backup, DR

---

## 6. Business Requirements

| ID | Requirement | Must support |
|---|---|---|
| BR1 | Professional Course Delivery | Executive education, certificate courses, diploma programmes, professional development, corporate academies, custom client programmes, public training, hybrid/instructor-led/self-paced learning |
| BR2 | Revenue Generation | Individual enrolments, corporate subscriptions, annual licensing, membership models, premium content, bundles, promo pricing, affiliate programmes, corporate invoicing, discount management |
| BR3 | Client Relationship Management | Corporate accounts, client-specific portals, org reporting, learning contracts, customer support, renewal management |
| BR4 | Thought Leadership | Research publications, blogs, podcasts, webinars, knowledge repositories, digital libraries, expert communities |

---

## 7. Functional Requirements

### 7.1 User Management
**User types:** Super Administrator · System Administrator · Learning Administrator · Corporate Administrator · Trainer · Instructor · Subject Matter Expert · Course Author · Learner · Corporate Client · Finance Officer · Marketing Officer · Guest User · Technical Support

**Authentication methods:** username/password · social login (Google, Microsoft, LinkedIn) · SAML · OAuth2 · OpenID Connect · SSO · MFA

**User profile fields:** biography, organization, skills, competencies, certifications, learning history, achievements, learning goals, professional interests

**Organization management:** hierarchy, departments, branches, teams, cohorts, learning groups

### 7.2 Course Management
**Sample categories:** Banking, Agricultural Finance, Green Finance, Climate Finance, Financial Inclusion, SME Development, Digital Transformation, Strategy, Leadership, Governance, Risk Management, Credit Management, M&E, Project Management, Entrepreneurship, AI, Data Analytics, Learning Paths

**Levels/pathways:** Beginner · Intermediate · Advanced · Certification pathways · Competency pathways · Corporate learning paths

**Course features:** draft mode, scheduled publishing, version control, prerequisites, learning objectives, estimated completion time, ratings, reviews, recommendations, related courses

### 7.3 Content Management System
**Content types:** HD video, audio, PowerPoint, Word, PDF, Excel, HTML5, interactive simulations, virtual labs, case studies, templates, checklists, toolkits, podcasts, infographics

> ⚠️ **Open item from source doc:** "*Can we add SCORM / xAPI / H5P*" — flagged in the original ToR as an unresolved question. Recommend resolving during Workstream 4 (architecture) since it directly affects the LMS vs. custom-build decision (Section 5) and interoperability requirements (§8.6).

**Authoring support:** online editing, versioning, approval workflows, collaborative authoring, metadata tagging, search optimization

### 7.4 Assessment & Exam Management
**Types:** quizzes, MCQ, true/false, matching, essay, short answer, practical assignments, simulations, capstone projects

**Exam features:** randomized questions, question pools, time limits, negative marking, multiple attempts, auto/manual grading, rubrics, secure browser support, online proctoring integration, AI-assisted grading, plagiarism detection

### 7.5 Certification Management
Professional certificates · CPD certificates · completion certificates · achievement badges · digital wallet · blockchain-ready verification · QR verification · certificate expiry & renewal

### 7.6 AI Functional Requirements

| Module | Capabilities |
|---|---|
| **AI Tutor** | Answer learner questions, explain concepts, recommend resources, provide study plans, offer revision guidance |
| **AI Learning Assistant** | Personalized learning pathways, adaptive learning, competency recommendations, learning reminders, progress coaching, intelligent notifications |
| **AI Course Author** | Draft course outlines, create assessments/quizzes, generate learning objectives, content summaries, interactive activities |
| **AI Analytics** | Completion prediction, dropout prediction, skill gap analysis, competency mapping, learning recommendations, organizational capability reports |
| **AI Translation** | English, Swahili, French, Arabic, Portuguese — with provision for additional African languages |

---

## 8. Integration & Technical Architecture

### 8.1 Enterprise Integrations Required

| Category | Systems |
|---|---|
| CRM | Zoho CRM |
| Productivity | Microsoft 365, Outlook, Teams, SharePoint |
| Finance | Accounting software, ERP systems |
| Payments | M-Pesa, Stripe, PayPal, Visa, Mastercard, Bank transfer |
| Virtual Learning | Zoom, Microsoft Teams, Google Meet |
| Marketing | Mailchimp, Zoho Campaigns, LinkedIn, Facebook, X, YouTube |

### 8.2 Preferred Cloud Platform: AWS (unless an alternative demonstrates clear advantages)

| Layer | Suggested AWS Services | Frappe-native equivalent |
|---|---|---|
| Compute | EC2, ECS, EKS | Bench processes (gunicorn + socketio + workers) on EC2, or containerized via `frappe_docker` on ECS/EKS |
| Storage | S3, EBS, EFS | Local disk (public/private files) by default; S3 offload needs a 3rd-party attachment app |
| Database | ~~RDS PostgreSQL, Aurora~~ RDS for MariaDB (or self-managed MariaDB/Galera for HA) | MariaDB is Frappe's supported DB engine — no Postgres |
| Authentication | ~~Amazon Cognito~~ not used | Frappe User doctype + session/token auth + Social Login Keys (OAuth2) + built-in 2FA |
| CDN | CloudFront | unchanged — serves built frontend assets/`lms/public` |
| DNS | Route 53 | unchanged |
| Monitoring | CloudWatch | CloudWatch + Frappe error log / Sentry integration |
| Logging | CloudTrail | unchanged (infra-level); app-level logs are Frappe's own |
| Secrets | AWS Secrets Manager | unchanged, or bench `site_config.json` for app-level config |
| Backup | AWS Backup | AWS Backup + bench's built-in `bench backup` for site/DB backups |
| Security | AWS WAF, AWS Shield, IAM, GuardDuty | unchanged — infra-level, orthogonal to app stack |
| AI Services | Amazon Bedrock (or equivalent), SageMaker | any LLM API called from Python — no AWS lock-in required |
| Notifications | SNS, SES | Frappe Email Queue + Notification doctype; SMS needs a gateway integration either way |
| Queueing | ~~SQS~~ | Redis Queue (RQ) — Frappe's native background job queue (`lms/hooks.py` scheduler_events); SQS only if bridging to external services |
| Workflow | ~~Step Functions~~ | Frappe scheduler + doc-event hooks; Step Functions only for cross-service orchestration outside Frappe |

### 8.7 Reconciliation with Existing Frappe Stack

This spec's original service references (§8.2, §9, §10) were written cloud/stack-agnostic. Since the build target is this repository, the table below flags what's already implemented vs. a genuine gap.

| ToR Requirement | Status in this repo |
|---|---|
| Social login (Google/Microsoft) | Supported out of box via Social Login Key doctype; LinkedIn needs a custom OAuth provider entry |
| SAML SSO | Gap — no first-party SAML SP in Frappe core; needs a custom app or 3rd-party add-on |
| MFA | Existing — built-in two-factor auth (System Settings) |
| Search | Existing — `lms/sqlite.py` `LearningSearch` (SQLite FTS), not Elasticsearch/OpenSearch |
| Payments | Existing base — `frappe/payments` app + `lms/lms/payments.py` (Stripe/PayPal/Razorpay-style gateways); M-Pesa needs a custom gateway |
| SCORM | Partially existing — `lms.page_renderers.SCORMRenderer`, `SCORMChapter.vue` |
| xAPI / H5P | Not present — still an open item (§16.2) |
| Containerized deploy | No k8s manifests in this repo today — `frappe_docker` is the standard path if containerization is required |
| AI Tutor/Assistant/Author/Analytics/Translation (§7.6) | Not yet implemented in this repo |

### 8.3 Architectural Principles
Cloud-native · API-first · containerization (Docker via `frappe_docker`, Kubernetes optional) · Infrastructure as Code (Terraform/CloudFormation) · DevSecOps · CI/CD · modular/extensible · high availability · fault tolerance · horizontal scalability · Zero Trust security.

> Frappe is a monolithic app framework by design — modularity is achieved through doctypes/modules within this single codebase (`lms/`), not service-per-repo microservices. Reserve true microservices for workloads that don't fit the Frappe/Python runtime (e.g. a dedicated AI inference service), not for core LMS functionality.

### 8.4 Performance Requirements (minimum standards)

| Requirement | Minimum Standard |
|---|---|
| Average page load time | ≤ 2 seconds |
| Login response time | ≤ 3 seconds |
| Search results | ≤ 2 seconds |
| Course enrollment | ≤ 5 seconds |
| Video buffering | < 2 seconds on broadband |
| API response time | ≤ 500 ms |
| Concurrent users | Minimum 5,000 |
| Database response | ≤ 1 second |
| Dashboard generation | ≤ 5 seconds |
| File upload (100 MB) | ≤ 30 seconds |

### 8.5 Scalability Targets
- ~500 active learners initially
- ~5,000 registered users initially *(source doc states "5,00" — confirm intended figure before finalizing capacity planning)*
- 3,000 learners by Year Three
- Architecture must support future scale beyond 100,000 users
- Horizontal/vertical/auto scaling, elastic compute & storage, distributed caching, load balancing, multi-region (future), container orchestration

### 8.6 Availability, Reliability, Maintainability, Interoperability
- **Availability:** 99.9% annual uptime (excluding scheduled maintenance) — redundant infra, load balancing, automatic failover, DB replication, cloud redundancy, continuous monitoring.
- **Reliability:** fault tolerance, graceful degradation, automatic recovery, health monitoring, self-healing where applicable.
- **Maintainability:** modular upgrades, code reuse, configuration management, version control, automated deployment.
- **Interoperability standards:** REST, GraphQL (where applicable), JSON, XML, SCORM 1.2, SCORM 2004, xAPI (Tin Can), LTI, OAuth2, SAML.
- **Browser support:** latest Chrome, Edge, Firefox, Safari, Opera.
- **Accessibility:** WCAG 2.2 AA, WAI-ARIA, keyboard navigation, screen readers, captioned video, color contrast, adjustable font sizes, accessible forms.

---

## 9. Cybersecurity Requirements

Security-by-Design + Zero Trust, integrated throughout the SDLC.

| Domain | Requirements |
|---|---|
| **IAM** | RBAC, ABAC, least privilege, MFA, password policies/expiration, session timeout, device management, identity federation |
| **Authentication** | SSO, OAuth2, OpenID Connect via Frappe Social Login Keys (Google, Microsoft, GitHub); SAML/Entra ID federation is a gap — no first-party SAML SP in Frappe core (see §8.7) |
| **Encryption** | TLS 1.3 (in transit) · AES-256 (at rest) · Argon2/bcrypt (password hashing) · KMS for key management |
| **API Security** | API Gateway, rate limiting, token validation, API auth/authorization, monitoring, logging |
| **Secure SDLC** | OWASP Top 10, secure coding standards, code reviews, SAST, DAST, dependency scanning, secret scanning, SCA |
| **Vulnerability Management** | Vulnerability assessments, penetration testing, security audits/code reviews, configuration reviews, patch management |
| **Logging & Monitoring** | Centralized logging, audit trails, security event monitoring, SIEM integration, user/admin/API/DB logs (tamper-resistant, retained per policy) |
| **Incident Response** | IR plan, escalation procedures, forensic readiness, recovery procedures, communication plan |

### 9.1 Data Protection & Privacy Compliance
- Kenya Data Protection Act, 2019
- GDPR (where applicable)
- ISO 27001 / ISO 27701

**Personal data management:** consent management, data minimization, purpose limitation, retention & deletion policies, right to access/rectification/erasure, data portability.

**Privacy controls:** Privacy by Design, Privacy Impact Assessment (PIA), consent records, cookie management, data classification, anonymization/pseudonymization.

---

## 10. Cloud Infrastructure Requirements

**a) Infrastructure components:** VPC, public/private subnets, NACLs, Security Groups, Elastic Load Balancers, Auto Scaling Groups, Bastion Host (or equivalent), CloudWatch, CloudTrail, Backup Services, DR environment, WAF, DDoS protection, Secrets Management.

**b) Database:** MariaDB (RDS for MariaDB, or self-managed Galera cluster for HA) — automated backup, read replicas, Multi-AZ, point-in-time recovery, encryption. *(Not Postgres/Aurora — MariaDB is Frappe's supported DB engine.)*

**c) Storage:** Amazon S3 — versioning, lifecycle policies, intelligent tiering, secure access controls.

---

## 11. DevSecOps Requirements

| Area | Preferred Tooling |
|---|---|
| Source Control | GitHub Enterprise, GitLab, or Azure DevOps |
| CI | Automated build, unit testing, security scanning, code quality analysis |
| CD | Dev → Test → UAT → Production, automated with rollback capability |
| IaC | Terraform or AWS CloudFormation |
| Containerization | Docker, Kubernetes, Amazon ECS/EKS |

---

## 12. Quality Assurance & Testing Strategy

**QA covers:** coding standards, documentation standards, design reviews, UI consistency, security compliance, performance benchmarks, functional compliance, accessibility compliance.

| Test Type | Focus |
|---|---|
| Unit Testing | ≥ 80% code coverage |
| Integration Testing | APIs, payment gateway, CRM, email, authentication, video conferencing, analytics |
| System Testing | All functional requirements |
| Performance Testing | Stress, load, volume, spike, endurance testing |
| Security Testing | Penetration testing, vulnerability assessment, auth/authz testing, API testing, encryption testing |
| UAT | UAT scripts, acceptance criteria, defect log, sign-off forms — **no deployment without formal UAT sign-off** |

---

## 13. Business Continuity & Disaster Recovery

**BCP:** recovery strategies, critical business functions, communication procedures, emergency contacts.

**DRP targets:**

| Parameter | Target |
|---|---|
| Recovery Time Objective (RTO) | ≤ 4 hours |
| Recovery Point Objective (RPO) | ≤ 15 minutes |
| Backup Frequency | Daily incremental, weekly full |
| Backup Retention | Minimum 90 days |
| DR Testing | At least annually |

---

## 14. Mobile Learning Requirements

Native apps for **Android** and **iOS**, or a justified **Progressive Web App (PWA)** if it demonstrably meets offline, UX, and performance requirements.

> This repo's frontend (`frontend/`) is already a Vue 3 SPA — a PWA (service worker + manifest added to the existing Vite build) is the lower-lift path vs. standing up separate native codebases, and should be the default recommendation unless a native-only requirement (e.g. deep OS integration) surfaces.

**Mobile features:** offline learning & sync, push notifications, course/certificate downloads, video streaming, mobile assessments, mobile payments, AI chatbot, calendar sync, QR verification, camera integration (e.g. assignment uploads).

---

## 15. Sustainability & Future-Proofing

Platform must be designed to:
- Support modular expansion
- Accommodate AI evolution
- Integrate emerging technologies
- Support future blockchain credential verification
- Support future Learning Record Stores (LRS)
- Enable future interoperability with national/international digital credential frameworks
- Incorporate additional languages and regional payment systems over time

---

## 16. Open Items / Decisions Needed Before Build

These are ambiguities or unresolved questions carried over from the source ToR — resolve before locking architecture:

1. ~~**LMS build strategy**~~ **RESOLVED** — build extends this existing Frappe Learning app (Option B/C: custom/hybrid on Frappe), not Moodle Workplace. See §5 Workstream 3 and §8.7 for what that implies downstream.
2. **SCORM/xAPI/H5P support** — SCORM is partially implemented already (`lms.page_renderers.SCORMRenderer`, `SCORMChapter.vue`); xAPI and H5P are not present in this repo — still open, decide scope before content-authoring work begins.
3. **Registered user target** — source states "5,00" registered users initially; confirm whether this means 500 or 5,000 before sizing infrastructure.
4. **Workstream numbering** — the source ToR has two workstreams both labeled "Workstream 2" (Business Analysis, and Technology Assessment); renumber Technology Assessment as Workstream 3 for planning purposes (reflected as such in this document's cross-references).
5. **Bastion host vs. modern alternative** — source allows "equivalent secure administrative access" (e.g. AWS SSM Session Manager) instead of a traditional bastion.

---

## 17. Suggested Build Sequence (Mapping ToR → Sprints)

1. **Phase 0 — Inception:** Workstream 1 deliverables; resolve Section 16 open items.
2. **Phase 1 — Discovery:** Business analysis (Workstream 2), technology assessment & LMS decision (Workstream 3).
3. **Phase 2 — Architecture:** Enterprise architecture (Workstream 4); finalize AWS service map (§8.2); security architecture (§9).
4. **Phase 3 — Core Platform Build:** User management → course management → CMS → assessments → certification (§7.1–7.5).
5. **Phase 4 — AI Layer:** AI Tutor, Learning Assistant, Course Author, Analytics, Translation (§7.6).
6. **Phase 5 — Integrations:** CRM, payments, virtual classrooms, marketing tools (§8.1).
7. **Phase 6 — Mobile:** Android/iOS or PWA (§14).
8. **Phase 7 — Hardening & Testing:** Full test strategy (§12), pen testing, BCP/DRP validation (§13).
9. **Phase 8 — Go-Live & Handover:** UAT sign-off, training, documentation, warranty support, maintenance plan.

---

*Source: "Terms of Reference for Revamping/Developing CENTOP Academy," Centafrique Consulting, dated 26/07/2026. Converted and restructured for implementation planning; content reorganized by build workstream, section numbering normalized, and open items called out explicitly (Section 16) but no requirements were added or removed from the original scope.*
