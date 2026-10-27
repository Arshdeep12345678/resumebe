from bson import ObjectId
from flask import Blueprint, jsonify, make_response, request

import globals
from decorators import admin_required, current_user, jwt_required

resumes_bp = Blueprint("resumes_bp", __name__)

resumes = globals.db.resumes


def to_json(resume):
    """MongoDB ObjectIds can't go into JSON, so turn them into strings."""
    resume["_id"] = str(resume["_id"])
    for note in resume.get("notes", []):
        note["_id"] = str(note["_id"])
    return resume


def read_skills(text):
    """'Python, Flask , mongodb' -> ['python', 'flask', 'mongodb']"""
    return [s.strip().lower() for s in text.split(",") if s.strip()]


@resumes_bp.route("/api/v1.0/resumes", methods=["GET"])
def show_all_resumes():
    page_num, page_size = 1, 10
    try:
        if request.args.get("pn"):
            page_num = int(request.args.get("pn"))
        if request.args.get("ps"):
            page_size = int(request.args.get("ps"))
    except ValueError:
        return make_response(jsonify({"error": "pn and ps must be whole numbers"}), 400)
    if page_num < 1 or page_size < 1 or page_size > 50:
        return make_response(jsonify({"error": "pn must be 1 or more and ps between 1 and 50"}), 400)
    page_start = (page_size * (page_num - 1))

    # Optional filters: ?skill=python  ?location=belfast
    query = {}
    if request.args.get("skill"):
        query["skills"] = request.args.get("skill").strip().lower()
    if request.args.get("location"):
        query["location"] = {"$regex": request.args.get("location").strip(), "$options": "i"}

    data_to_return = []
    for resume in resumes.find(query).skip(page_start).limit(page_size):
        data_to_return.append(to_json(resume))

    return make_response(jsonify(data_to_return), 200)


@resumes_bp.route("/api/v1.0/resumes/<string:id>", methods=["GET"])
def show_one_resume(id):
    if not ObjectId.is_valid(id):
        return make_response(jsonify({"error": "Invalid resume ID"}), 400)

    resume = resumes.find_one({"_id": ObjectId(id)})
    if resume is not None:
        return make_response(jsonify(to_json(resume)), 200)
    return make_response(jsonify({"error": "Resume not found"}), 404)


@resumes_bp.route("/api/v1.0/resumes", methods=["POST"])
@jwt_required
def add_resume():
    body = globals.get_body()
    fields = ["name", "email", "title", "location", "years_experience", "skills"]
    for field in fields:
        if not body.get(field, "").strip():
            return make_response(jsonify({"error": "Missing field: " + field}), 400)

    try:
        years = int(body["years_experience"])
    except ValueError:
        return make_response(jsonify({"error": "years_experience must be a whole number"}), 400)
    if years < 0 or years > 50:
        return make_response(jsonify({"error": "years_experience must be between 0 and 50"}), 400)
    if "@" not in body["email"]:
        return make_response(jsonify({"error": "Email is not valid"}), 400)

    new_resume = {
        "name": body["name"].strip(),
        "email": body["email"].strip().lower(),
        "title": body["title"].strip(),
        "location": body["location"].strip(),
        "years_experience": years,
        "skills": read_skills(body["skills"]),
        "owner": current_user(),
        "notes": [],
    }
    new_id = resumes.insert_one(new_resume).inserted_id
    new_link = "http://127.0.0.1:8000/api/v1.0/resumes/" + str(new_id)
    return make_response(jsonify({"url": new_link}), 201)


@resumes_bp.route("/api/v1.0/resumes/<string:id>", methods=["PUT"])
@jwt_required
def edit_resume(id):
    body = globals.get_body()
    if not ObjectId.is_valid(id):
        return make_response(jsonify({"error": "Invalid resume ID"}), 400)

    # Only send the fields you want to change
    changes = {}
    for field in ["name", "email", "title", "location"]:
        if body.get(field, "").strip():
            changes[field] = body[field].strip()
    if body.get("skills", "").strip():
        changes["skills"] = read_skills(body["skills"])
    if body.get("years_experience", "").strip():
        try:
            changes["years_experience"] = int(body["years_experience"])
        except ValueError:
            return make_response(jsonify({"error": "years_experience must be a whole number"}), 400)

    if not changes:
        return make_response(jsonify({"error": "Send at least one field to change"}), 400)

    result = resumes.update_one({"_id": ObjectId(id)}, {"$set": changes})
    if result.matched_count == 1:
        edited_link = "http://127.0.0.1:8000/api/v1.0/resumes/" + id
        return make_response(jsonify({"url": edited_link}), 200)
    return make_response(jsonify({"error": "Resume not found"}), 404)


@resumes_bp.route("/api/v1.0/resumes/<string:id>", methods=["DELETE"])
@jwt_required
@admin_required
def delete_resume(id):
    if not ObjectId.is_valid(id):
        return make_response(jsonify({"error": "Invalid resume ID"}), 400)

    result = resumes.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 1:
        return make_response(jsonify({}), 204)
    return make_response(jsonify({"error": "Resume not found"}), 404)
