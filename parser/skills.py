"""Skill extraction from a fixed dictionary (used for jobs and resumes).

Only skills whose name or alias literally appears in the text are returned,
so the system can never "invent" a skill someone does not have.
Each canonical skill lists the spellings people commonly use.
"""

import re

# canonical name -> lowercase aliases (the canonical name itself is always included)
SKILLS: dict[str, list[str]] = {
    # Avoid aliases that are ordinary English words ("rest", "node", "go").
    "Python": [], "Java": [], "JavaScript": ["js"], "TypeScript": [],
    "C++": ["cpp"], "C#": ["csharp"], "Kotlin": [], "Golang": ["go lang"],
    "SQL": [], "MySQL": [], "PostgreSQL": ["postgres"], "MongoDB": ["mongo"],
    "HTML": [], "CSS": [], "React": ["react.js", "reactjs"], "Node.js": ["nodejs"],
    "FastAPI": [], "Django": [], "Flask": [], "REST APIs": ["rest api", "restful"],
    "Linux": [], "Bash": ["shell scripting", "shell script"], "Git": [], "GitHub": [],
    "Docker": [], "Kubernetes": ["k8s"], "Terraform": [], "Ansible": [],
    "Jenkins": [], "GitHub Actions": [], "CI/CD": ["ci cd", "cicd"],
    "AWS": ["amazon web services"], "Azure": [], "GCP": ["google cloud"],
    "Prometheus": [], "Grafana": [], "Elasticsearch": ["elastic search"], "Redis": [],
    "Excel": ["ms excel"], "Power BI": ["powerbi"], "Tableau": [],
    "Pandas": [], "NumPy": [], "Machine Learning": ["ml"], "Deep Learning": [],
    "PyTorch": [], "TensorFlow": [], "Spark": ["pyspark", "apache spark"],
    "Android": [], "Figma": [], "Networking": ["computer networks"], "CCNA": [],
    "ROS": [], "RTOS": [], "Microcontrollers": ["microcontroller", "embedded c"],
}


def _pattern(alias: str) -> re.Pattern[str]:
    # Not preceded/followed by a letter, digit, + or #, so "java" does not match
    # inside "javascript" and "c" does not match inside "c++".
    return re.compile(rf"(?<![\w+#]){re.escape(alias)}(?![\w+#])", re.IGNORECASE)


_COMPILED: list[tuple[str, str, re.Pattern[str]]] = [
    (canonical, alias, _pattern(alias))
    for canonical, aliases in SKILLS.items()
    for alias in [canonical.lower(), *aliases]
]


def find_skills(text: str) -> dict[str, str]:
    """{canonical skill: the spelling actually used in the text}, in order of appearance."""
    hits: list[tuple[int, str, str]] = []
    seen: set[str] = set()
    for canonical, _alias, pattern in _COMPILED:
        if canonical in seen:
            continue
        match = pattern.search(text)
        if match:
            seen.add(canonical)
            hits.append((match.start(), canonical, match.group(0)))
    return {canonical: used for _, canonical, used in sorted(hits)}


def extract_skills(text: str) -> list[str]:
    """Canonical skill names found in the text."""
    return list(find_skills(text))


def reword_suggestions(text: str) -> list[str]:
    """Suggest the standard name for skills the text already mentions under another
    spelling. Never suggests a skill that is not already in the text."""
    tips = []
    for canonical, used in find_skills(text).items():
        if used.lower() != canonical.lower():
            tips.append(f"You wrote '{used}'. Many ATS filters search for '{canonical}', "
                        f"so consider writing '{canonical} ({used})'.")
    return tips


def match_score(candidate_skills: list[str], job_skills: list[str]) -> dict:
    """Share of the job's skills the candidate has, as a 0-100 score."""
    have = set(candidate_skills)
    matched = [s for s in job_skills if s in have]
    missing = [s for s in job_skills if s not in have]
    score = round(100 * len(matched) / len(job_skills)) if job_skills else 0
    return {"match_score": score, "matched_skills": matched, "missing_skills": missing}
