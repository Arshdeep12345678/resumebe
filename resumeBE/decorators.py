from functools import wraps

import jwt
from flask import jsonify, make_response, request

import globals

blacklist = globals.db.blacklist


def jwt_required(func):
    """Only lets the request through if it has a valid, not logged-out token."""
    @wraps(func)
    def jwt_required_wrapper(*args, **kwargs):
        token = request.headers.get("x-access-token")
        if not token:
            return make_response(jsonify({"error": "Token is missing"}), 401)
        try:
            jwt.decode(token, globals.secret_key, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return make_response(jsonify({"error": "Token has expired"}), 401)
        except jwt.InvalidTokenError:
            return make_response(jsonify({"error": "Token is invalid"}), 401)
        if blacklist.find_one({"token": token}):
            return make_response(jsonify({"error": "Token has been cancelled"}), 401)
        return func(*args, **kwargs)
    return jwt_required_wrapper


def admin_required(func):
    """Only lets admins through. Always used after @jwt_required."""
    @wraps(func)
    def admin_required_wrapper(*args, **kwargs):
        token = request.headers.get("x-access-token")
        data = jwt.decode(token, globals.secret_key, algorithms=["HS256"])
        if data["admin"]:
            return func(*args, **kwargs)
        return make_response(jsonify({"error": "Admin access required"}), 403)
    return admin_required_wrapper


def current_user():
    """Username stored inside the token of the current request."""
    token = request.headers.get("x-access-token")
    return jwt.decode(token, globals.secret_key, algorithms=["HS256"])["user"]
