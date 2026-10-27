import datetime

import bcrypt
import jwt
from flask import Blueprint, jsonify, make_response, request

import globals
from decorators import jwt_required

auth_bp = Blueprint("auth_bp", __name__)

users = globals.db.users
blacklist = globals.db.blacklist


@auth_bp.route("/api/v1.0/register", methods=["POST"])
def register():
    body = globals.get_body()
    username = body.get("username", "").strip().lower()
    password = body.get("password", "")
    name = body.get("name", "").strip()
    email = body.get("email", "").strip().lower()

    if not username or not password or not name or not email:
        return make_response(jsonify({"error": "username, password, name and email are required"}), 400)
    if len(password) < 6:
        return make_response(jsonify({"error": "Password must be at least 6 characters"}), 400)
    if "@" not in email:
        return make_response(jsonify({"error": "Email is not valid"}), 400)
    if users.find_one({"username": username}):
        return make_response(jsonify({"error": "Username already taken"}), 409)

    new_user = {
        "username": username,
        "password": bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()),
        "name": name,
        "email": email,
        "admin": False,
    }
    new_id = users.insert_one(new_user).inserted_id
    return make_response(jsonify({"message": "User created", "_id": str(new_id)}), 201)


@auth_bp.route("/api/v1.0/login", methods=["GET"])
def login():
    auth = request.authorization

    if auth:
        user = users.find_one({"username": auth.username})

        if user is not None:
            if bcrypt.checkpw(bytes(auth.password, "utf-8"), user["password"]):
                token = jwt.encode({
                    "user": auth.username,
                    "admin": user["admin"],
                    "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=60),
                }, globals.secret_key, algorithm="HS256")
                return make_response(jsonify({"token": token, "admin": user["admin"]}), 200)
            else:
                return make_response(jsonify({"error": "Bad password"}), 401)
        else:
            return make_response(jsonify({"error": "Bad username"}), 401)

    return make_response(jsonify({"error": "Could not verify"}), 401,
                         {"WWW-Authenticate": 'Basic realm="Login required"'})


@auth_bp.route("/api/v1.0/logout", methods=["GET"])
@jwt_required
def logout():
    token = request.headers["x-access-token"]
    blacklist.insert_one({"token": token})
    return make_response(jsonify({"message": "Logout successful"}), 200)
