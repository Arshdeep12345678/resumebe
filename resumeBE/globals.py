from pymongo import MongoClient

# One connection to MongoDB, shared by every blueprint
client = MongoClient("mongodb://127.0.0.1:27017")
db = client.resumeAnalyserDB

# Used to sign and check the login tokens
secret_key = "arsh-resumeanalyser-project-2026-done"


def get_body():
   # Reads the request body (JSON or form) and turns every value into text
    from flask import request
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        data = request.form.to_dict()
    clean = {}
    for key, value in data.items():
        if isinstance(value, list):
            clean[key] = ", ".join(str(v) for v in value)
        elif value is None:
            clean[key] = ""
        else:
            clean[key] = str(value)
    return clean
