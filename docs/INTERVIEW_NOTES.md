# PlacementHub – Interview notes

## 30-second pitch

"In my college, placement openings arrive as hundreds of duplicated Telegram
messages, and students miss deadlines. I built PlacementHub: a Telegram bot and
web app that parses each message into a structured job, removes duplicates
with Redis, and makes everything searchable with Elasticsearch. It runs as five
Docker containers on an AWS EC2 instance that I provision with Terraform. GitHub
Actions tests every push and deploys to EC2 when tests pass, and a nightly
Jenkins pipeline checks parser accuracy, rebuilds the index and backs data up
to S3. I kept it inside the AWS Free plan with a budget alert."

## 2-minute walkthrough

1. **Ingest.** The bot reads placement groups with long polling and sends each
   message to the API (`POST /ingest`). The bot never talks to the database:
   one write path.
2. **Parse.** A rule-based parser extracts company, role, CTC or stipend,
   location, branches, CGPA, batch, deadline and the apply link. It sits behind
   a `Parser` interface so an LLM parser could be added without changing callers.
3. **Dedup.** I hash the normalized text with SHA-256. Redis `SET NX` catches
   duplicates fast; the same hash is the Elasticsearch document id written with
   `op_type=create`, so duplicates are blocked even if Redis is down.
4. **Search.** Elasticsearch gives fuzzy full-text search plus filters on
   category, role, location and deadline. Results are cached in Redis for 60
   seconds. Students use `/search`, `/deadlines`, `/filter` or the web UI.
5. **Infrastructure.** Terraform creates a security group with only ports 80
   and 22, one EC2 instance, a private S3 bucket, a least-privilege IAM role,
   the bot token in SSM Parameter Store and a $5 budget. A first-boot script
   installs Docker and starts the stack.
6. **Delivery.** CI runs lint, tests, an accuracy gate, Docker builds and
   Terraform validation on every push. CD runs only after CI passes on main:
   it pushes SHA-tagged images to GHCR, SSHes into EC2, pulls and restarts,
   then checks `/health`. Jenkins handles nightly maintenance.
7. **Operations.** JSON logs, `/health` with ok/degraded/down, Prometheus
   metrics, log rotation, and graceful degradation when Redis fails.

## Design decisions and trade-offs

| Decision | Why | Trade-off |
|---|---|---|
| One EC2 + Docker Compose | Cheapest way to run 5 services; easy to explain | No high availability; one server is a single point of failure |
| Self-hosted Elasticsearch, not managed OpenSearch | Managed search is not free | I handle heap limits, swap and `vm.max_map_count` myself |
| Redis as helper, ES as source of truth | Redis is memory-only and can lose data | Two places to reason about; worth it for speed and resilience |
| Rule-based parser first | Free, fast, deterministic, testable | Misses unusual formats; LLM parser is the planned upgrade |
| Long polling bot | No domain, TLS or inbound port | Slightly less efficient than webhooks at large scale |
| SSH-based CD with port 22 open (key-only) | GitHub runner IPs change constantly | Port 22 is exposed; production upgrade is SSM Run Command + OIDC |
| Search cache TTL 60 s | Huge read savings, simple | New jobs can take up to a minute to appear in cached searches |
| Fail-open rate limiter | A broken limiter should not block students | During a Redis outage there is no limit |
| Alias + versioned indexes | Zero-downtime mapping changes and re-parsing | Needs a re-index script and briefly double disk usage |

## 25 likely interview questions

**1. What is Terraform state, and why does it matter?**
State is Terraform's record of which real resources it created and how they map
to the code. `plan` compares code, state and real AWS to work out changes.
Without state, Terraform would try to create everything again. It can contain
secrets, so it is never committed; teams keep it in an encrypted, versioned S3
bucket with locking.

**2. What do `terraform plan` and `terraform apply` do?**
`plan` is a dry run: it shows what will be created, changed or destroyed, and
changes nothing. `apply` makes exactly those changes and updates the state.
Running `apply` again with no code changes does nothing, because Terraform is
declarative.

**3. Why Infrastructure as Code instead of clicking in the console?**
It is repeatable (same environment every time), reviewable in pull requests,
versioned in Git (you can see who changed what), and disposable: I create the
whole stack before a demo and delete it with one `destroy`, which also keeps
costs at zero.

**4. Redis vs Elasticsearch: what does each do here?**
Redis is an in-memory key-value store: tiny, fast, atomic operations, used for
dedup keys, a 60-second search cache and rate-limit counters. Elasticsearch is a
search engine: it analyzes text into an inverted index for relevance-ranked,
typo-tolerant search with filters. Elasticsearch holds the data; Redis only
speeds things up and can be lost safely.

**5. Why Elasticsearch instead of SQL `LIKE '%term%'`?**
`LIKE` scans every row, cannot use a normal index for a leading wildcard,
has no relevance ranking and no typo tolerance. Elasticsearch uses an inverted
index (word → documents), ranks results by relevance (BM25), handles stemming
("analysts" → "analyst") and fuzziness ("anlyst" → "analyst").

**6. How does your search cache work, and what is a TTL?**
The cache key is a hash of all search parameters. On a miss we query
Elasticsearch and store the JSON in Redis with a 60-second TTL (time to live),
after which Redis deletes it automatically. Short TTL means simple invalidation:
data is at most a minute stale, which is fine for job posts.

**7. How did you design duplicate detection?**
Normalize the text (lowercase, remove emojis and punctuation, collapse spaces),
hash it with SHA-256, then `SET dedup:<hash> NX EX 30d` in Redis. `NX` makes it
atomic: only the first writer succeeds. The same hash is the Elasticsearch
document id with `op_type=create`, a second safety net. If saving to
Elasticsearch fails, I delete the Redis key so a retry is not wrongly treated
as a duplicate.

**8. Why `SET NX` instead of `GET` then `SET`?**
`GET` then `SET` is two steps: two bot instances could both see "not found"
and both store the message (a race condition). `SET NX` checks and sets in one
atomic operation.

**9. How does the rate limiter work?**
Fixed window: key `rl:<user>:<minute>`, `INCR` it and set `EXPIRE` 60 s in one
pipeline. If the count is above 10 the command is refused. Keys expire on their
own. It fails open if Redis is down.

**10. Jenkins vs GitHub Actions: why both?**
GitHub Actions is hosted, lives next to the code and is ideal for CI/CD on every
push. Jenkins is self-hosted, very flexible, and runs inside your own network,
which suits scheduled or internal jobs; many companies still run it. I used
Actions for CI/CD and Jenkins for nightly maintenance, configured as code
(Jenkinsfile + JCasC).

**11. CI vs CD?**
Continuous Integration: every change is automatically built and tested so
problems are found early. Continuous Delivery/Deployment: changes that pass are
automatically packaged and released. Here CI runs on every push and PR; CD runs
only after CI succeeds on main.

**12. How do you handle secrets?**
Nothing secret is in Git: `.env`, `terraform.tfvars` and state are ignored. The
bot token is an SSM SecureString (KMS-encrypted) that the server reads at boot
using its IAM role, so no AWS keys live on the server. CI/CD secrets are GitHub
Secrets, and the registry token is sent over the SSH session, not as a
command-line argument. In code the token is a `SecretStr`, so it is masked in logs.

**13. Docker image vs container?**
An image is a read-only template (filesystem layers plus metadata), built from
a Dockerfile and stored in a registry. A container is a running instance of an
image with its own writable layer. One image can run as many containers.

**14. Why multi-stage builds, slim images and a non-root user?**
Multi-stage keeps build tools and caches out of the final image (smaller,
fewer vulnerabilities). Slim base images reduce size and attack surface.
Running as non-root means a compromised app does not get root inside the
container.

**15. What does a Docker healthcheck give you?**
Docker runs a command periodically and marks the container healthy or
unhealthy. Compose uses it to start the API only after Elasticsearch is
healthy, and `docker compose ps` shows problems at a glance. The bot has no HTTP
port, so it touches a heartbeat file that the healthcheck checks.

**16. What happens if Redis goes down?**
The app keeps working: searches skip the cache, dedup falls back to the
Elasticsearch id check, the rate limiter allows requests. `/health` reports
`degraded`, warnings are logged and `placementhub_redis_errors_total` increases.

**17. What happens if Elasticsearch goes down?**
Search and ingest return HTTP 503 with a clear message instead of crashing;
`/health` returns `down` (503) so Docker and CD detect it; the bot tells
students the service is temporarily unavailable. Data is safe on the Docker
volume and in the nightly S3 backup.

**18. What happens if the EC2 instance dies?**
Containers restart automatically after a reboot (`restart: unless-stopped`).
If the instance is lost, `terraform apply` recreates it and the first-boot
script reinstalls everything; data can be restored from the S3 backups. For
real high availability I would move to multiple instances behind a load
balancer or managed services, at extra cost.

**19. How would you scale to many groups and colleges?**
Separate ingestion from serving: put messages on a queue (SQS/Redis Streams)
and run several parser workers; run multiple stateless API containers behind a
load balancer; move Elasticsearch to a multi-node cluster or managed
OpenSearch; add a `college` field and per-college filters; consider
Kubernetes for orchestration.

**20. How do you control cost on AWS?**
Free-plan-only resources, default VPC (no NAT gateway), no load balancer or
Elastic IP, `cpu_credits = "standard"`, S3 lifecycle rules, a $5 budget
alert, tags on every resource, and `terraform destroy` after every demo.

**21. Why IMDSv2 and an IAM role instead of access keys on the server?**
The role gives the instance short-lived credentials that rotate
automatically, so no long-term keys can leak. IMDSv2 requires a session token,
which blocks a common attack where a vulnerable app is tricked into reading
instance credentials.

**22. What is an Elasticsearch alias and why use one?**
An alias is a pointer name (`jobs`) to a real index (`jobs_v1`). The app only
uses the alias. To change mappings or re-parse data, I build `jobs_v2`,
verify it, then move the alias in one atomic request: zero downtime and an
easy rollback.

**23. Why `filter` instead of `must` for filters?**
Clauses in `must` affect the relevance score. `filter` clauses are yes/no,
not scored, and Elasticsearch can cache them, so they are faster. Text search
goes in `must`; category, location and date ranges go in `filter`.

**24. How do you know the parser is good, and stays good?**
50 labelled sample messages with expected fields. An accuracy script scores
every field; CI fails below 95% and the nightly Jenkins job runs it too.
Honestly, the samples were written alongside the parser, so 100% there does
not mean 100% on real messages; I would keep adding real, anonymized messages
to the labelled set.

**25. How does Resume Match work without inventing skills?**
Skills come from a fixed dictionary and are only taken when they literally
appear in the resume. Each job also stores its skills and skill count.
Elasticsearch's `terms_set` query keeps jobs where the resume covers at least
70% of the job's skills (the minimum is computed per job). The API computes the
exact score and missing skills, and caches results in Redis. Suggestions only
reword a skill already in the resume, e.g. "k8s" → "Kubernetes (k8s)".

## Numbers worth remembering

- 5 containers: Elasticsearch, Redis, API, bot, web (nginx)
- 50 sample messages: 47 unique + 3 duplicates; 10 parsed fields
- 192 automated tests; coverage gate 85% (about 94% actual)
- Search cache TTL 60 s; dedup TTL 30 days; rate limit 10 commands/min
- Elasticsearch heap 512 MB (256 MB on t3.micro) + 2 GB swap
- $5 budget alert; only ports 80 and 22 open
