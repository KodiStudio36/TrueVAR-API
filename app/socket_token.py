# app/socket_token.py
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import current_app

TOKEN_SALT = "socketio-session-v1"

def _serializer() -> URLSafeTimedSerializer:
    # Uses Flask SECRET_KEY; make sure it's set and strong
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=TOKEN_SALT)

def create_socket_token(*, license_key: str, machine_id: str) -> str:
    s = _serializer()
    payload = {
        "license_key": license_key,
        "machine_id": machine_id,
    }
    return s.dumps(payload)

def verify_socket_token(token: str, *, max_age_seconds: int) -> dict:
    s = _serializer()
    # Raises SignatureExpired / BadSignature on failure
    return s.loads(token, max_age=max_age_seconds)
