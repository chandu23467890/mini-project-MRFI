from datetime import datetime

from flask import Blueprint, jsonify, request

from middleware.auth import token_required
from models import AuditLog, Intervention, StabilityRecord, db
from services.recommendation_engine import RecommendationEngine
from services.ai_recommendations import ai_recommendation_engine

recommendations_bp = Blueprint("recommendations", __name__)


@recommendations_bp.route("/recommendations", methods=["GET"])
@token_required
def get_recommendations():
    user = request.current_user
    latest = StabilityRecord.query.filter_by(user_id=user.id).order_by(StabilityRecord.calculated_at.desc()).first()
    if not latest:
        return jsonify({"recommendations": [], "insufficient_data": True, "message": "Need at least 10 glucose measurements for personalized recommendations"}), 200

    existing = Intervention.query.filter(
        Intervention.user_id == user.id,
        Intervention.status.in_(["recommended", "accepted"]),
        Intervention.recommended_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
    ).order_by(Intervention.recommended_at.desc()).all()
    if existing:
        return jsonify({"recommendations": [i.to_dict() for i in existing]}), 200

    # Use traditional recommendations (AI temporarily disabled)
    generated = RecommendationEngine.generate_interventions(user, latest)
    interventions = []
    for item in generated:
        intervention = Intervention(
            user_id=user.id,
            recommendation_id=item.get("id"),
            title=item["title"],
            description=item.get("description"),
            actions=item["actions"],
            expected_improvement=item.get("expected_improvement"),
            expected_timeline_days=item.get("expected_timeline_days", 14),
            rationale="Ranked from metabolic component deficits, observed variability patterns, and user profile context.",
            warning_signs=item.get("warning_signs", []),
            status="recommended",
        )
        db.session.add(intervention)
        interventions.append(intervention)

    db.session.add(
        AuditLog(
            user_id=user.id,
            action="generate_recommendations",
            resource_type="intervention",
            details={"count": len(interventions)},
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent"),
        )
    )
    db.session.commit()
    return jsonify({"recommendations": [i.to_dict() for i in interventions]}), 200


@recommendations_bp.route("/recommendations/<int:intervention_id>/accept", methods=["POST"])
@token_required
def accept_recommendation(intervention_id):
    user = request.current_user
    intervention = Intervention.query.filter_by(id=intervention_id, user_id=user.id).first_or_404()
    intervention.status = "accepted"
    intervention.accepted_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"message": "Recommendation accepted", "intervention": intervention.to_dict()}), 200


@recommendations_bp.route("/recommendations/<int:intervention_id>/feedback", methods=["POST"])
@token_required
def submit_feedback(intervention_id):
    user = request.current_user
    data = request.get_json() or {}
    intervention = Intervention.query.filter_by(id=intervention_id, user_id=user.id).first_or_404()
    intervention.user_rating = data.get("rating")
    intervention.user_feedback = data.get("feedback")
    intervention.adherence_score = data.get("adherence_score")
    intervention.completed_at = datetime.utcnow()
    intervention.status = "completed"
    db.session.commit()
    return jsonify({"message": "Feedback submitted successfully"}), 200
