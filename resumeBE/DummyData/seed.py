# Fills the database with test data. Run: python DummyData/seed.py
# Logins: admin / admin123 (admin), recruiter / recruiter123
import random

import bcrypt
from bson import ObjectId
from pymongo import MongoClient

client = MongoClient("mongodb://127.0.0.1:27017")
db = client.resumeAnalyserDB

random.seed(661)

FIRST = ["Aoife", "Ciaran", "Niamh", "Sean", "Priya", "Arjun", "Emma", "Jack", "Sofia",
         "Liam", "Grace", "Ryan", "Chloe", "Adam", "Hannah", "Omar", "Zara", "Daniel",
         "Megan", "Harpreet"]
LAST = ["Murphy", "Kelly", "O'Neill", "Walsh", "Sharma", "Singh", "Smith", "Brown",
        "Wilson", "Campbell", "Patel", "Doherty", "Quinn", "Khan", "Taylor"]
CITIES = ["Belfast", "Derry", "Coleraine", "Lisburn", "Dublin", "London", "Manchester"]

# Each role has a set of skills people in that role usually have
ROLES = {
    "Backend Developer": ["python", "flask", "mongodb", "sql", "rest api", "git", "docker", "linux"],
    "Frontend Developer": ["javascript", "typescript", "angular", "react", "html", "css", "git"],
    "Data Analyst": ["python", "sql", "excel", "power bi", "pandas", "statistics", "tableau"],
    "DevOps Engineer": ["docker", "kubernetes", "aws", "azure", "linux", "ci/cd", "terraform"],
    "Software Tester": ["selenium", "python", "java", "unit testing", "jira", "git", "sql"],
}

COMMENTS = [
    ("Strong technical skills, invite to interview", 5),
    ("Good experience but missing cloud skills", 3),
    ("CV is clear and well laid out", 4),
    ("Not enough experience for senior roles", 2),
    ("Great projects on GitHub", 5),
]


def make_users():
    db.users.drop()
    db.users.insert_many([
        {"username": "admin", "name": "Site Admin", "email": "admin@resume.com",
         "password": bcrypt.hashpw(b"admin123", bcrypt.gensalt()), "admin": True},
        {"username": "recruiter", "name": "Rachel Recruiter", "email": "rachel@resume.com",
         "password": bcrypt.hashpw(b"recruiter123", bcrypt.gensalt()), "admin": False},
    ])


def make_resumes(how_many=40):
    db.resumes.drop()
    resume_list = []
    for i in range(how_many):
        first, last = random.choice(FIRST), random.choice(LAST)
        title = random.choice(list(ROLES))
        skills = random.sample(ROLES[title], random.randint(3, len(ROLES[title])))

        notes = []
        for comment, rating in random.sample(COMMENTS, random.randint(0, 2)):
            notes.append({"_id": ObjectId(), "author": "recruiter",
                          "comment": comment, "rating": rating})

        resume_list.append({
            "name": first + " " + last,
            "email": (first + "." + last + str(i)).lower().replace("'", "") + "@mail.com",
            "title": title,
            "location": random.choice(CITIES),
            "years_experience": random.randint(0, 12),
            "skills": skills,
            "owner": "admin",
            "notes": notes,
        })
    db.resumes.insert_many(resume_list)


def make_jobs():
    db.jobs.drop()
    db.jobs.insert_many([
        {"title": "Junior Python Developer", "company": "Kainos", "location": "Belfast",
         "required_skills": ["python", "flask", "sql", "git"], "nice_skills": ["docker", "mongodb"],
         "min_experience": 1, "posted_by": "admin"},
        {"title": "Angular Developer", "company": "Allstate", "location": "Belfast",
         "required_skills": ["angular", "typescript", "html", "css"], "nice_skills": ["git"],
         "min_experience": 2, "posted_by": "admin"},
        {"title": "Data Analyst", "company": "Citi", "location": "Belfast",
         "required_skills": ["sql", "excel", "power bi"], "nice_skills": ["python", "tableau"],
         "min_experience": 2, "posted_by": "admin"},
        {"title": "Cloud Engineer", "company": "Version 1", "location": "Dublin",
         "required_skills": ["azure", "docker", "linux"], "nice_skills": ["terraform", "kubernetes"],
         "min_experience": 3, "posted_by": "admin"},
        {"title": "QA Tester", "company": "Liberty IT", "location": "Derry",
         "required_skills": ["selenium", "unit testing", "jira"], "nice_skills": ["python"],
         "min_experience": 0, "posted_by": "admin"},
    ])


if __name__ == "__main__":
    make_users()
    make_resumes()
    make_jobs()
    db.blacklist.drop()
    print("Done: 2 users, 40 resumes, 5 jobs added to resumeAnalyserDB")
