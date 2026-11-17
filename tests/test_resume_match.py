"""Resume Match: skill extraction, scoring, resume upload and the /jobs/match API."""

import pytest

from app.es import build_document, build_match_query
from app.resume import ResumeError, ResumeStore, S3ResumeUploader, extract_text
from parser.skills import extract_skills, match_score, reword_suggestions


def make_pdf(text: str) -> bytes:
    """Build a tiny valid one-page PDF containing `text` (no extra libraries)."""
    stream = f"BT /F1 12 Tf 10 100 Td ({text}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 400 144] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out, offsets = b"%PDF-1.4\n", []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % number + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    out += b"".join(b"%010d 00000 n \n" % offset for offset in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF" % (
        len(objects) + 1, xref)
    return out


# ---------------------------------------------------------------- skills
def test_extracts_only_skills_present_with_canonical_names():
    text = "Projects with python, k8s, Docker and CI/CD. Also JavaScript and C++."
    assert extract_skills(text) == ["Python", "Kubernetes", "Docker", "CI/CD",
                                    "JavaScript", "C++"]


def test_word_boundaries_prevent_false_matches():
    # "java" inside "javascript", "git" inside "github", "rest" as a normal word
    assert extract_skills("JavaScript developer on GitHub, the rest is history") == [
        "JavaScript", "GitHub"]


def test_suggestions_only_reword_existing_skills():
    tips = reword_suggestions("Deployed apps on k8s using python")
    assert len(tips) == 1 and "Kubernetes (k8s)" in tips[0]
    assert reword_suggestions("Python and Docker") == []      # nothing to reword, nothing added


def test_match_score():
    result = match_score(["Python", "Docker"], ["Python", "Docker", "Linux", "Git"])
    assert result == {"match_score": 50, "matched_skills": ["Python", "Docker"],
                      "missing_skills": ["Linux", "Git"]}
    assert match_score(["Python"], [])["match_score"] == 0


def test_job_documents_store_skills_count():
    doc = build_document({"skills": ["Linux", "Docker"]}, "raw", "seed", "2026-11-17T00:00:00")
    assert doc["skills_count"] == 2


def test_match_query_uses_terms_set_with_per_job_minimum():
    query = build_match_query(["Python", "Docker"], 0.7)
    terms_set = query["bool"]["filter"][1]["terms_set"]["skills"]
    assert terms_set["terms"] == ["Python", "Docker"]
    assert terms_set["minimum_should_match_script"]["params"] == {"ratio": 0.7}


# ---------------------------------------------------------------- resume files
def test_extract_text_from_pdf_and_txt():
    assert "Docker" in extract_text("cv.pdf", make_pdf("Python Docker Linux"))
    assert extract_text("cv.txt", b"Python and SQL") == "Python and SQL"


@pytest.mark.parametrize("name, content, message", [
    ("cv.pdf", b"", "empty"),
    ("cv.docx", b"PK\x03\x04 word file", "PDF or a .txt"),
    ("cv.pdf", b"%PDF-1.4 broken", "Could not read"),
    ("cv.txt", b"x" * (2 * 1024 * 1024 + 1), "2 MB"),
], ids=["empty", "docx", "broken-pdf", "too-big"])
def test_extract_text_rejects_bad_files(name, content, message):
    with pytest.raises(ResumeError, match=message):
        extract_text(name, content)


def test_resume_store_survives_redis_outage(redis_server):
    import fakeredis
    store = ResumeStore(fakeredis.FakeRedis(server=redis_server, decode_responses=True))
    resume_id = store.save(["Python"])
    assert store.skills(resume_id) == ["Python"]
    redis_server.connected = False
    assert store.skills(resume_id) is None
    assert len(store.save(["Python"])) == 32           # still returns an id


class FakeS3:
    def __init__(self, fail=False):
        self.calls, self.fail = [], fail

    def put_object(self, **kwargs):
        if self.fail:
            raise RuntimeError("S3 down")
        self.calls.append(kwargs)


def test_uploader_stores_privately_and_never_raises():
    s3 = FakeS3()
    assert S3ResumeUploader("bucket", "ap-south-1", client=s3).upload("abc", "cv.pdf",
                                                                       make_pdf("x"))
    assert s3.calls[0]["Key"] == "resumes/abc.pdf"
    assert s3.calls[0]["ServerSideEncryption"] == "AES256"
    assert S3ResumeUploader("", "ap-south-1").upload("abc", "cv.pdf", b"%PDF") is False
    assert S3ResumeUploader("b", "r", client=FakeS3(fail=True)).upload("a", "cv.txt", b"x") is False


# ---------------------------------------------------------------- API
DEVOPS_JOB = """Lotus Cloudworks – DevOps Intern
Stipend: ₹28,000 per month
Skills: Linux, Git, Docker, AWS"""
DATA_JOB = """Konark Payments – Data Analyst
CTC: 9 LPA
Rounds: SQL test with Python, Excel and Power BI"""


def upload(client, text: str):
    return client.post("/resume", files={"file": ("cv.txt", text.encode(), "text/plain")})


def test_resume_upload_returns_skills_and_suggestions(client):
    resp = upload(client, "Skills: Linux, Git, Docker, AWS, k8s")
    assert resp.status_code == 200
    body = resp.json()
    assert body["skills"] == ["Linux", "Git", "Docker", "AWS", "Kubernetes"]
    assert body["stored_in_s3"] is False and len(body["suggestions"]) == 1


def test_resume_upload_rejects_unsupported_files(client):
    resp = client.post("/resume", files={"file": ("cv.docx", b"PK..", "application/zip")})
    assert resp.status_code == 422


def test_match_returns_scored_jobs_above_threshold_and_caches(client):
    client.post("/ingest", json={"text": DEVOPS_JOB})
    client.post("/ingest", json={"text": DATA_JOB})
    resume_id = upload(client, "Linux, Git, Docker and Python").json()["resume_id"]

    first = client.get("/jobs/match", params={"resume_id": resume_id, "min_score": 70})
    body = first.json()
    assert first.status_code == 200 and body["cached"] is False
    assert [j["company"] for j in body["items"]] == ["Lotus Cloudworks"]
    assert body["items"][0]["match_score"] == 75
    assert body["items"][0]["missing_skills"] == ["AWS"]

    second = client.get("/jobs/match", params={"resume_id": resume_id, "min_score": 70})
    assert second.json()["cached"] is True


def test_match_with_skills_param_when_resume_unknown(client):
    client.post("/ingest", json={"text": DEVOPS_JOB})
    resp = client.get("/jobs/match", params={"skills": "linux, git, docker, aws",
                                             "min_score": 100})
    assert resp.json()["items"][0]["match_score"] == 100


def test_match_without_resume_or_skills_is_404(client):
    assert client.get("/jobs/match", params={"resume_id": "missing"}).status_code == 404
