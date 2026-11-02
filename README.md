# Matillion EC2: Stop With Running-Jobs Check

AWS Lambda functions (Python 3.11, deployed as container images) that stop a Matillion EC2 server
(PROD, DEV or TEST) **only when it is safe**: before shutting down, the Lambda asks the Matillion API
for running or queued jobs, so a scheduled shutdown does not kill a job in progress.
A small companion Lambda starts the server again.

The main function is **EC2StopWithMatillionRunningJobsCheck**. The other two support it.

| Lambda | Handler file | Dockerfile | Purpose |
|---|---|---|---|
| **EC2StopWithMatillionRunningJobsCheck** (main) | `lambda_function_EC2StopWithMatillionRunningJobsCheck.py` | `Dockerfile_EC2StopWithMatillionRunningJobsCheck` | Checks Matillion for running jobs, then stops the EC2 instance if allowed |
| CallEC2StopWithMatillionRunningJobsCheck | `lambda_function_CallEC2StopWithMatillionRunningJobsCheck.py` | none yet | Dispatcher: turns an S3 flag file into a call to the Stop Lambda |
| EC2Start | `lambda_function_EC2Start.py` | `Dockerfile_EC2Start` | Starts the Matillion EC2 instance |

## How they fit together

```
EventBridge schedule ──────────────► EC2Start                          (start in the morning)

EventBridge schedule ──────────────► EC2StopWithMatillionRunningJobsCheck   (stop in the evening)
                                          ▲
S3: Matillion-<ENV>.flag ─► CallEC2Stop… ─┘   (on-demand trigger, see "Status" below)
```

## Common event payload

EC2Start and EC2StopWithMatillionRunningJobsCheck take the same JSON payload:

```json
{
  "e_system": "DEV",
  "e_region": "us-east-1",
  "e_force": "no",
  "e_email_to": "someone@example.com",
  "e_email_to_developers": "devs@example.com"
}
```

| Field | Meaning |
|---|---|
| `e_system` | `PROD`, `DEV` or `TEST`. Selects the Secrets Manager secret `/matillion/<e_system lowercased>` |
| `e_region` | AWS region, e.g. `us-east-1` |
| `e_force` | `yes` or `no`. Used by Stop only (ignored by Start) |
| `e_email_to` | Recipient of the result email |
| `e_email_to_developers` | Recipient of the "jobs are running" notice (Stop only) |

The secret `/matillion/<env>` must contain: `user`, `password`, `instanceid`, `url` (the Matillion REST API base URL, e.g. `https://<host>:8443/rest/v1`).

---

## 1. EC2Start

Starts the Matillion EC2 instance and waits until it is running.

1. Reads the secret and looks up the instance name.
2. Reads the instance state:
   - `running` / `pending`: nothing to do (`AlreadyRunning`).
   - `stopping`: waits for `stopped`, then starts it.
   - `stopped`: starts it.
   - `shutting-down` / `terminated`: reports an error.
3. Polls every 5 seconds, up to 30 times, until the state is `running`.
4. Emails the result to `e_email_to`.

Code: `Modules_start/Layer_ec2start.py`.

## 2. EC2StopWithMatillionRunningJobsCheck

Stops the Matillion EC2 instance only when that is safe.

1. Reads the secret and checks the EC2 state. If the instance is already stopped, it sends an
   "already stopped" email and exits without any API calls (this happens when an earlier attempt
   already stopped it).
2. Calls the Matillion REST API (`/group`, `/group/name/<g>/project`, `.../task/running`) and
   counts jobs in state `RUNNING` or `QUEUED`.
3. If the API cannot be reached (timeout, connection error), the instance is stopped without a jobs check,
   and a warning email is sent. This covers Matillion being unresponsive while EC2 is still up.
4. Otherwise decides using two S3 marker files in the bucket from `z_config.py`
   (`s3_bucket`, under the prefix `Matillion-<ENV>/`):

   | Marker file | Meaning |
   |---|---|
   | `Dry-Run.txt` | Exists: never stop the instance (for testing) |
   | `Shutdown_With_Running_Jobs-Allowed-ECops_Managed_File.txt` | Exists: ECops allows a forced shutdown even when jobs are running. Usually present for DEV/TEST and absent for PROD |

   | Running jobs | `e_force` | ECops file | Result |
   |---|---|---|---|
   | 0 | any | n/a | Stop (unless Dry-Run exists) |
   | >0 | `no` | n/a | Not stopped, developers are emailed the job list |
   | >0 | `yes` | exists | Stop (unless Dry-Run exists) |
   | >0 | `yes` | missing | Not stopped. The ECops file is re-created for the next run (see Known issues) |

5. Emails the result to `e_email_to`. When jobs are running, `e_email_to_developers` gets the job list.

Code: `Modules_stop/` (stop logic, EC2 status check) and `Modules_common/`.

## 3. CallEC2StopWithMatillionRunningJobsCheck

A small dispatcher. It exists so that uploading a file to S3 triggers a stop check, without anyone writing a payload.

1. Triggered by an S3 `ObjectCreated` event.
2. Maps the uploaded filename to an environment: `Matillion-PROD.flag`, `Matillion-DEV.flag` or `Matillion-TEST.flag`. Any other name is rejected.
3. Loads that environment's payload and target Lambda ARN from `z_config_CallEC2StopWithMatillionRunningJobsCheck.ini`.
4. Is meant to invoke the Stop Lambda with that payload (the payloads set `e_force` to `no`).

**Status: unfinished.** The `lambda_client.invoke(...)` call is commented out, so it only prints the
payload. There is also no Dockerfile for it, so the ini file is not packaged. The function needs both
fixed, and `lambda:InvokeFunction` permission on the three target Lambdas, before it can work.

---

## Configuration (environment variables)

Site-specific values are not in the code. Set them on each Lambda (function configuration), or locally with
`cp project.env.example project.env`, edit it, and run `. ./project.env` in the same shell before the `main-0-*` scripts.

| Variable | Required | Used by | Meaning |
|---|---|---|---|
| `MATILLION_S3_BUCKET` | yes | Stop | Bucket holding the Dry-Run and ECops marker files |
| `MATILLION_ADMIN_EMAIL` | yes | Stop | Receives the "already stopped" email |
| `MATILLION_EMAIL_SENDER` | yes | Start, Stop | SES "From" address (must be verified in SES) |
| `MATILLION_EMAIL_ALWAYS_CC` | no | Start, Stop | If set, copied on every email |

The Call Lambda's per-environment payloads live in `z_config_CallEC2StopWithMatillionRunningJobsCheck.ini`
(git-ignored). Copy `…ini.example` and fill in real values.

## Project layout

```
lambda_function_*.py          Lambda handlers (one per Lambda)
main-0-*.py                   Local runners: pick an event JSON and call the handler
event-*.json                  Sample events (Mat-DEV, Mat-TEST, Mat-PROD--Fake_PROD, Mat-PROD--Real_PROD, Call…)
z_config.py                   S3 bucket / marker-file names
z_config_Call…ini             Per-environment payloads for the Call Lambda
Modules_common/               Shared: Secrets Manager, S3, email, EC2 name lookup, message helpers
Modules_start/                Start logic
Modules_stop/                 Stop logic and EC2 status check
Dockerfile_*                  Container image builds (handler is copied in as lambda_function.py)
__*.txt                       Working notes: deploy steps, test procedures, permissions, TODOs
```

## Running locally

Needs AWS credentials with access to Secrets Manager, EC2, S3 and email, and network access to Matillion.

```
python main-0-EC2Start.py                                  # choose a DEV/TEST/PROD event file
python main-0-EC2StopWithMatillionRunningJobsCheck.py
python main-0-CallEC2StopWithMatillionRunningJobsCheck.py
```

**Testing without touching Matillion servers:** use `event-Mat-TEST.json`. The TEST secret points the
jobs check at Matillion-DEV but the start/stop at a throwaway Amazon Linux instance.
To test the "API unreachable" path, temporarily break the `url` in the `/matillion/test` secret (and restore it afterwards).
See `__NOTES_Stop_with_Runnin_jobs_check-2.txt`.

## Deploying a new version

See `__DEPLOY_NEW_VERSION.txt`. In short: update the code, test locally, rebuild the Docker image,
push it to ECR, update the Lambda, publish a new version, and repoint the alias to it.

## Known issues

- Call Lambda does not invoke the Stop Lambda and has no Dockerfile (see above).
- `Modules_start/Layer_ec2start.py` references `botocore.exceptions` without importing it, and can hit an unset
  variable in the `IncorrectInstanceState` branch. It also calls `exit()` on errors.
- The Stop Lambda re-creates the ECops "shutdown allowed" file when a forced stop is refused. This undoes ECops deleting
  it to protect PROD, so confirm this is intended.
- Matillion API calls use `verify=False` (TLS verification disabled) and have no timeout on the project/job calls.
- Stop Lambda returns nothing on its normal path, and has no validation of the incoming event.
- No automated tests.
