# Retrospective Test Plan

## 1. Purpose

This document records the retrospective test plan for the Musician Evaluation System,
including the test strategy, execution evidence, scenarios, cases, and results.

## 2. Test Items

- Backend API and service layer
- Frontend authentication pages
- Audio upload and storage flow
- Assignment and evaluation workflow
- Audio similarity scoring
- Health and initialization flows

## 3. Scope

### In scope

- Unit testing
- Integration testing
- End user acceptance testing

### Out of scope

- Manual exploratory test logs
- Performance/load testing
- Penetration testing
- Unimplemented regression/security placeholders

## 4. Objectives

| Objective | Description |
|---|---|
| O1 | Verify authentication, refresh token, and RBAC behavior |
| O2 | Verify performance upload and storage resilience |
| O3 | Verify assignment, reference track, and evaluation workflows |
| O4 | Verify audio similarity scoring outputs |
| O5 | Verify frontend login/register usability |
| O6 | Verify health and database initialization behavior |

## 5. Test Strategy

| Level | Strategy | Typical Evidence |
|---|---|---|
| Unit | Isolated function/service/schema validation | Pytest function results |
| Integration | Multi-component workflow coverage | API workflow results |
| Acceptance | Browser-level user journey smoke checks | Playwright results |

## 6. Test Environment

| Area | Tooling / Configuration |
|---|---|
| Backend runtime | Python 3.12 |
| Backend test framework | Pytest + FastAPI TestClient |
| Backend test database | SQLite local file for automated execution |
| Frontend runtime | Vite + React + TypeScript |
| Acceptance framework | Playwright + Chromium |
| Production reference | Render-hosted backend with S3-backed audio uploads |

Note:

- PostgreSQL is the production database.
- SQLite was used only for local automated testing because the local PostgreSQL instance
  was not available for the run.

## 7. Entry and Exit Criteria

| Type | Criteria |
|---|---|
| Entry | Test environment available, dependencies installed, backend and frontend test suites discoverable |
| Exit | All automated cases executed, zero failures, results recorded, evidence linked |

## 8. Test Data

| Data Type | Use |
|---|---|
| Test users | Admin, musician, evaluator |
| Audio fixtures | WAV sine-wave fixtures and MP3 alias samples |
| Upload storage | Local disk fallback and live S3-backed production verification |
| Assignment data | Reference track + assignment + performance chains |

## 9. Retrospective Execution Summary

| Level | Cases | Passed | Failed | Result |
|---|---:|---:|---:|---|
| Unit | 43 | 43 | 0 | Pass |
| Integration | 12 | 12 | 0 | Pass |
| Acceptance | 5 | 5 | 0 | Pass |
| Total | 60 | 60 | 0 | Pass |

Execution commands:

```bash
cd backend
pytest -q tests

cd frontend
npm run test:smoke
```

## 10. Scenario and Case Matrix

### 10.1 Unit Test Scenarios

| Scenario ID | Scenario | Test Case ID(s) | Result |
|---|---|---|---|
| U-SC-01 | Authentication and login validation | UT-AUTH-01 to UT-AUTH-06 | Pass |
| U-SC-02 | Password hashing and secret rotation | UT-AUTH-07 to UT-AUTH-09 | Pass |
| U-SC-03 | Role-based access control | UT-AUTH-10 to UT-AUTH-13 | Pass |
| U-SC-04 | User profile management | UT-AUTH-14 to UT-AUTH-22 | Pass |
| U-SC-05 | Refresh token lifecycle | UT-AUTH-23 to UT-AUTH-28 | Pass |
| U-SC-06 | Audio similarity scoring | UT-AUDIO-01 to UT-AUDIO-03 | Pass |
| U-SC-07 | Health and initialization | UT-HEALTH-01 to UT-DB-01 | Pass |
| U-SC-08 | Audio upload and storage rules | UT-UPLOAD-01 to UT-UPLOAD-09 | Pass |

### 10.2 Integration Test Scenarios

| Scenario ID | Scenario | Test Case ID(s) | Result |
|---|---|---|---|
| I-SC-01 | Reference track and assignment creation | INT-01 | Pass |
| I-SC-02 | Performance analysis against assignment | INT-02 | Pass |
| I-SC-03 | Authorization guardrail for analysis | INT-03 | Pass |
| I-SC-04 | Performance deletion and related cleanup | INT-04 | Pass |
| I-SC-05 | Assignment deletion and reference track cleanup | INT-05 to INT-06 | Pass |
| I-SC-06 | Admin user lifecycle management | INT-07 to INT-09 | Pass |
| I-SC-07 | Musician assignment submission flow | INT-10 to INT-11 | Pass |
| I-SC-08 | Admin submission rejection | INT-12 | Pass |

### 10.3 Acceptance Test Scenarios

| Scenario ID | Scenario | Test Case ID(s) | Result |
|---|---|---|---|
| A-SC-01 | Login page rendering | AC-01 | Pass |
| A-SC-02 | Register page rendering | AC-02 | Pass |
| A-SC-03 | Password reset request rendering | AC-03 | Pass |
| A-SC-04 | Password reset form rendering | AC-04 | Pass |
| A-SC-05 | Protected dashboard redirect for unauthenticated users | AC-05 | Pass |

### 10.4 Functional Test Scenarios

| Scenario ID | Scenario | Test Case ID(s) | Result |
|---|---|---|---|
| F-SC-01 | Authentication lifecycle | UT-AUTH-01 to UT-AUTH-06, UT-AUTH-23 to UT-AUTH-28 | Pass |
| F-SC-02 | User profile management lifecycle | UT-AUTH-14 to UT-AUTH-22 | Pass |
| F-SC-03 | Audio upload lifecycle | UT-UPLOAD-01 to UT-UPLOAD-09 | Pass |
| F-SC-04 | Assignment and evaluation workflow | INT-01 to INT-12 | Pass |
| F-SC-05 | Recovery page navigation and usability | AC-03 to AC-05 | Pass |

## 11. Detailed Test Case Tables

### 11.1 Unit Test Cases - Authentication and RBAC

| Case ID | Test Case | Expected Result | Actual Result | Status | Evidence |
|---|---|---|---|---|---|
| UT-AUTH-01 | Register a valid user | 201 Created | 201 Created | Pass | [backend/tests/unit/test_auth.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_auth.py) |
| UT-AUTH-02 | Reject duplicate registration | 400 Bad Request | 400 Bad Request | Pass | [backend/tests/unit/test_auth.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_auth.py) |
| UT-AUTH-03 | Reject invalid email | 422 Validation Error | 422 Validation Error | Pass | [backend/tests/unit/test_auth.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_auth.py) |
| UT-AUTH-04 | Login with correct credentials | 200 OK with tokens | 200 OK with tokens | Pass | [backend/tests/unit/test_auth.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_auth.py) |
| UT-AUTH-05 | Reject invalid password | 401 Unauthorized | 401 Unauthorized | Pass | [backend/tests/unit/test_auth.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_auth.py) |
| UT-AUTH-06 | Reject nonexistent user login | 401 Unauthorized | 401 Unauthorized | Pass | [backend/tests/unit/test_auth.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_auth.py) |
| UT-AUTH-07 | Hash password safely | Hash differs from plain text | Pass | Pass | [backend/tests/unit/test_auth.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_auth.py) |
| UT-AUTH-08 | Reject wrong password verification | Verification fails | Verification failed as expected | Pass | [backend/tests/unit/test_auth.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_auth.py) |
| UT-AUTH-09 | Support secret rotation decoding | Old token still validates | Pass | Pass | [backend/tests/unit/test_auth.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_auth.py) |
| UT-AUTH-10 | Allow admin access | 200 OK | 200 OK | Pass | [backend/tests/unit/test_auth.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_auth.py) |
| UT-AUTH-11 | Deny musician admin access | 403 Forbidden | 403 Forbidden | Pass | [backend/tests/unit/test_auth.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_auth.py) |
| UT-AUTH-12 | Reject missing token | 403 Forbidden | 403 Forbidden | Pass | [backend/tests/unit/test_auth.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_auth.py) |
| UT-AUTH-13 | Reject invalid token | 403 Forbidden | 403 Forbidden | Pass | [backend/tests/unit/test_auth.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_auth.py) |
| UT-AUTH-14 | Get current user | 200 OK | 200 OK | Pass | [backend/tests/unit/test_auth.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_auth.py) |
| UT-AUTH-15 | Register with profile fields | Profile fields stored | Stored | Pass | [backend/tests/unit/test_auth.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_auth.py) |
| UT-AUTH-16 | Update current user | 200 OK | 200 OK | Pass | [backend/tests/unit/test_auth.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_auth.py) |
| UT-AUTH-17 | Reject invalid profile email update | 422 Validation Error | 422 Validation Error | Pass | [backend/tests/unit/test_auth.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_auth.py) |
| UT-AUTH-18 | Change password | 200 OK | 200 OK | Pass | [backend/tests/unit/test_auth.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_auth.py) |
| UT-AUTH-19 | Reject wrong current password | 400 Bad Request | 400 Bad Request | Pass | [backend/tests/unit/test_auth.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_auth.py) |
| UT-AUTH-20 | Admin list users | 200 OK | 200 OK | Pass | [backend/tests/unit/test_auth.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_auth.py) |
| UT-AUTH-21 | Admin get user | 200 OK | 200 OK | Pass | [backend/tests/unit/test_auth.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_auth.py) |
| UT-AUTH-22 | Admin update user | 200 OK | 200 OK | Pass | [backend/tests/unit/test_auth.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_auth.py) |
| UT-AUTH-23 | Login returns refresh token | Refresh token present | Present | Pass | [backend/tests/unit/test_auth.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_auth.py) |
| UT-AUTH-24 | Refresh token success | New access token issued | Issued | Pass | [backend/tests/unit/test_auth.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_auth.py) |
| UT-AUTH-25 | Reject invalid refresh token | 401 Unauthorized | 401 Unauthorized | Pass | [backend/tests/unit/test_auth.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_auth.py) |
| UT-AUTH-26 | Use new access token | Protected route accessible | Accessible | Pass | [backend/tests/unit/test_auth.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_auth.py) |
| UT-AUTH-27 | Reject inactive-user refresh | 403 Forbidden | 403 Forbidden | Pass | [backend/tests/unit/test_auth.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_auth.py) |
| UT-AUTH-28 | Reject expired refresh token | 401/403 as expected | Rejected | Pass | [backend/tests/unit/test_auth.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_auth.py) |

### 11.2 Unit Test Cases - Audio Similarity, Health, DB, Upload

| Case ID | Test Case | Expected Result | Actual Result | Status | Evidence |
|---|---|---|---|---|---|
| UT-AUDIO-01 | Matching audio scores higher | Higher score | Higher score | Pass | [backend/tests/unit/test_audio_similarity.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_audio_similarity.py) |
| UT-AUDIO-02 | Different audio scores lower | Lower score | Lower score | Pass | [backend/tests/unit/test_audio_similarity.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_audio_similarity.py) |
| UT-AUDIO-03 | Explainable breakdown exists | Breakdown returned | Returned | Pass | [backend/tests/unit/test_audio_similarity.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_audio_similarity.py) |
| UT-HEALTH-01 | Health endpoint responds | 200 OK | 200 OK | Pass | [backend/tests/unit/test_health.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_health.py) |
| UT-HEALTH-02 | Root endpoint responds | 200 OK | 200 OK | Pass | [backend/tests/unit/test_health.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_health.py) |
| UT-DB-01 | Init DB imports reference models | No import failure | No import failure | Pass | [backend/tests/unit/test_init_db.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_init_db.py) |
| UT-UPLOAD-01 | Create performance from upload | 201 Created | 201 Created | Pass | [backend/tests/unit/test_performance_upload.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_performance_upload.py) |
| UT-UPLOAD-02 | Reject invalid content type | 400 Bad Request | 400 Bad Request | Pass | [backend/tests/unit/test_performance_upload.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_performance_upload.py) |
| UT-UPLOAD-03 | Accept MP3 content type alias | 201 Created | 201 Created | Pass | [backend/tests/unit/test_performance_upload.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_performance_upload.py) |
| UT-UPLOAD-04 | Local storage fallback writes file | File written to disk | File written | Pass | [backend/tests/unit/test_performance_upload.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_performance_upload.py) |
| UT-UPLOAD-05 | S3 failure falls back to local | Local fallback used | Local fallback used | Pass | [backend/tests/unit/test_performance_upload.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_performance_upload.py) |
| UT-UPLOAD-06 | Missing S3 config without fallback fails | S3StorageError raised | Raised | Pass | [backend/tests/unit/test_performance_upload.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_performance_upload.py) |
| UT-UPLOAD-07 | Reject signature mismatch | 400 Bad Request | 400 Bad Request | Pass | [backend/tests/unit/test_performance_upload.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_performance_upload.py) |
| UT-UPLOAD-08 | Enforce maximum size | 413 Payload Too Large | 413 Payload Too Large | Pass | [backend/tests/unit/test_performance_upload.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_performance_upload.py) |
| UT-UPLOAD-09 | Local backend health reported | Healthy local backend | Healthy | Pass | [backend/tests/unit/test_performance_upload.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit/test_performance_upload.py) |

### 11.3 Integration Test Cases

| Case ID | Test Case | Expected Result | Actual Result | Status | Evidence |
|---|---|---|---|---|---|
| INT-01 | Create reference track and assignment | Assignment linked to reference | Linked | Pass | [backend/tests/integration/test_reference_assignment_flow.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/integration/test_reference_assignment_flow.py) |
| INT-02 | Analyze performance with assignment | Score stored | Score stored | Pass | [backend/tests/integration/test_reference_assignment_flow.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/integration/test_reference_assignment_flow.py) |
| INT-03 | Prevent evaluator from analyzing performance | 403 Forbidden | 403 Forbidden | Pass | [backend/tests/integration/test_reference_assignment_flow.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/integration/test_reference_assignment_flow.py) |
| INT-04 | Delete performance and related evaluation | Cleanup succeeds | Cleanup succeeds | Pass | [backend/tests/integration/test_reference_assignment_flow.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/integration/test_reference_assignment_flow.py) |
| INT-05 | Delete assignment unlinks performances | Records unlinked | Unlinked | Pass | [backend/tests/integration/test_reference_assignment_flow.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/integration/test_reference_assignment_flow.py) |
| INT-06 | Delete reference track only after assignment removal | Blocked until cleanup | Blocked until cleanup | Pass | [backend/tests/integration/test_reference_assignment_flow.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/integration/test_reference_assignment_flow.py) |
| INT-07 | Admin deletes user and cleans owned content | Owned content removed | Removed | Pass | [backend/tests/integration/test_reference_assignment_flow.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/integration/test_reference_assignment_flow.py) |
| INT-08 | Admin changes user role | Role updated | Updated | Pass | [backend/tests/integration/test_reference_assignment_flow.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/integration/test_reference_assignment_flow.py) |
| INT-09 | Admin cannot delete own account | 403 Forbidden | 403 Forbidden | Pass | [backend/tests/integration/test_reference_assignment_flow.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/integration/test_reference_assignment_flow.py) |
| INT-10 | Musician submits assignment and receives score | Score returned | Score returned | Pass | [backend/tests/integration/test_reference_assignment_flow.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/integration/test_reference_assignment_flow.py) |
| INT-11 | Submission survives missing reference audio | Flow still completes | Completed | Pass | [backend/tests/integration/test_reference_assignment_flow.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/integration/test_reference_assignment_flow.py) |
| INT-12 | Admin cannot submit performance | 403 Forbidden | 403 Forbidden | Pass | [backend/tests/integration/test_reference_assignment_flow.py](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/integration/test_reference_assignment_flow.py) |

### 11.4 Acceptance Test Cases

| Case ID | Test Case | Expected Result | Actual Result | Status | Evidence |
|---|---|---|---|---|---|
| AC-01 | Render login page | Login page renders | Login page renders | Pass | [frontend/tests/acceptance/smoke.spec.ts](C:/Users/Admin/Documents/Repos/Musician-Eval-System/frontend/tests/acceptance/smoke.spec.ts) |
| AC-02 | Render register page | Register page renders | Register page renders | Pass | [frontend/tests/acceptance/smoke.spec.ts](C:/Users/Admin/Documents/Repos/Musician-Eval-System/frontend/tests/acceptance/smoke.spec.ts) |
| AC-03 | Render password reset request page | Request page renders | Request page renders | Pass | [frontend/tests/acceptance/smoke.spec.ts](C:/Users/Admin/Documents/Repos/Musician-Eval-System/frontend/tests/acceptance/smoke.spec.ts) |
| AC-04 | Render password reset form | Reset form renders | Reset form renders | Pass | [frontend/tests/acceptance/smoke.spec.ts](C:/Users/Admin/Documents/Repos/Musician-Eval-System/frontend/tests/acceptance/smoke.spec.ts) |
| AC-05 | Redirect unauthenticated user from protected dashboard | Redirect to login | Redirect to login | Pass | [frontend/tests/acceptance/smoke.spec.ts](C:/Users/Admin/Documents/Repos/Musician-Eval-System/frontend/tests/acceptance/smoke.spec.ts) |

## 12. Evidence Pointers

| Evidence Type | Pointer |
|---|---|
| Unit test source | [backend/tests/unit/](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/unit) |
| Integration test source | [backend/tests/integration/](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/tests/integration) |
| Acceptance test source | [frontend/tests/acceptance/](C:/Users/Admin/Documents/Repos/Musician-Eval-System/frontend/tests/acceptance) |
| Retrospective test plan | [TESTING.md](C:/Users/Admin/Documents/Repos/Musician-Eval-System/TESTING.md) |
| System overview | [README.md](C:/Users/Admin/Documents/Repos/Musician-Eval-System/README.md) |
| Backend implementation guide | [RBAC_IMPLEMENTATION.md](C:/Users/Admin/Documents/Repos/Musician-Eval-System/backend/RBAC_IMPLEMENTATION.md) |
| Live backend health check | https://musician-eval-backend.onrender.com/api/v1/health |
| Live production upload verification | https://musician-eval-backend.onrender.com/api/v1/performances/upload-audio |
| Render deployment history | [Render Dashboard Deploys](https://dashboard.render.com/web/srv-d9k1imbm8hqs73be2v80/deploys) |

## 13. Risks and Limitations

| Item | Note |
|---|---|
| SQLite in test runs | Used only for local automated execution |
| Deprecation warnings | Present, but do not fail tests |
| Security/performance suites | Placeholder only, not yet automated |

## 14. Conclusion

The retrospective automated test run completed successfully with 60/60 passing:

- 43 unit cases
- 12 integration cases
- 5 acceptance cases

This plan reflects the current implemented test coverage and provides traceable evidence for
each test category.
