# app/api_auth.py
from flask import Blueprint, request, jsonify
from app import db, jwt
from app.models import User, TokenBlocklist
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from datetime import datetime
from zoneinfo import ZoneInfo

api_auth_bp = Blueprint("api_auth", __name__, url_prefix="/api/auth")

# helper to revoke token (store jti)
def revoke_token(jti, token_type, user_id=None):
    tb = TokenBlocklist(jti=jti, token_type=token_type, user_id=user_id, created_at=datetime.utcnow())
    db.session.add(tb)
    db.session.commit()

# -------------------------
# Register
# -------------------------
@api_auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not (username and email and password):
        return jsonify({"error": "username, email and password required"}), 400

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({"error": "Username or email already exists"}), 409

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Registration successful", "user": {"id": user.id, "username": user.username}}), 201


# -------------------------
# Login -> returns access & refresh tokens
# -------------------------
@api_auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not (email and password):
        return jsonify({"error": "email and password required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {"id": user.id, "username": user.username, "email": user.email}
    }), 200


# -------------------------
# Refresh -> exchange refresh token for new access token
# -------------------------
@api_auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    new_access_token = create_access_token(identity=identity)
    return jsonify({"access_token": new_access_token}), 200


# -------------------------
# Revoke access token (logout) - client should send access token in Authorization header
# -------------------------
@api_auth_bp.route("/logout_access", methods=["DELETE"])
@jwt_required()  # requires valid access token
def logout_access():
    jti = get_jwt()["jti"]
    identity = get_jwt_identity()
    revoke_token(jti=jti, token_type="access", user_id=identity)
    return jsonify({"message": "Access token revoked"}), 200


# -------------------------
# Revoke refresh token (logout/forget) - client sends refresh token in Authorization header
# -------------------------
@api_auth_bp.route("/logout_refresh", methods=["DELETE"])
@jwt_required(refresh=True)
def logout_refresh():
    jti = get_jwt()["jti"]
    identity = get_jwt_identity()
    revoke_token(jti=jti, token_type="refresh", user_id=identity)
    return jsonify({"message": "Refresh token revoked"}), 200


# -------------------------
# Example protected route (requires access token)
# -------------------------
@api_auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"id": user.id, "username": user.username, "email": user.email}), 200
