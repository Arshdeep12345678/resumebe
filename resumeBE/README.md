# Resume Analyser – Back End (COM661 CW1)

**Arshdeep Singh – B01002953**

A REST API built with **Flask** and **MongoDB**. Recruiters store candidate resumes, write notes on them and post jobs. For any job, the API ranks all resumes with a **match score out of 100**.

---

## Project structure

```
resumeBE/
├── app.py               # starts the app and registers the blueprints
├── globals.py           # MongoDB connection and secret key
├── decorators.py        # @jwt_required and @admin_required
├── auth/auth.py         # register, login, logout
├── resumes/resumes.py   # resumes CRUD, pagination and filters
├── notes/notes.py       # notes inside a resume (sub-documents)
├── jobs/jobs.py         # jobs CRUD + match score
├── DummyData/seed.py    # fills the database with test data
├── postman/             # Postman collection (44 requests with tests)
└── requirements.txt
```

## How to run

1. Start MongoDB (`127.0.0.1:27017`)
2. Install packages
   ```bash
   pip install -r requirements.txt
   ```
3. Add test data
   ```bash
   python DummyData/seed.py
   ```
4. Start the API
   ```bash
   python app.py
   ```
   The API runs at `http://127.0.0.1:8000/api/v1.0`
5. In Postman, import `postman/ResumeBE.postman_collection.json` and click **Run collection**.

## Test logins

| Username  | Password     | Admin |
|-----------|--------------|-------|
| admin     | admin123     | Yes   |
| recruiter | recruiter123 | No    |

## Who can do what

| User       | Can do |
|------------|--------|
| Anyone     | View resumes, notes, jobs and match scores; register; login |
| Logged in  | Add / edit resumes, add / edit notes, logout |
| Admin only | Delete resumes, delete notes, add / edit / delete jobs |

## Endpoints

All URLs start with `/api/v1.0`

| Method | URL | Access |
|--------|-----|--------|
| POST   | `/register` | Anyone |
| GET    | `/login` | Basic auth, returns a token |
| GET    | `/logout` | Token |
| GET    | `/resumes?pn=1&ps=10&skill=python&location=belfast` | Anyone |
| GET    | `/resumes/<id>` | Anyone |
| POST   | `/resumes` | Token |
| PUT    | `/resumes/<id>` | Token |
| DELETE | `/resumes/<id>` | Admin |
| GET    | `/resumes/<id>/notes` | Anyone |
| GET    | `/resumes/<id>/notes/<nid>` | Anyone |
| POST   | `/resumes/<id>/notes` | Token |
| PUT    | `/resumes/<id>/notes/<nid>` | Token |
| DELETE | `/resumes/<id>/notes/<nid>` | Admin |
| GET    | `/jobs` | Anyone |
| GET    | `/jobs/<id>` | Anyone |
| POST   | `/jobs` | Admin |
| PUT    | `/jobs/<id>` | Admin |
| DELETE | `/jobs/<id>` | Admin |
| GET    | `/jobs/<id>/matches?min_score=50` | Anyone |

- The token goes in a header called `x-access-token`.
- POST and PUT data is sent as **JSON** (Postman: Body → raw → JSON).

Example – add a resume:

```json
{
  "name": "Demo Candidate",
  "email": "demo@mail.com",
  "title": "Backend Developer",
  "location": "Belfast",
  "years_experience": 3,
  "skills": ["python", "flask", "sql", "git"]
}
```

## Match score

Found in `jobs/jobs.py` and calculated with a MongoDB aggregation pipeline:

```
score = 70 × (required skills the person has / all required skills)
      + 20 × (years experience / job's minimum years, max 1)
      + 10 × (nice-to-have skills the person has / all nice skills)
```

Results are sorted best first. The pipeline uses `$setIntersection` (matching skills), `$setDifference` (missing skills), `$size`, `$divide`, `$multiply`, `$min`, `$add`, `$round`, `$sort` and `$match`.

## Status codes

| Code | Meaning |
|------|---------|
| 200 | OK |
| 201 | Created |
| 204 | Deleted |
| 400 | Bad data or bad ID |
| 401 | No token, expired token or logged out |
| 403 | Not allowed (admin only) |
| 404 | Not found |
| 409 | Username already taken |