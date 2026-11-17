# Jenkins nightly pipeline

GitHub Actions runs on every push. Jenkins runs **scheduled maintenance** every
night: it checks the parser still meets its accuracy target, rebuilds the
search index with the latest parser, and backs the data up.

## Run it locally

```powershell
# 1. Main stack first (Jenkins joins its network to reach Elasticsearch)
docker compose up -d --build
.\.venv\Scripts\python.exe -m scripts.seed

# 2. Jenkins
cd jenkins
Copy-Item .env.example .env        # set JENKINS_ADMIN_PASSWORD
docker compose up -d --build
```

Open <http://localhost:8081>, log in as `admin`, open **placementhub-nightly**
and click **Build with Parameters** → **Build**. Expected result: three green
stages, a JUnit test report, and `reports/parser-accuracy.txt` plus a
`jobs-*.jsonl.gz` backup under *Build Artifacts*. The Elasticsearch alias
`jobs` now points to `jobs_v2` (`curl localhost:9200/_cat/aliases`).

### Optional: real S3 upload from Jenkins
1. Create an IAM user `jenkins-backup` with only `s3:PutObject` on
   `arn:aws:s3:::<bucket>/backups/*`, and an access key.
2. Jenkins → *Manage Jenkins* → *Credentials* → add **Username with password**,
   ID `aws-backup`, username = access key ID, password = secret key.
3. Build with `S3_BUCKET=<bucket>`.

## How it is built

| Piece | What it does |
|---|---|
| `jenkins/Dockerfile` | Jenkins LTS + Python + plugins. No Docker socket is mounted (that would give Jenkins root access to the host). |
| `jenkins/casc.yaml` | **Configuration as Code**: admin user, security and the pipeline job are defined in YAML, so Jenkins can be rebuilt identically at any time. |
| `jenkins/Jenkinsfile` | **Pipeline as code**: the stages live in Git and are reviewed like any other code. |
| `scripts/reindex.py` | Builds `jobs_vN+1`, re-parses every message, verifies counts, then switches the alias atomically. |
| `scripts/backup_jobs.py` | Scroll-exports every job to gzipped JSON lines; uploads to S3 if a bucket is given. |

## Jenkins vs GitHub Actions

| | GitHub Actions | Jenkins |
|---|---|---|
| Where it runs | GitHub's hosted runners (or self-hosted) | Your own server/container |
| Setup | A YAML file in `.github/workflows` | Install, plugins, credentials, upkeep |
| Best at | Per-commit CI/CD tightly tied to GitHub | Long-running, scheduled or on-premise jobs; private networks; any Git host |
| Cost | Free for public repos, minutes for private | Free software, but you pay for and maintain the server |
| Access to private systems | Needs network access from GitHub | Lives inside your network (here: reaches Elasticsearch directly) |
| In this project | CI on every push, CD to EC2 | Nightly accuracy check, re-index, backup |

Many companies use both: GitHub Actions (or GitLab CI) for fast feedback on
every commit, Jenkins for heavier or internal jobs that existed before
hosted CI and need access to internal systems.
