# PlacementHub – 5-minute demo script

Prepare **before** the interview (not during the 5 minutes):
- Stack running locally (`docker compose up -d`) or on EC2 (`terraform apply`).
- Seed data loaded (`python -m scripts.seed`).
- Browser tabs open: web UI, `/docs`, GitHub Actions page, Jenkins (optional).
- Telegram open with the bot and the forum group.
- A terminal in the repo folder; a sample resume `.txt` or `.pdf` ready.

---

### 0:00 – 0:30  The problem (talk)
"Placement messages arrive in Telegram groups, duplicated and unsearchable.
PlacementHub turns them into structured, searchable jobs." Show the
architecture diagram in the README.

### 0:30 – 1:30  Search (web UI)
1. Open the web UI. Point out the green health dot.
2. Type **`data anlyst`** (with the typo) → analyst jobs appear: fuzzy search.
3. Select **Internship**, type **Bengaluru** in Location → filters.
4. Tick **Closing in 3 days**, sort by **Deadline** → red/amber cards.
5. Search the same thing twice → "served from cache" badge (Redis, 60 s TTL).

### 1:30 – 2:30  Telegram bot
1. In the bot chat: `/deadlines` → cards with 🔴/🟠 badges.
2. `/filter role=devops location=bengaluru`.
3. Paste a new placement message into the source group → a structured card
   appears in the right forum topic. Paste it **again** → nothing is reposted:
   duplicate caught by Redis `SET NX` + the Elasticsearch id.

### 2:30 – 3:15  Resilience
```bash
docker compose stop redis
curl http://localhost/api/health          # "status": "degraded"
```
Search in the UI still works (no cache badge). Then `docker compose start redis`.
"Redis is a helper, Elasticsearch is the source of truth."

### 3:15 – 4:15  DevOps pipeline
1. GitHub → **Actions**: show a CI run (lint, tests, accuracy gate, Docker
   builds, Terraform validate) and the CD run that followed it on `main`.
2. Open `infra/terraform/` and show `ec2.tf` and `network.tf`: "only ports 80
   and 22, IMDSv2, the token comes from SSM, $5 budget".
3. Optional: Jenkins → `placementhub-nightly` → stages and the accuracy report.

### 4:15 – 5:00  Resume Match + wrap-up
1. Upload a resume in the **Resume Match** panel → skill chips, match scores
   and missing skills on the cards.
2. Close: "Everything is code: Terraform for AWS, Compose for the services,
   YAML for CI/CD, a Jenkinsfile for nightly jobs. After a demo I run
   `terraform destroy` so it costs nothing."

---

### If something breaks during the demo
- UI shows "Search is unavailable": `docker compose ps`, then
  `docker compose logs --tail 30 api` (talk through the JSON logs).
- Bot silent: `docker compose logs --tail 30 bot` (token missing or privacy
  mode still on).
- No results: re-run `python -m scripts.seed`.
