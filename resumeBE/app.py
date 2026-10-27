from flask import Flask, jsonify, make_response

from auth.auth import auth_bp
from jobs.jobs import jobs_bp
from notes.notes import notes_bp
from resumes.resumes import resumes_bp

app = Flask(__name__)

app.register_blueprint(auth_bp)
app.register_blueprint(resumes_bp)
app.register_blueprint(notes_bp)
app.register_blueprint(jobs_bp)


@app.route("/api/v1.0", methods=["GET"],strict_slashes=False)
def index():
    return make_response(jsonify({"message": "Resume Analyser API is running"}), 200)


@app.errorhandler(404)
def not_found(e):
    return make_response(jsonify({"error": "URL not found"}), 404)


if __name__ == "__main__":
    app.run(debug=True, port=8000)
