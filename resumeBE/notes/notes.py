from bson import ObjectId
from flask import Blueprint, jsonify, make_response, request

import globals
from decorators import admin_required, current_user, jwt_required

notes_bp = Blueprint("notes_bp", __name__)

resumes = globals.db.resumes

# Notes are recruiter comments stored INSIDE a resume (a sub-document list):
#   resume = { ..., "notes": [ {_id, author, comment, rating}, ... ] }


def check_ids(*ids):
    for one_id in ids:
        if not ObjectId.is_valid(one_id):
            return make_response(jsonify({"error": "Invalid ID: " + one_id}), 400)
    return None


def read_rating():
    """Returns (rating, error_response)."""
    body = globals.get_body()
    try:
        rating = int(body.get("rating", ""))
    except ValueError:
        return None, make_response(jsonify({"error": "rating must be a whole number"}), 400)
    if rating < 1 or rating > 5:
        return None, make_response(jsonify({"error": "rating must be between 1 and 5"}), 400)
    return rating, None


@notes_bp.route("/api/v1.0/resumes/<string:id>/notes", methods=["GET"])
def fetch_all_notes(id):
    bad = check_ids(id)
    if bad:
        return bad

    resume = resumes.find_one({"_id": ObjectId(id)}, {"notes": 1, "_id": 0})
    if resume is None:
        return make_response(jsonify({"error": "Resume not found"}), 404)

    data_to_return = []
    for note in resume["notes"]:
        note["_id"] = str(note["_id"])
        data_to_return.append(note)
    return make_response(jsonify(data_to_return), 200)


@notes_bp.route("/api/v1.0/resumes/<string:id>/notes/<string:nid>", methods=["GET"])
def fetch_one_note(id, nid):
    bad = check_ids(id, nid)
    if bad:
        return bad

    resume = resumes.find_one({"_id": ObjectId(id), "notes._id": ObjectId(nid)},
                              {"_id": 0, "notes.$": 1})
    if resume is None:
        return make_response(jsonify({"error": "Resume or note not found"}), 404)

    note = resume["notes"][0]
    note["_id"] = str(note["_id"])
    return make_response(jsonify(note), 200)


@notes_bp.route("/api/v1.0/resumes/<string:id>/notes", methods=["POST"])
@jwt_required
def add_note(id):
    body = globals.get_body()
    bad = check_ids(id)
    if bad:
        return bad
    if not body.get("comment", "").strip():
        return make_response(jsonify({"error": "Missing field: comment"}), 400)
    rating, error = read_rating()
    if error:
        return error

    new_note = {
        "_id": ObjectId(),
        "author": current_user(),
        "comment": body["comment"].strip(),
        "rating": rating,
    }
    result = resumes.update_one({"_id": ObjectId(id)}, {"$push": {"notes": new_note}})
    if result.matched_count == 0:
        return make_response(jsonify({"error": "Resume not found"}), 404)

    new_link = "http://127.0.0.1:8000/api/v1.0/resumes/" + id + "/notes/" + str(new_note["_id"])
    return make_response(jsonify({"url": new_link}), 201)


@notes_bp.route("/api/v1.0/resumes/<string:id>/notes/<string:nid>", methods=["PUT"])
@jwt_required
def edit_note(id, nid):
    body = globals.get_body()
    bad = check_ids(id, nid)
    if bad:
        return bad
    if not body.get("comment", "").strip():
        return make_response(jsonify({"error": "Missing field: comment"}), 400)
    rating, error = read_rating()
    if error:
        return error

    result = resumes.update_one(
        {"_id": ObjectId(id), "notes._id": ObjectId(nid)},
        {"$set": {"notes.$.comment": body["comment"].strip(),
                  "notes.$.rating": rating}})
    if result.matched_count == 0:
        return make_response(jsonify({"error": "Resume or note not found"}), 404)

    edit_link = "http://127.0.0.1:8000/api/v1.0/resumes/" + id + "/notes/" + nid
    return make_response(jsonify({"url": edit_link}), 200)


@notes_bp.route("/api/v1.0/resumes/<string:id>/notes/<string:nid>", methods=["DELETE"])
@jwt_required
@admin_required
def delete_note(id, nid):
    bad = check_ids(id, nid)
    if bad:
        return bad

    result = resumes.update_one({"_id": ObjectId(id)},
                                {"$pull": {"notes": {"_id": ObjectId(nid)}}})
    if result.modified_count == 0:
        return make_response(jsonify({"error": "Resume or note not found"}), 404)
    return make_response(jsonify({}), 204)
