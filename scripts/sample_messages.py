"""~50 realistic sample placement messages in Indian campus style.

All companies, links and people are FICTIONAL (links use the reserved
.example domain). Each message has hand-written `expected` labels, used to
measure parser accuracy (pytest in Phase 2, nightly Jenkins job in Phase 8).

Deadlines are written as "{deadline}" and filled in relative to today
(`deadline_days`), so the "closing soon" demo always works.
The last 3 messages are re-forwarded duplicates (same text, different
emojis/case/spacing) to demonstrate duplicate detection.
"""

from datetime import date, timedelta
from typing import Any

MESSAGES: list[dict[str, Any]] = [
    # 1
    {
        "text": """🔔 *Placement Drive Alert* 🔔

Company: Nimbus Analytics
Role: Data Analyst
CTC: 7.5 LPA
Location: Bengaluru
Eligibility: B.Tech CSE / ISE / AIML / DS, 2027 batch, CGPA 7.0 and above, no active backlogs
Last date to apply: {deadline}
Register here: https://careers.nimbus-analytics.example/apply/da-2027

- Training & Placement Office""",
        "deadline_days": 2, "deadline_format": "%d %b %Y",
        "expected": {"category": "Full-time", "company": "Nimbus Analytics", "role": "Data Analyst",
                     "location": "Bengaluru", "ctc_lpa": 7.5, "cgpa_min": 7.0, "batch": [2027],
                     "branches": ["CSE", "ISE", "AIML", "DS"]},
    },
    # 2
    {
        "text": """Dear Students,

Kaveri Systems is hiring Associate Software Engineers from the 2027 passing-out batch.
Package: Rs 6,00,000 per annum
Job location: Hyderabad
Open to all branches with a minimum CGPA of 6.5.
Interested students must fill the form before {deadline}.
Form: https://forms.kaveri-systems.example/ase-2027

Regards,
Placement Cell""",
        "deadline_days": 5, "deadline_format": "%d/%m/%Y",
        "expected": {"category": "Full-time", "company": "Kaveri Systems",
                     "role": "Associate Software Engineer", "location": "Hyderabad", "ctc_lpa": 6.0,
                     "cgpa_min": 6.5, "batch": [2027], "branches": ["ALL"]},
    },
    # 3
    {
        "text": """📢 Internship Opportunity 📢

Tridentia Labs - SDE Intern (6 months)
Stipend: ₹40,000/month
Location: Bengaluru (on-site)
Who can apply: CSE & ISE students of 2027 batch with 8.0+ CGPA
Apply by {deadline}: https://tridentia-labs.example/jobs/sde-intern""",
        "deadline_days": 1, "deadline_format": "%d-%m-%Y",
        "expected": {"category": "Internship", "company": "Tridentia Labs", "role": "SDE Intern",
                     "location": "Bengaluru", "stipend_month": 40000, "cgpa_min": 8.0,
                     "batch": [2027], "branches": ["CSE", "ISE"]},
    },
    # 4
    {
        "text": """Zephyr Fintech | Backend Developer | Full Time
CTC: 12 LPA
Location: Pune
Branches: CSE, IT
Batch: 2027
CGPA cutoff: 7.5
Skills: Java or Go, SQL, REST APIs
Deadline: {deadline}
Link: https://zephyr-fintech.example/careers/backend-2027""",
        "deadline_days": 7, "deadline_format": "%d %B %Y",
        "expected": {"category": "Full-time", "company": "Zephyr Fintech",
                     "role": "Backend Developer", "location": "Pune", "ctc_lpa": 12.0,
                     "cgpa_min": 7.5, "batch": [2027], "branches": ["CSE", "IT"]},
    },
    # 5
    {
        "text": """🚀 CODE MONSOON 2026 – National Hackathon by Monsoon Mobility 🚀

Build solutions for smarter city transport. Teams of 2-4.
Prize pool: ₹2,00,000 + internship interviews for winners
Mode: Online
Open to all branches, 2027, 2028 and 2029 batches.
Registration closes on {deadline}
Register: https://monsoon-mobility.example/codemonsoon""",
        "deadline_days": 3, "deadline_format": "%d %b %Y",
        "expected": {"category": "Hackathon", "company": "Monsoon Mobility", "role": None,
                     "location": "Remote", "batch": [2027, 2028, 2029], "branches": ["ALL"]},
    },
    # 6
    {
        "text": """Orbitron Technologies is conducting an on-campus drive.

Position: DevOps Engineer Trainee
CTC: 5.5 LPA
Location: Chennai
Eligible branches: CSE / ISE / ECE
Batch: 2027 | Minimum CGPA: 6.0
Selection: Online test, technical interview, HR
Last date: {deadline}
Apply: https://orbitron-tech.example/drive/devops-trainee""",
        "deadline_days": 10, "deadline_format": "%d/%m/%Y",
        "expected": {"category": "Full-time", "company": "Orbitron Technologies",
                     "role": "DevOps Engineer Trainee", "location": "Chennai", "ctc_lpa": 5.5,
                     "cgpa_min": 6.0, "batch": [2027], "branches": ["CSE", "ISE", "ECE"]},
    },
    # 7
    {
        "text": """Saptarishi Software is looking for Frontend Developer Interns 💻

Duration: 3 months | Work from home
Stipend: Rs. 25000 per month
Eligibility: CSE, ISE, IT | 2028 batch | CGPA 7 and above
Tech: React, JavaScript, CSS
Apply before {deadline}
https://saptarishi-software.example/intern/frontend""",
        "deadline_days": 4, "deadline_format": "%d %b %Y",
        "expected": {"category": "Internship", "company": "Saptarishi Software",
                     "role": "Frontend Developer Intern", "location": "Remote",
                     "stipend_month": 25000, "cgpa_min": 7.0, "batch": [2028],
                     "branches": ["CSE", "ISE", "IT"]},
    },
    # 8
    {
        "text": """Bluepeak Data – Data Science Intern

Stipend: INR 30k/month
Location: Bengaluru
Eligibility: CSE / DS / AIML, 2027 batch, CGPA ≥ 7.5
Knowledge of Python, pandas and basic ML is a must.
Deadline: {deadline}
Apply: https://bluepeak-data.example/careers/ds-intern""",
        "deadline_days": 2, "deadline_format": "%d-%m-%Y",
        "expected": {"category": "Internship", "company": "Bluepeak Data",
                     "role": "Data Science Intern", "location": "Bengaluru", "stipend_month": 30000,
                     "cgpa_min": 7.5, "batch": [2027], "branches": ["CSE", "DS", "AIML"]},
    },
    # 9
    {
        "text": """Lotus Cloudworks hiring – Cloud Support Associate

CTC: 4.5 LPA
Location: Hyderabad
Open to all branches, 2027 batch
Min CGPA: 6.0
Good communication skills and basic Linux knowledge required.
Register by {deadline}: https://lotus-cloudworks.example/hiring/csa""",
        "deadline_days": 6, "deadline_format": "%d %B %Y",
        "expected": {"category": "Full-time", "company": "Lotus Cloudworks",
                     "role": "Cloud Support Associate", "location": "Hyderabad", "ctc_lpa": 4.5,
                     "cgpa_min": 6.0, "batch": [2027], "branches": ["ALL"]},
    },
    # 10
    {
        "text": """IndusGrid Energy – Graduate Engineer Trainee (GET)

Package: 6.5 LPA
Posting: Ahmedabad
Branches: EEE, Mechanical
Batch: 2027
CGPA: 6.5 and above, no backlogs
Last date to register: {deadline}
https://indusgrid-energy.example/get-2027""",
        "deadline_days": 9, "deadline_format": "%d/%m/%Y",
        "expected": {"category": "Full-time", "company": "IndusGrid Energy",
                     "role": "Graduate Engineer Trainee", "location": "Ahmedabad", "ctc_lpa": 6.5,
                     "cgpa_min": 6.5, "batch": [2027], "branches": ["EEE", "MECH"]},
    },
    # 11
    {
        "text": """Pre-Placement Talk by Kaveri Systems tomorrow at 10:30 AM in Seminar Hall 2.
Attendance is mandatory for all registered students.
Please carry your college ID card.""",
        "deadline_days": None,
        "expected": {"category": "Other", "company": "Kaveri Systems", "role": None},
    },
    # 12
    {
        "text": """Varuna Ledger is hiring Business Analysts 📊

CTC: 8 LPA
Location: Mumbai
Eligibility: All branches | 2027 batch | 7.0 CGPA and above
Rounds: Aptitude, Case study, Interview
Apply by {deadline}
https://varuna-ledger.example/ba-campus""",
        "deadline_days": 3, "deadline_format": "%d %b %Y",
        "expected": {"category": "Full-time", "company": "Varuna Ledger",
                     "role": "Business Analyst", "location": "Mumbai", "ctc_lpa": 8.0,
                     "cgpa_min": 7.0, "batch": [2027], "branches": ["ALL"]},
    },
    # 13
    {
        "text": """Pinnacle Semicon – VLSI Design Intern

Stipend: ₹35,000 per month
Location: Bengaluru
Eligibility: ECE / EEE, 2027 batch, CGPA 7.5+
Duration: 6 months (Jan to Jun)
Deadline: {deadline}
Apply: https://pinnacle-semicon.example/intern/vlsi""",
        "deadline_days": 8, "deadline_format": "%d %B %Y",
        "expected": {"category": "Internship", "company": "Pinnacle Semicon",
                     "role": "VLSI Design Intern", "location": "Bengaluru", "stipend_month": 35000,
                     "cgpa_min": 7.5, "batch": [2027], "branches": ["ECE", "EEE"]},
    },
    # 14
    {
        "text": """Sahyadri Infotech campus drive

Role: Software Engineer
CTC: 6-8 LPA (based on interview performance)
Location: Mysuru
Branches: CSE, ISE
Batch: 2027
Minimum CGPA: 6.5
Last date: {deadline}
Registration link: https://sahyadri-infotech.example/drive2027""",
        "deadline_days": 12, "deadline_format": "%d-%m-%Y",
        "expected": {"category": "Full-time", "company": "Sahyadri Infotech",
                     "role": "Software Engineer", "location": "Mysuru", "ctc_lpa": 8.0,
                     "cgpa_min": 6.5, "batch": [2027], "branches": ["CSE", "ISE"]},
    },
    # 15
    {
        "text": """Aravali Robotics – Robotics Engineer (Full-time)

CTC: 9 LPA
Location: Gurugram
Eligible: Mechanical, ECE, EEE | 2027 batch | CGPA 7.0+
Hands-on experience with ROS or embedded C preferred.
Apply before {deadline}: https://aravali-robotics.example/careers/re""",
        "deadline_days": 5, "deadline_format": "%d %b %Y",
        "expected": {"category": "Full-time", "company": "Aravali Robotics",
                     "role": "Robotics Engineer", "location": "Gurugram", "ctc_lpa": 9.0,
                     "cgpa_min": 7.0, "batch": [2027], "branches": ["MECH", "ECE", "EEE"]},
    },
    # 16
    {
        "text": """💡 Smart Campus Ideathon by Silverline Edu 💡

Pitch your idea to make campus life easier. Individual or team of 3.
Mode: Online
Open to all branches and all batches (2027, 2028, 2029).
Last date to submit your idea: {deadline}
Submit: https://silverline-edu.example/ideathon""",
        "deadline_days": 1, "deadline_format": "%d/%m/%Y",
        "expected": {"category": "Hackathon", "company": "Silverline Edu", "role": None,
                     "location": "Remote", "batch": [2027, 2028, 2029], "branches": ["ALL"]},
    },
    # 17
    {
        "text": """Coralbyte – Machine Learning Engineer Intern

Stipend: 45,000 INR per month
Location: Remote
Eligibility: CSE / AIML / DS, 2027 batch, CGPA 8.0 and above
Must know Python, PyTorch or TensorFlow.
Deadline: {deadline}
Apply: https://coralbyte.example/jobs/ml-intern""",
        "deadline_days": 6, "deadline_format": "%d %B %Y",
        "expected": {"category": "Internship", "company": "Coralbyte",
                     "role": "Machine Learning Engineer Intern", "location": "Remote",
                     "stipend_month": 45000, "cgpa_min": 8.0, "batch": [2027],
                     "branches": ["CSE", "AIML", "DS"]},
    },
    # 18
    {
        "text": """Quillstack is hiring Technical Writers ✍️

CTC: 5 LPA
Location: Pune
Open to all branches, 2027 batch
CGPA: 6.0 and above
Strong written English is a must.
Apply by {deadline}
https://quillstack.example/careers/tech-writer""",
        "deadline_days": 14, "deadline_format": "%d %b %Y",
        "expected": {"category": "Full-time", "company": "Quillstack", "role": "Technical Writer",
                     "location": "Pune", "ctc_lpa": 5.0, "cgpa_min": 6.0, "batch": [2027],
                     "branches": ["ALL"]},
    },
    # 19
    {
        "text": """Ganga Health Tech – Data Engineer

CTC: 10 LPA
Location: Noida
Eligibility: CSE, ISE, DS | 2027 batch | Min 7.0 CGPA
Skills: SQL, Python, Spark basics
Last date to apply: {deadline}
Apply here: https://ganga-healthtech.example/de-2027""",
        "deadline_days": 2, "deadline_format": "%d/%m/%Y",
        "expected": {"category": "Full-time", "company": "Ganga Health Tech",
                     "role": "Data Engineer", "location": "Noida", "ctc_lpa": 10.0,
                     "cgpa_min": 7.0, "batch": [2027], "branches": ["CSE", "ISE", "DS"]},
    },
    # 20
    {
        "text": """Deccan Logistics AI – Operations Analyst Intern

Stipend: Rs 20,000/month
Location: Hyderabad
Open to all branches, 2028 batch, CGPA 6.0 and above
Deadline: {deadline}
Apply: https://deccan-logistics.example/intern/ops""",
        "deadline_days": -2, "deadline_format": "%d %b %Y",
        "expected": {"category": "Internship", "company": "Deccan Logistics AI",
                     "role": "Operations Analyst Intern", "location": "Hyderabad",
                     "stipend_month": 20000, "cgpa_min": 6.0, "batch": [2028],
                     "branches": ["ALL"]},
    },
    # 21
    {
        "text": """Nilgiri Networks – Network Engineer

CTC: 5 LPA
Location: Kochi
Branches: ECE, CSE, IT
Batch: 2027
CGPA cutoff: 6.0
CCNA certification is a plus.
Apply before {deadline}: https://nilgiri-networks.example/ne-campus""",
        "deadline_days": 4, "deadline_format": "%d-%m-%Y",
        "expected": {"category": "Full-time", "company": "Nilgiri Networks",
                     "role": "Network Engineer", "location": "Kochi", "ctc_lpa": 5.0,
                     "cgpa_min": 6.0, "batch": [2027], "branches": ["ECE", "CSE", "IT"]},
    },
    # 22
    {
        "text": """Ashoka Retail Labs – Product Analyst 🛒

CTC: 9.5 LPA
Location: Bengaluru
Eligibility: All branches | 2027 batch | 7.5 CGPA and above
Rounds: Online assessment, guesstimate round, 2 interviews
Last date: {deadline}
Register: https://ashoka-retail.example/pa-2027""",
        "deadline_days": 7, "deadline_format": "%d %B %Y",
        "expected": {"category": "Full-time", "company": "Ashoka Retail Labs",
                     "role": "Product Analyst", "location": "Bengaluru", "ctc_lpa": 9.5,
                     "cgpa_min": 7.5, "batch": [2027], "branches": ["ALL"]},
    },
    # 23
    {
        "text": """Reminder: All final-year students must upload their updated resume to the
placement portal by {deadline}. Students who miss this will not be shortlisted
for upcoming drives.""",
        "deadline_days": 1, "deadline_format": "%d %b %Y",
        "expected": {"category": "Other", "company": None, "role": None},
    },
    # 24
    {
        "text": """Brahmaputra Motors – Graduate Engineer Trainee (Mechanical)

CTC: Rs 4.8 Lakhs p.a.
Location: Pune (plant)
Branch: Mechanical only
Batch: 2027 | CGPA: 6.0+
Last date: {deadline}
https://brahmaputra-motors.example/get-mech""",
        "deadline_days": 10, "deadline_format": "%d/%m/%Y",
        "expected": {"category": "Full-time", "company": "Brahmaputra Motors",
                     "role": "Graduate Engineer Trainee", "location": "Pune", "ctc_lpa": 4.8,
                     "cgpa_min": 6.0, "batch": [2027], "branches": ["MECH"]},
    },
    # 25
    {
        "text": """🔥 Konark Payments – SDE-1 🔥

CTC: 14 LPA
Location: Bengaluru
Eligibility: CSE / ISE / IT | 2027 batch | CGPA 8.0 and above
Rounds: Coding test, 2 technical interviews, HR
Apply by {deadline}
Link: https://konark-payments.example/careers/sde1""",
        "deadline_days": 3, "deadline_format": "%d %b %Y",
        "expected": {"category": "Full-time", "company": "Konark Payments", "role": "SDE-1",
                     "location": "Bengaluru", "ctc_lpa": 14.0, "cgpa_min": 8.0,
                     "batch": [2027], "branches": ["CSE", "ISE", "IT"]},
    },
    # 26
    {
        "text": """Tungabhadra Steel – Management Trainee

Package: 6 LPA
Location: Ballari
Branches: EEE, Mechanical, Civil
Batch: 2027 | Minimum CGPA 6.0
Last date to apply: {deadline}
https://tungabhadra-steel.example/mt-2027""",
        "deadline_days": 9, "deadline_format": "%d %B %Y",
        "expected": {"category": "Full-time", "company": "Tungabhadra Steel",
                     "role": "Management Trainee", "location": "Ballari", "ctc_lpa": 6.0,
                     "cgpa_min": 6.0, "batch": [2027], "branches": ["EEE", "MECH", "CIVIL"]},
    },
    # 27
    {
        "text": """Narmada Insights – Data Analyst Intern

Stipend: ₹15K per month
Location: Remote
Open to all branches, 2028 batch, CGPA 6.5 and above
Excel and SQL basics needed.
Deadline: {deadline}
Apply: https://narmada-insights.example/intern/da""",
        "deadline_days": 5, "deadline_format": "%d-%m-%Y",
        "expected": {"category": "Internship", "company": "Narmada Insights",
                     "role": "Data Analyst Intern", "location": "Remote", "stipend_month": 15000,
                     "cgpa_min": 6.5, "batch": [2028], "branches": ["ALL"]},
    },
    # 28
    {
        "text": """⚙️ Himalaya CloudOps DevOps Challenge ⚙️

Automate a real deployment pipeline in 48 hours. Teams of up to 3.
Mode: Online
Open to all branches, 2027 and 2028 batches.
Top teams get fast-track interviews.
Registration closes on {deadline}
https://himalaya-cloudops.example/devops-challenge""",
        "deadline_days": 6, "deadline_format": "%d %b %Y",
        "expected": {"category": "Hackathon", "company": "Himalaya CloudOps", "role": None,
                     "location": "Remote", "batch": [2027, 2028], "branches": ["ALL"]},
    },
    # 29
    {
        "text": """Kestrel Security – Security Analyst

CTC: 7 LPA
Location: Chennai
Eligibility: CSE / ISE / IT, 2027 batch, CGPA 7.0 and above
Knowledge of networking and Linux is preferred.
Apply before {deadline}
https://kestrel-security.example/campus/sa""",
        "deadline_days": 2, "deadline_format": "%d/%m/%Y",
        "expected": {"category": "Full-time", "company": "Kestrel Security",
                     "role": "Security Analyst", "location": "Chennai", "ctc_lpa": 7.0,
                     "cgpa_min": 7.0, "batch": [2027], "branches": ["CSE", "ISE", "IT"]},
    },
    # 30
    {
        "text": """Mango Commerce – Full Stack Developer Intern

Stipend: Rs 30,000 per month
Location: Bengaluru
Eligibility: CSE, ISE | 2027 batch | CGPA 7.0+
Stack: Node.js, React, MongoDB
Last date: {deadline}
Apply: https://mango-commerce.example/intern/fullstack""",
        "deadline_days": 3, "deadline_format": "%d %B %Y",
        "expected": {"category": "Internship", "company": "Mango Commerce",
                     "role": "Full Stack Developer Intern", "location": "Bengaluru",
                     "stipend_month": 30000, "cgpa_min": 7.0, "batch": [2027],
                     "branches": ["CSE", "ISE"]},
    },
    # 31
    {
        "text": """Peacock Media is hiring Digital Marketing Associates

CTC: 4 LPA
Location: Mumbai
Open to all branches, 2027 batch, CGPA 6.0 and above
Apply by {deadline}
https://peacock-media.example/dma-campus""",
        "deadline_days": 11, "deadline_format": "%d %b %Y",
        "expected": {"category": "Full-time", "company": "Peacock Media",
                     "role": "Digital Marketing Associate", "location": "Mumbai", "ctc_lpa": 4.0,
                     "cgpa_min": 6.0, "batch": [2027], "branches": ["ALL"]},
    },
    # 32
    {
        "text": """Vayu Avionics – Embedded Software Engineer ✈️

CTC: 8.5 LPA
Location: Bengaluru
Branches: ECE, EEE, CSE
Batch: 2027
CGPA: 7.0 and above
Skills: C, microcontrollers, RTOS basics
Deadline: {deadline}
https://vayu-avionics.example/careers/ese""",
        "deadline_days": 13, "deadline_format": "%d-%m-%Y",
        "expected": {"category": "Full-time", "company": "Vayu Avionics",
                     "role": "Embedded Software Engineer", "location": "Bengaluru",
                     "ctc_lpa": 8.5, "cgpa_min": 7.0, "batch": [2027],
                     "branches": ["ECE", "EEE", "CSE"]},
    },
    # 33
    {
        "text": """The placement cell is organising a 3-day aptitude and soft skills workshop
from Monday in the main auditorium. All final-year students should attend.
Contact your class coordinator for the schedule.""",
        "deadline_days": None,
        "expected": {"category": "Other", "company": None, "role": None},
    },
    # 34
    {
        "text": """Himalaya CloudOps – Site Reliability Engineer Intern

Stipend: ₹35,000/month
Location: Hyderabad
Eligibility: CSE / ISE / IT, 2027 batch, CGPA 7.5 and above
Skills: Linux, Docker, scripting (Bash or Python)
Apply by {deadline}: https://himalaya-cloudops.example/intern/sre""",
        "deadline_days": 4, "deadline_format": "%d %b %Y",
        "expected": {"category": "Internship", "company": "Himalaya CloudOps",
                     "role": "Site Reliability Engineer Intern", "location": "Hyderabad",
                     "stipend_month": 35000, "cgpa_min": 7.5, "batch": [2027],
                     "branches": ["CSE", "ISE", "IT"]},
    },
    # 35
    {
        "text": """Rangoli Design Studio – UI/UX Design Intern 🎨

Stipend: Rs. 18000 per month
Location: Remote
Open to all branches, 2028 batch, CGPA 6.0 and above
Please attach a portfolio link in the form.
Deadline: {deadline}
https://rangoli-design.example/intern/uiux""",
        "deadline_days": 8, "deadline_format": "%d/%m/%Y",
        "expected": {"category": "Internship", "company": "Rangoli Design Studio",
                     "role": "UI/UX Design Intern", "location": "Remote", "stipend_month": 18000,
                     "cgpa_min": 6.0, "batch": [2028], "branches": ["ALL"]},
    },
    # 36
    {
        "text": """Nimbus Analytics – Machine Learning Engineer

CTC: 11 LPA
Location: Bengaluru
Eligibility: CSE / AIML / DS | 2027 batch | CGPA 8.0 and above
Rounds: ML assignment, technical interview, HR
Last date to apply: {deadline}
Apply: https://careers.nimbus-analytics.example/apply/mle-2027""",
        "deadline_days": 6, "deadline_format": "%d %B %Y",
        "expected": {"category": "Full-time", "company": "Nimbus Analytics",
                     "role": "Machine Learning Engineer", "location": "Bengaluru",
                     "ctc_lpa": 11.0, "cgpa_min": 8.0, "batch": [2027],
                     "branches": ["CSE", "AIML", "DS"]},
    },
    # 37
    {
        "text": """Kaveri Systems – QA Engineer

CTC: 5 LPA
Location: Chennai
Branches: CSE, ISE, ECE, IT
Batch: 2027 | CGPA 6.0 and above
Apply before {deadline}
https://forms.kaveri-systems.example/qa-2027""",
        "deadline_days": 1, "deadline_format": "%d %b %Y",
        "expected": {"category": "Full-time", "company": "Kaveri Systems", "role": "QA Engineer",
                     "location": "Chennai", "ctc_lpa": 5.0, "cgpa_min": 6.0, "batch": [2027],
                     "branches": ["CSE", "ISE", "ECE", "IT"]},
    },
    # 38
    {
        "text": """💳 Konark Payments FinHack 💳

24-hour offline hackathon on the future of UPI payments.
Venue: Konark Payments office, Bengaluru
Open to all branches, 2027 and 2028 batches. Teams of 2-4.
Registration closes on {deadline}
https://konark-payments.example/finhack""",
        "deadline_days": 7, "deadline_format": "%d-%m-%Y",
        "expected": {"category": "Hackathon", "company": "Konark Payments", "role": None,
                     "location": "Bengaluru", "batch": [2027, 2028], "branches": ["ALL"]},
    },
    # 39
    {
        "text": """Zephyr Fintech – Risk Analyst Intern

Stipend: ₹25,000 per month
Location: Mumbai
Open to all branches, 2028 batch, CGPA 7.0 and above
Deadline: {deadline}
Apply: https://zephyr-fintech.example/careers/risk-intern""",
        "deadline_days": 10, "deadline_format": "%d %b %Y",
        "expected": {"category": "Internship", "company": "Zephyr Fintech",
                     "role": "Risk Analyst Intern", "location": "Mumbai", "stipend_month": 25000,
                     "cgpa_min": 7.0, "batch": [2028], "branches": ["ALL"]},
    },
    # 40
    {
        "text": """Orbitron Technologies – Cloud Engineer

CTC: 7 LPA
Location: Hyderabad
Eligible branches: CSE, ISE, IT, ECE
Batch: 2027 | CGPA 6.5 and above
AWS or Azure certification is a plus.
Last date: {deadline}
https://orbitron-tech.example/drive/cloud-engineer""",
        "deadline_days": -1, "deadline_format": "%d/%m/%Y",
        "expected": {"category": "Full-time", "company": "Orbitron Technologies",
                     "role": "Cloud Engineer", "location": "Hyderabad", "ctc_lpa": 7.0,
                     "cgpa_min": 6.5, "batch": [2027], "branches": ["CSE", "ISE", "IT", "ECE"]},
    },
    # 41
    {
        "text": """Coralbyte – Android Developer (Full Time)

CTC: 9 LPA
Location: Remote
Eligibility: CSE / IT, 2027 batch, CGPA 7.0+
Kotlin experience preferred.
Apply by {deadline}
https://coralbyte.example/jobs/android""",
        "deadline_days": 5, "deadline_format": "%d %B %Y",
        "expected": {"category": "Full-time", "company": "Coralbyte",
                     "role": "Android Developer", "location": "Remote", "ctc_lpa": 9.0,
                     "cgpa_min": 7.0, "batch": [2027], "branches": ["CSE", "IT"]},
    },
    # 42
    {
        "text": """Saptarishi Software – Software Engineer Intern

Stipend: Rs 22,000/month
Location: Mysuru
Eligibility: CSE / ISE / AIML / DS, 2027 batch, CGPA 7.0 and above
Duration: 6 months with possible full-time offer
Deadline: {deadline}
https://saptarishi-software.example/intern/swe""",
        "deadline_days": 2, "deadline_format": "%d %b %Y",
        "expected": {"category": "Internship", "company": "Saptarishi Software",
                     "role": "Software Engineer Intern", "location": "Mysuru",
                     "stipend_month": 22000, "cgpa_min": 7.0, "batch": [2027],
                     "branches": ["CSE", "ISE", "AIML", "DS"]},
    },
    # 43
    {
        "text": """Ganga Health Tech – Clinical Data Analyst

CTC: 6 LPA
Location: Noida
Open to all branches, 2027 batch, CGPA 6.5 and above
Last date to apply: {deadline}
https://ganga-healthtech.example/cda-2027""",
        "deadline_days": 8, "deadline_format": "%d-%m-%Y",
        "expected": {"category": "Full-time", "company": "Ganga Health Tech",
                     "role": "Clinical Data Analyst", "location": "Noida", "ctc_lpa": 6.0,
                     "cgpa_min": 6.5, "batch": [2027], "branches": ["ALL"]},
    },
    # 44
    {
        "text": """🏁 Deccan Code Sprint – coding contest by Deccan Logistics AI 🏁

90-minute online coding contest. Top 20 coders get interview calls.
Mode: Online
Open to all branches, 2027 and 2028 batches.
Register before {deadline}
https://deccan-logistics.example/codesprint""",
        "deadline_days": 2, "deadline_format": "%d %B %Y",
        "expected": {"category": "Hackathon", "company": "Deccan Logistics AI", "role": None,
                     "location": "Remote", "batch": [2027, 2028], "branches": ["ALL"]},
    },
    # 45
    {
        "text": """Congratulations to the 14 students selected by Kaveri Systems in
yesterday's drive! 🎉 The final list is on the placement portal.
Offer letters will be shared by HR next week.""",
        "deadline_days": None,
        "expected": {"category": "Other", "company": "Kaveri Systems", "role": None},
    },
    # 46
    {
        "text": """Lotus Cloudworks – DevOps Intern ☁️

Stipend: ₹28,000 per month
Location: Bengaluru
Eligibility: CSE / ISE / IT | 2027 batch | CGPA 7.0 and above
Skills: Linux, Git, Docker, any one cloud (AWS preferred)
Apply by {deadline}
https://lotus-cloudworks.example/intern/devops""",
        "deadline_days": 3, "deadline_format": "%d/%m/%Y",
        "expected": {"category": "Internship", "company": "Lotus Cloudworks",
                     "role": "DevOps Intern", "location": "Bengaluru", "stipend_month": 28000,
                     "cgpa_min": 7.0, "batch": [2027], "branches": ["CSE", "ISE", "IT"]},
    },
    # 47
    {
        "text": """Konark Payments – Data Analyst

CTC: 7-9 LPA
Location: Bengaluru
Open to all branches, 2027 batch, CGPA 7.0 and above
Rounds: SQL test, case study, interview
Deadline: {deadline}
https://konark-payments.example/careers/data-analyst""",
        "deadline_days": 6, "deadline_format": "%d %b %Y",
        "expected": {"category": "Full-time", "company": "Konark Payments",
                     "role": "Data Analyst", "location": "Bengaluru", "ctc_lpa": 9.0,
                     "cgpa_min": 7.0, "batch": [2027], "branches": ["ALL"]},
    },
    # 48 - duplicate of #1 (forwarded again: different emojis, case and spacing)
    {
        "text": """🚨🚨 PLACEMENT DRIVE ALERT 🚨🚨

Company: Nimbus Analytics
Role: Data Analyst
CTC: 7.5 LPA
Location: Bengaluru
Eligibility: B.Tech CSE / ISE / AIML / DS,  2027 batch,  CGPA 7.0 and above, no active backlogs
Last date to apply: {deadline}
Register here: https://careers.nimbus-analytics.example/apply/da-2027

- Training & Placement Office""",
        "deadline_days": 2, "deadline_format": "%d %b %Y", "duplicate_of": 1,
        "expected": {"category": "Full-time", "company": "Nimbus Analytics", "role": "Data Analyst",
                     "location": "Bengaluru", "ctc_lpa": 7.5, "cgpa_min": 7.0, "batch": [2027],
                     "branches": ["CSE", "ISE", "AIML", "DS"]},
    },
    # 49 - duplicate of #3
    {
        "text": """Internship Opportunity!!

Tridentia Labs - SDE Intern (6 months)
Stipend: ₹40,000/month
Location: Bengaluru (on-site)
Who can apply: CSE & ISE students of 2027 batch with 8.0+ CGPA
Apply by {deadline}: https://tridentia-labs.example/jobs/sde-intern""",
        "deadline_days": 1, "deadline_format": "%d-%m-%Y", "duplicate_of": 3,
        "expected": {"category": "Internship", "company": "Tridentia Labs", "role": "SDE Intern",
                     "location": "Bengaluru", "stipend_month": 40000, "cgpa_min": 8.0,
                     "batch": [2027], "branches": ["CSE", "ISE"]},
    },
    # 50 - duplicate of #25
    {
        "text": """konark payments – sde-1

ctc: 14 lpa
location: bengaluru
eligibility: cse / ise / it | 2027 batch | cgpa 8.0 and above
rounds: coding test, 2 technical interviews, hr
apply by {deadline}
link: https://konark-payments.example/careers/sde1""",
        "deadline_days": 3, "deadline_format": "%d %b %Y", "duplicate_of": 25,
        "expected": {"category": "Full-time", "company": "Konark Payments", "role": "SDE-1",
                     "location": "Bengaluru", "ctc_lpa": 14.0, "cgpa_min": 8.0,
                     "batch": [2027], "branches": ["CSE", "ISE", "IT"]},
    },
]


def deadline_for(message: dict[str, Any], today: date) -> date | None:
    """The concrete deadline date for a message, relative to `today`."""
    days = message.get("deadline_days")
    return None if days is None else today + timedelta(days=days)


def render_message(message: dict[str, Any], today: date) -> str:
    """Fill the {deadline} placeholder using the message's own date format."""
    text: str = message["text"]
    deadline = deadline_for(message, today)
    if deadline is not None:
        text = text.replace("{deadline}", deadline.strftime(message["deadline_format"]))
    return text
