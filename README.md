# Profile Lab

A classroom application for integrating security test cases and security scanning into a delivery pipeline. All accounts and profiles use synthetic data.

- App: https://profile-security-classroom.onrender.com
- Repository: https://github.com/david-negrete/ITESO-SSDLC
- Pipeline: https://github.com/david-negrete/ITESO-SSDLC/actions/workflows/security.yml

## Students: start here

Follow the [Student Setup Guide](docs/student-setup.md) to fork this repository into your own GitHub account, enable Actions, run the baseline and authorization-regression scenarios, and inspect the reports. No local Python or Docker installation is required for the GitHub-only exercise. Render deployment is optional and uses your own service and credentials.

The application and pipeline links above belong to the instructor's project. Use your fork for the exercise; it does not inherit the instructor's deployment credentials. Leave `DEPLOY_ENABLED` unset or `false` until you configure your own deployment.

## Run locally

Requires Python 3.12 and access to PyPI to install dependencies.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run_local.py
```

Open http://127.0.0.1:5000. The console displays temporary passwords for `alice`, `bob`, and `admin`. Each restart generates new local credentials. The local server listens only on loopback.

Users can read and update their own profile. Administrators can access every profile. Only `bio` can be edited; clients cannot change roles or IDs. Profiles, sessions, and login attempt limits are stored in memory and reset when the service restarts. The deployment therefore uses one worker. This application is intended for a small demonstration with synthetic data.

## Run tests and scans

```powershell
python scripts/run_tests.py
python -m pip install -r requirements-ci.txt
python -m bandit app.py wsgi.py -f json -o reports/bandit.json
python -m pip_audit -r requirements.txt -f json -o reports/sca.json
```

Test cases have visible IDs, such as `TC_AUTHZ_02_other_profile_is_denied`. The matrix in `docs/test-cases.csv` lists preconditions, actions, expected results, and references. The summary report is written to `reports/tests.json`.

## GitHub Actions pipeline

The repository is `david-negrete/ITESO-SSDLC`, with `main` as its default branch. Preserve the folder structure, including `.github/`. Repository write access and GitHub Actions are required to configure the pipeline.

The `Classroom security pipeline` workflow runs on pushes to `main`, pull requests, and manual executions:

1. **Functional and security test cases:** runs the automated cases.
2. **SAST - Bandit:** analyzes `app.py` and `wsgi.py`. Any reported finding fails the job.
3. **SCA - pip-audit:** checks runtime dependencies, including resolved transitive dependencies, for known vulnerabilities. Any reported vulnerability fails the job.
4. **Secret scanning - Gitleaks:** scans Git history. Reports redact detected secrets.
5. **DAST - ZAP:** starts a temporary application and performs a passive baseline scan of public routes. Missing CSP or X-Content-Type-Options headers are configured as FAIL. Other warnings remain in the report. Scanner errors also fail the job.
6. **Deploy:** runs only on `main`, after the preceding jobs pass and `DEPLOY_ENABLED=true` is configured.

Scan jobs save downloadable evidence as artifacts. SAST, SCA, and secret scanning run in parallel with the tests. DAST waits for the tests to pass. ZAP does not authenticate or test private profiles; authorization test cases verify that behavior. A successful scan does not establish full ASVS compliance.

CI tools are installed on the runners, rather than included in runtime dependencies. Runtime dependency versions are pinned. ZAP uses its `stable` image channel, and Actions use major-version tags. To freeze the classroom environment for long-term reproducibility, record and pin action SHAs and image digests after a successful run.

## Demonstrate isolated classroom failures

Open **Actions → Classroom security pipeline → Run workflow** on `main` and choose a scenario:

| Scenario | Temporary change | Expected test evidence |
| --- | --- | --- |
| `baseline` | None | All 20 starting cases pass, subject to actual results |
| `authorization-regression` | Removes effective ownership rejection | Other-profile access and modification tests fail |
| `validation-regression` | Removes the 200-character bio limit, preserving the text-type check | `test_TC_INPUT_01_bio_limit_and_type` fails for a 201-character string: actual 200, expected 400 |
| `csrf-test-setup-error` | Omits CSRF only in the owner-update test request; application unchanged | `test_TC_AUTHZ_04_owner_can_update` fails: actual 403, expected 200 |

The tests job changes only its own temporary checkout and shows the diff in **Apply isolated teaching scenario**. Read **Verify application behavior** for failed assertions and download `test-case-results`. The CSRF scenario demonstrates incorrect test preparation, rather than an application defect. Independent scanner jobs inspect their own unchanged checkouts. DAST and deployment are skipped when tests fail; deployment also explicitly allows only pushes or manual baseline runs on `main`. No failure scenario is deployed, even if its tests unexpectedly pass. The repository source and public app keep their normal controls. Run `baseline` to compare normal behavior (an eligible baseline on `main` can deploy).

This compares two code states in isolated runners. Use actual test and scanner results as classroom evidence.

Additional isolated scenarios cover logout revocation, session expiration, previous-session invalidation on login, protected-field validation, administrator access, and cache policy. Choose them in the same scenario menu. Each changes only the tests job's temporary application copy. The optional `exercise_id` labels a run, for example `Classroom exercise 01`, without putting the scenario name in its title. Manually dispatched runs use separate concurrency groups so exercise runs can queue without replacing each other; push runs retain concurrency grouping by branch. Failure scenarios remain excluded from deployment regardless of test outcomes.

## Deploy on Render

1. Import `render.yaml` as a Render Blueprint from the repository. Review the plan before creating the service. The file requests `free`, subject to availability on your account.
2. Render generates the three account passwords and session signing key. Retrieve them from the service's Environment page. Share only the synthetic account passwords needed for class.
3. Render performs the initial deployment when the service is created. Auto-deploy is disabled so GitHub Actions controls subsequent deployments.
4. Create the GitHub environment `classroom`. Add the secret `RENDER_DEPLOY_HOOK` with the Render deploy hook, and the variable `APP_URL` with the service's HTTPS URL. The hook is a secret; keep it out of source files, tickets, and chat messages.
5. Add the repository variable `DEPLOY_ENABLED=true` to enable pipeline deployments.
6. Run `baseline` from `main`. The job requests deployment of the tested commit, then polls `/health` until the revision matches and the running instance changes. This also verifies a restart when the same commit is redeployed.

Do not enable `APP_LOCAL_HTTP` on Render. The public service uses Secure cookies and HSTS. Restarts invalidate existing sessions. Open the app before class to allow the free instance to wake up if needed.

## References

- [ASVS 5.0.0](https://github.com/OWASP/ASVS/tree/v5.0.0/5.0/en)
- [WSTG 4.2](https://wstg.owasp.org/v4.2/)
- [GitHub: Python workflows](https://docs.github.com/en/actions/tutorials/build-and-test-code/python)
- [Bandit](https://bandit.readthedocs.io/en/latest/)
- [pip-audit](https://github.com/pypa/pip-audit)
- [Gitleaks](https://github.com/gitleaks/gitleaks)
- [ZAP baseline](https://www.zaproxy.org/docs/docker/baseline-scan/)
- [Render Blueprints](https://render.com/docs/blueprint-spec)
- [Render deploy hooks](https://render.com/docs/deploy-hooks)
