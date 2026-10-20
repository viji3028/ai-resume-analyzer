
import re
import fitz
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SKILLS = [
    "python", "sql", "excel", "power bi", "statistics",
    "machine learning", "html", "css", "javascript",
    "git", "apis", "pandas", "numpy", "communication"
]


def extract_resume_text(pdf_bytes):
    text = ""

    with fitz.open(stream=pdf_bytes, filetype="pdf") as pdf:
        for page in pdf:
            text += page.get_text() + "\n"

    return text.lower()


def extract_skills(text):
    text = text.lower()
    found = []

    for skill in SKILLS:
        pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"
        if re.search(pattern, text):
            found.append(skill)

    return found


def compare_resume(resume_text, job):
    required = [
        skill.strip().lower()
        for skill in job["required_skills"].split(",")
    ]

    resume_skills = extract_skills(resume_text)

    matched = [s for s in required if s in resume_skills]
    missing = [s for s in required if s not in resume_skills]

    skill_score = (
        len(matched) / len(required) * 100
        if required else 0
    )

    documents = [resume_text, job["description"]]
    vectorizer = TfidfVectorizer()
    matrix = vectorizer.fit_transform(documents)

    similarity = cosine_similarity(
        matrix[0:1], matrix[1:2]
    )[0][0] * 100

    overall_score = 0.7 * skill_score + 0.3 * similarity

    return {
        "resume_skills": resume_skills,
        "matched_skills": matched,
        "missing_skills": missing,
        "skill_score": round(skill_score, 1),
        "text_similarity": round(similarity, 1),
        "overall_score": round(overall_score, 1)
    }


def load_jobs():
    return pd.read_csv("jobs.csv")
