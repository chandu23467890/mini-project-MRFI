from datetime import datetime

from flask import Blueprint, jsonify, request

from middleware.auth import generate_token, hash_password, token_required, verify_password
from models import AuditLog, User, db

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    required = ["name", "email", "password"]
    missing = [field for field in required if not data.get(field)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 422

    email = data["email"].strip().lower()
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    user = User(
        name=data["name"].strip(),
        email=email,
        password_hash=hash_password(data["password"]),
        gender=data.get("gender"),
        ethnicity=data.get("ethnicity"),
        dietary_preference=data.get("dietary_preference"),
        cultural_food_preferences=data.get("cultural_food_preferences", []),
        activity_level=data.get("activity_level"),
        timezone=data.get("timezone", "Asia/Calcutta"),
        family_history_diabetes=bool(data.get("family_history_diabetes", False)),
    )

    db.session.add(user)
    db.session.flush()
    db.session.add(
        AuditLog(
            user_id=user.id,
            action="register",
            resource_type="user",
            resource_id=user.id,
            details={"email": email},
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent"),
        )
    )
    db.session.commit()

    return jsonify({"message": "Registration successful"}), 201


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not verify_password(password, user.password_hash):
        return jsonify({"error": "Invalid credentials"}), 401

    user.last_active = datetime.utcnow()
    db.session.add(
        AuditLog(
            user_id=user.id,
            action="login",
            resource_type="user",
            resource_id=user.id,
            details={"email": email},
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent"),
        )
    )
    db.session.commit()

    return jsonify({"token": generate_token(user.id), "user": user.to_dict()}), 200


@auth_bp.route("/auth/me", methods=["GET"])
@token_required
def me():
    return jsonify({"user": request.current_user.to_dict()}), 200


@auth_bp.route("/auth/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    
    if not email:
        return jsonify({"error": "Email is required"}), 400
    
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "Email not found"}), 404
    
    # Generate password reset token (simplified for demo)
    reset_token = f"reset_{user.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    # In a real application, you would send an email here
    # For demo purposes, we'll return the token directly
    return jsonify({
        "message": "Password reset token generated",
        "reset_token": reset_token,
        "note": "In production, this would be sent via email"
    }), 200


@auth_bp.route("/auth/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json() or {}
    token = data.get("token", "").strip()
    new_password = data.get("new_password", "").strip()
    
    if not token or not new_password:
        return jsonify({"error": "Token and new password are required"}), 400
    
    # Validate token format (simplified for demo)
    if not token.startswith("reset_"):
        return jsonify({"error": "Invalid token"}), 400
    
    # Extract user ID from token (simplified)
    try:
        user_id = int(token.split("_")[1].split("_")[0])
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "Invalid token"}), 400
        
        # Update password
        user.password_hash = hash_password(new_password)
        db.session.commit()
        
        return jsonify({"message": "Password reset successful"}), 200
        
    except (ValueError, IndexError):
        return jsonify({"error": "Invalid token"}), 400
