# Student Guide: Run Profile Lab in Your Own GitHub Account

This guide takes you from a personal copy of the repository to security test results and scanner reports. Start with Part A. Deploying a public application in Part B is optional unless your instructor requires it.

## What you will set up

| Part | What you need | What you get |
| --- | --- | --- |
| A: Tests and scans | GitHub account and web browser | Your own repository, baseline run, failing regression run, and reports |
| B: Public deployment (optional) | Part A plus a Render account | Your own hosted application and pipeline-controlled deployment |

For Part A, you do not need to install Python, Docker, or scanners on your computer. GitHub-hosted Ubuntu runners prepare the tools. Standard hosted runner execution is free for public repositories; private repositories have plan-dependent usage allowances. Check your account's billing and storage limits before using paid options.

## Part A: Run the pipeline without Render

### 1. Create your own copy

1. Sign in to GitHub.
2. Open [david-negrete/ITESO-SSDLC](https://github.com/david-negrete/ITESO-SSDLC).
3. Click **Fork** and choose your personal account as the owner.
4. Keep the repository name `ITESO-SSDLC` and create the fork. Copying only `main` is sufficient.
5. Confirm the page now shows **YOUR-USERNAME/ITESO-SSDLC**. Perform the remaining steps in your fork, not the instructor's repository.
6. Confirm these files exist: `.github/workflows/security.yml`, `app.py`, `tests/test_security.py`, and `requirements.txt`.

A fork copies repository files and history. It does not give you the instructor's deployment credentials or Render service. The README's instructor app link is a reference, not your own deployment.

### 2. Enable GitHub Actions

1. Open the **Actions** tab in your fork.
2. If GitHub displays a notice that workflows are disabled in a fork, enable them using the button on that page.
3. Find **Classroom security pipeline** in the workflow list.
4. If it is unavailable, check **Settings → Actions → General** and confirm Actions and the required actions are allowed. Account or organization policies can restrict availability.

Leave the repository variable `DEPLOY_ENABLED` unset, or set it to `false`. No deployment secrets are needed for Part A. The deployment job will be skipped.

### 3. Run the baseline scenario

1. Open **Actions → Classroom security pipeline**.
2. Click **Run workflow**.
3. Select branch **main** and scenario **baseline**.
4. Click the button that starts the workflow. Refresh the run list if it does not appear immediately.
5. Open the new run and wait for it to finish. Downloads and runner queues can affect duration.

Expected behavior for the unchanged starting code:

| Job | Expected outcome |
| --- | --- |
| Functional and security test cases | Pass; 20 cases in the starting version |
| SAST - Bandit | Pass if no findings are reported |
| SCA - pip-audit | Pass if no known dependency vulnerabilities are reported at execution time |
| Secret scanning - Gitleaks | Pass if no secrets are detected |
| DAST - ZAP passive baseline | Pass if no configured FAIL rules or scanner errors occur; warnings may remain |
| Deploy tested commit to Render | Skipped because deployment is not enabled |

Baseline means the code is tested without the deliberate teaching regression. It does not guarantee a green result forever: new dependency advisories, code changes, or tool/environment errors can cause failures. Investigate the actual evidence rather than changing a result just to make it green.

Tests, SAST, SCA, and secret scanning can run in parallel. DAST waits for tests. Each job has its own runner environment; the DAST job starts a separate temporary HTTP server. Nothing in Part A scans the instructor's public Render application.

### 4. Inspect logs and download reports

1. In the run graph, click **Functional and security test cases**.
2. Expand **Verify application behavior** to see case names and results.
3. Return to the run summary and scroll to **Artifacts**.
4. Click an artifact to download its ZIP, extract it, and open the report.

| Artifact | File | What to inspect |
| --- | --- | --- |
| `test-case-results` | `tests.json` | Total tests, failures, errors, and details for unsuccessful cases; passing case names are in the job logs |
| `sast-results` | `bandit.json` | Code findings, rule IDs, locations, severity, and confidence |
| `dependency-results` | `sca.json` | Dependency versions, vulnerability identifiers, and available fixes |
| `secret-scan-results` | `secrets.json` | Potential secrets in Git history; reported values are redacted |
| `dast-results` | `zap.html` and `zap.json` | Passive web findings; open `zap.html` in a browser |

A successful job can have an empty findings list. ZAP can also pass with warnings because the workflow uses `-I` and a rule configuration. An artifact may be missing if its generating step failed before creating the file. Reports are retained according to repository settings and can expire.

The ZAP baseline crawls public routes and analyzes responses. It is not an active attack scan and is not configured to authenticate. It does not verify Alice/Bob access restrictions. The targeted tests verify those expectations.

### 5. Run the authorization regression

1. Return to **Actions → Classroom security pipeline → Run workflow**.
2. Select **main** and **authorization-regression**.
3. Start the run and open **Functional and security test cases**.
4. Expand **Apply isolated teaching regression**. Read the displayed diff of `app.py`.
5. Expand **Verify application behavior**. Identify failed assertions and compare expected and actual results.
6. Download `test-case-results` if available and inspect the failure details.

The scenario adds `and profile_id == -1` to the ownership rejection condition. Existing profiles have positive IDs, so the rejection is bypassed. The unchanged tests still expect users to be denied access to other users' profiles. Receiving access instead makes those tests fail.

Expected authorization cases include `test_TC_AUTHZ_02_other_profile_is_denied` and `test_TC_AUTHZ_03_other_profile_cannot_be_modified`. Read your run's logs for the complete set.

**The tests job is expected to fail in this scenario.** DAST and deployment are skipped. Independent scanners can pass because they check their own unmodified checkouts. This demonstrates targeted test detection, not scanner detection of the injected defect.

The modification exists only in the temporary tests checkout. It is not committed to your fork, and a public deployment, if you have one, remains unchanged. Run `baseline` again to compare the normal behavior.

### 6. Connect the requirement to the test

Read [the test matrix](test-cases.csv) and [the test implementation](../tests/test_security.py).

- Requirement: ordinary users access only their own profile; administrators may access all profiles.
- ASVS reference: `v5.0.0-8.2.2` for access to specific data items.
- Related WSTG guidance: `WSTG-v42-ATHZ-04` for insecure direct object references.
- Test: authenticate as Alice, request Bob's profile, assert 403 and absence of protected data.

The test `setUp()` creates an isolated Flask application and random credentials. `login()` sends credentials and the test client retains session cookies. These are not Render passwords. The tests exercise the backend without opening a browser.

If assigned by your instructor, add a new case in a branch in your own fork and open a pull request targeting your fork's `main`, not the instructor's repository. Test methods must begin with `test_` to be discovered. Use the existing login/send helpers and meaningful assertions. Update the test matrix to match. After merging, pushes to `main` run the workflow automatically.

### 7. Suggested evidence to submit

Follow your instructor's assignment requirements. A useful evidence set is:

- Link to your fork.
- Links to your baseline and authorization-regression runs.
- One test ID, its preconditions, action, expected result, and observed result.
- Explanation of why an authorization assertion fails under regression.
- One scanner report observation, including scope or limitations.
- A new test and its result, if assigned.

## Part B: Deploy your own application on Render (optional)

### 8. Create a service from your fork

1. Sign in to Render and connect GitHub so Render can access your fork.
2. Choose **New → Blueprint** and select your fork and branch `main`.
3. Use the `render.yaml` in the repository root. If needed, change the service name in your fork to a unique name before creating the Blueprint.
4. Review the requested resources and pricing. The file requests the `free` plan; availability and account requirements can change. Do not select a paid alternative without reviewing its cost.
5. Create the Blueprint and wait for the initial deployment.
6. Open the new web service and record its own HTTPS URL. Do not use the instructor's URL.

The configuration installs `requirements.txt`, starts Gunicorn with one worker, checks `/health`, and generates `APP_SECRET_KEY`, `ALICE_PASSWORD`, `BOB_PASSWORD`, and `ADMIN_PASSWORD`. Retrieve account passwords from the service's **Environment** page to log into your app. Do not put these values in source files, screenshots, submissions, or issues.

Confirm **Auto-Deploy is disabled**. The Blueprint declares `autoDeployTrigger: off`; GitHub Actions should control subsequent deployments. The initial service creation still deploys once. Do not enable `APP_LOCAL_HTTP` on Render.

### 9. Configure GitHub deployment settings

1. In your Render service, open **Settings** and locate its **Deploy Hook**. Copy it privately.
2. In your GitHub fork, open **Settings → Environments** and create an environment named exactly `classroom`.
3. Inside that environment, add:

| Type | Name | Value |
| --- | --- | --- |
| Environment secret | `RENDER_DEPLOY_HOOK` | Your own Render service's deploy hook |
| Environment variable | `APP_URL` | Your own service's HTTPS URL |

4. Open **Settings → Secrets and variables → Actions → Variables**.
5. Create the repository variable `DEPLOY_ENABLED` with value `true`.

Names and scope matter: `RENDER_DEPLOY_HOOK` is a secret; `APP_URL` is a variable in `classroom`; `DEPLOY_ENABLED` is a repository variable. Never copy the instructor's hook or expose your hook in a commit. Forking does not supply these deployment settings.

### 10. Deploy and verify

1. Run **baseline** manually from **main** in your fork.
2. Wait for all checks to pass. The deploy job also waits for any environment approvals you configured.
3. Open **Deploy tested commit to Render → Deploy and verify revision**.
4. Confirm the deployment verification succeeds.
5. Open your own public URL and log in using the credentials from your Render service.
6. As Alice, view profile 1 (expect 200), then profile 2 (expect 403 without Bob's data).

`scripts/deploy.py` requests the commit under test, then verifies `/health` reports that revision and a changed instance ID. Render hosts the app after the runner finishes. Profiles and sessions are in memory and reset on restart, so you may need to log in again. An inactive free service may take time to wake up.

To disable later pipeline deployments while retaining checks, set `DEPLOY_ENABLED=false`. Remove unused hosting resources through your provider when the exercise is finished, following your instructor's guidance.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| Workflow is missing or disabled | Enable Actions in your fork; confirm `.github/workflows/security.yml` exists on `main` and account policies allow it |
| No Run workflow button | Open the specific workflow, use your own fork, confirm write access and the workflow exists on the default branch |
| Run stays queued | Runner availability or another execution in the same concurrency group; the workflow does not cancel the currently running execution |
| Baseline fails | Open the first failing step; distinguish application defects, new dependency advisories, and installation/network/tool errors |
| Regression fails | Expected if the authorization assertions fail; a setup error is not evidence of detecting the intended defect |
| Deploy is skipped | Expected in Part A, pull requests, and regression; otherwise check branch `main` and `DEPLOY_ENABLED=true` |
| Deploy cannot find configuration | Check environment name `classroom`, secret `RENDER_DEPLOY_HOOK`, and variable `APP_URL` |
| Deployment verification times out | Inspect Render deployment events/logs and `/health`; confirm the correct service URL, hook, and commit; do not post the hook |
| Public login fails after redeployment | Use your Render account passwords, not temporary test credentials; restart invalidates sessions |
| Tests fail with 403 in a new modification case | Ensure your request has a valid CSRF token so the case reaches the authorization rule you intend to test |

## References

- [GitHub workflow configuration](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
- [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions)
- [Render Blueprints](https://render.com/docs/infrastructure-as-code)
- [Render Blueprint fields](https://render.com/docs/blueprint-spec)
- [Render deploy hooks](https://render.com/docs/deploy-hooks)
- [ZAP baseline scan](https://www.zaproxy.org/docs/docker/baseline-scan/)
- [ASVS 5.0.0 authorization](https://github.com/OWASP/ASVS/blob/v5.0.0/5.0/en/0x17-V8-Authorization.md)
- [WSTG 4.2 IDOR testing](https://wstg.owasp.org/v4.2/4-Web_Application_Security_Testing/05-Authorization_Testing/04-Testing_for_Insecure_Direct_Object_References/)
