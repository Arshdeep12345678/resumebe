from bson import ObjectId
from flask import Blueprint, jsonify, make_response, request

import globals
from decorators import admin_required, current_user, jwt_required

jobs_bp = Blueprint("jobs_bp", __name__)

jobs = globals.db.jobs
resumes = globals.db.resumes


def read_skills(text):
    return [s.strip().lower() for s in text.split(",") if s.strip()]


def to_json(job):
    job["_id"] = str(job["_id"])
    return job


def read_job_form(partial=False):
    """Reads the job fields from the body. Returns (job_dict, error_response)."""
    body = globals.get_body()
    job = {}
    for field in ["title", "company", "location"]:
        if body.get(field, "").strip():
            job[field] = body[field].strip()
        elif not partial:
            return None, make_response(jsonify({"error": "Missing field: " + field}), 400)

    if body.get("required_skills", "").strip():
        job["required_skills"] = read_skills(body["required_skills"])
    elif not partial:
        return None, make_response(jsonify({"error": "Missing field: required_skills"}), 400)

    if body.get("nice_skills", "").strip():
        job["nice_skills"] = read_skills(body["nice_skills"])
    elif not partial:
        job["nice_skills"] = []

    if body.get("min_experience", "").strip():
        try:
            job["min_experience"] = int(body["min_experience"])
        except ValueError:
            return None, make_response(jsonify({"error": "min_experience must be a whole number"}), 400)
        if job["min_experience"] < 0:
            return None, make_response(jsonify({"error": "min_experience can't be negative"}), 400)
    elif not partial:
        job["min_experience"] = 0

    return job, None

    
@jobs_bp.route("/api/v1.0/jobs", methods=["GET"])
def show_all_jobs():
    data_to_return = []
    for job in jobs.find():
        data_to_return.append(to_json(job))
    return make_response(jsonify(data_to_return), 200)


@jobs_bp.route("/api/v1.0/jobs/<string:id>", methods=["GET"])
def show_one_job(id):
    if not ObjectId.is_valid(id):
        return make_response(jsonify({"error": "Invalid job ID"}), 400)
    job = jobs.find_one({"_id": ObjectId(id)})
    if job is None:
        return make_response(jsonify({"error": "Job not found"}), 404)
    return make_response(jsonify(to_json(job)), 200)


@jobs_bp.route("/api/v1.0/jobs", methods=["POST"])
@jwt_required
@admin_required
def add_job():
    new_job, error = read_job_form()
    if error:
        return error
    new_job["posted_by"] = current_user()
    new_id = jobs.insert_one(new_job).inserted_id
    new_link = "http://127.0.0.1:8000/api/v1.0/jobs/" + str(new_id)
    return make_response(jsonify({"url": new_link}), 201)


@jobs_bp.route("/api/v1.0/jobs/<string:id>", methods=["PUT"])
@jwt_required
@admin_required
def edit_job(id):
    if not ObjectId.is_valid(id):
        return make_response(jsonify({"error": "Invalid job ID"}), 400)
    changes, error = read_job_form(partial=True)
    if error:
        return error
    if not changes:
        return make_response(jsonify({"error": "Send at least one field to change"}), 400)

    result = jobs.update_one({"_id": ObjectId(id)}, {"$set": changes})
    if result.matched_count == 0:
        return make_response(jsonify({"error": "Job not found"}), 404)
    return make_response(jsonify({"url": "http://127.0.0.1:8000/api/v1.0/jobs/" + id}), 200)


@jobs_bp.route("/api/v1.0/jobs/<string:id>", methods=["DELETE"])
@jwt_required
@admin_required
def delete_job(id):
    if not ObjectId.is_valid(id):
        return make_response(jsonify({"error": "Invalid job ID"}), 400)
    result = jobs.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        return make_response(jsonify({"error": "Job not found"}), 404)
    return make_response(jsonify({}), 204)


@jobs_bp.route("/api/v1.0/jobs/<string:id>/matches", methods=["GET"])
def match_resumes(id):
    """
    Ranks every resume against this job (best match first).

    match_score (out of 100) =
        70 x (required skills the person has / all required skills)
      + 20 x (years experience / min experience, capped at 1)
      + 10 x (nice-to-have skills the person has / all nice skills)
    """
    if not ObjectId.is_valid(id):
        return make_response(jsonify({"error": "Invalid job ID"}), 400)
    job = jobs.find_one({"_id": ObjectId(id)})
    if job is None:
        return make_response(jsonify({"error": "Job not found"}), 404)

    required = job["required_skills"]
    nice = job.get("nice_skills", [])
    min_exp = job.get("min_experience", 0)

    pipeline = [
        # 1. which skills match and which are missing
        {"$project": {
            "name": 1, "title": 1, "location": 1, "years_experience": 1,
            "matched_skills": {"$setIntersection": ["$skills", {"$literal": required}]},
            "missing_skills": {"$setDifference": [{"$literal": required}, "$skills"]},
            "matched_nice": {"$setIntersection": ["$skills", {"$literal": nice}]},
        }},
        # 2. the three parts of the score
        {"$addFields": {
            "skill_part": {"$multiply": [70, {"$divide": [{"$size": "$matched_skills"}, len(required)]}]},
            "exp_part": (20 if min_exp == 0 else
                         {"$multiply": [20, {"$min": [1, {"$divide": ["$years_experience", min_exp]}]}]}),
            "nice_part": (0 if len(nice) == 0 else
                          {"$multiply": [10, {"$divide": [{"$size": "$matched_nice"}, len(nice)]}]}),
        }},
        # 3. add them up and round to 1 decimal place
        {"$addFields": {
            "match_score": {"$round": [{"$add": ["$skill_part", "$exp_part", "$nice_part"]}, 1]},
        }},
        {"$project": {"skill_part": 0, "exp_part": 0, "nice_part": 0, "matched_nice": 0}},
        # 4. best first
        {"$sort": {"match_score": -1}},
    ]

    # Optional: ?min_score=50 to hide weak matches
    if request.args.get("min_score"):
        try:
            min_score = float(request.args.get("min_score"))
        except ValueError:
            return make_response(jsonify({"error": "min_score must be a number"}), 400)
        pipeline.append({"$match": {"match_score": {"$gte": min_score}}})

    data_to_return = []
    for resume in resumes.aggregate(pipeline):
        resume["_id"] = str(resume["_id"])
        data_to_return.append(resume)

    return make_response(jsonify({"job": job["title"], "results": data_to_return}), 200)
