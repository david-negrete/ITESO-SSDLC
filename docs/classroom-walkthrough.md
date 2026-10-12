# Classroom walkthrough, 15 minutes

## 0–3 minutes: policy and application behavior

Sign in as Alice. Open Profile 1: expect a 200 response. Try Profile 2: expect a 403 response. Ask students to predict the outcome before making the second request. The policy is explicit: users can access only their own profile; the instructor has the administrator role.

## 3–6 minutes: from ASVS to a test case

Open `docs/test-cases.csv` and use TC-AUTHZ-02. Explain its relationship to ASVS v5.0.0-8.2.2 and WSTG-v42-ATHZ-04. The requirement establishes the authorization expectation. WSTG provides techniques for investigating object references. The application-specific case identifies the user, resource, action, and expected result.

Open the corresponding test in `tests/test_security.py`. It asserts a 403 response and verifies that protected profile fields are absent. An error message on screen alone is insufficient evidence.

## 6–10 minutes: a change fails verification

Run `authorization-regression` in Actions. Open the authorization diff and test job. Show TC_AUTHZ_02 and TC_AUTHZ_03 failing. Download `test-case-results` to inspect the evidence outside the log. The vulnerable code exists only in that execution's temporary runner.

Prepare this run before class as a backup while a live execution finishes. Use evidence from real runs.

## 10–13 minutes: security scanning

Open a successful `baseline` run. Compare Bandit, pip-audit, Gitleaks, and ZAP. Explain the input each tool receives and show an actual report artifact. Bandit does not know which user is allowed to read each profile. An application-specific authorization test can reveal a failure that a generic scanner misses.

The ZAP baseline is passive and unauthenticated. Review warnings even when they do not block the job. Distinguish a vulnerability finding, a warning, and a scanner execution error.

## 13–15 minutes: deployment

Open the Deploy job. Show its dependencies on the preceding checks and how it verifies the running revision against the tested commit, including a change of instance. Open the app and repeat the allowed and denied profile requests.

If deployment is not configured, the job is skipped. Explain that state accurately.

## Before class

- Verify the account credentials and open the app before the session.
- Keep a completed baseline run and authorization regression available.
- Check whether a new dependency advisory causes SCA to fail. Update the affected dependency and repeat verification if necessary.
- Keep the deploy hook, session signing key, and administrator password off the shared screen.
- Reserve SecureEnough for the assessed activity. This demonstration uses Profile Lab.
