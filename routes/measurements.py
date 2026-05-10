from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

from middleware.auth import token_required
from models import Alert, AuditLog, MealType, Measurement, MeasurementType, StabilityRecord, db
from services.image_processor import ImageProcessor
from services.stability_engine import MetabolicStabilityEngine
from services.validation import default_unit_for, parse_iso_timestamp, validate_measurement_timing, validate_measurement_value

measurements_bp = Blueprint("measurements", __name__)


@measurements_bp.route("/measurements", methods=["POST"])
@token_required
def add_measurement():
    user = request.current_user
    data = request.get_json() or {}
    for field in ["measurement_type", "value", "timestamp"]:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 422

    try:
        measurement_type = MeasurementType(data["measurement_type"])
        value = float(data["value"])
        timestamp = parse_iso_timestamp(data["timestamp"])
        meal_context = MealType(data["meal_context"]) if data.get("meal_context") else None
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 422

    is_valid, message = validate_measurement_value(measurement_type, value)
    if not is_valid:
        return jsonify({"error": message}), 422
    is_valid, message = validate_measurement_timing(user.id, timestamp)
    if not is_valid:
        return jsonify({"error": message}), 422

    recent_history = Measurement.query.filter_by(user_id=user.id).order_by(Measurement.timestamp.asc()).all()

    try:
        measurement = Measurement(
            user_id=user.id,
            measurement_type=measurement_type,
            value=value,
            unit=data.get("unit") or default_unit_for(measurement_type),
            meal_context=meal_context,
            timestamp=timestamp,
            source=data.get("source", "manual"),
            device_id=data.get("device_id"),
            ip_address=request.remote_addr,
            verification_status="raw",
        )

        is_anomaly, severity, reason = MetabolicStabilityEngine.detect_anomaly(measurement, recent_history)
        if is_anomaly:
            measurement.is_anomaly = True
            measurement.anomaly_severity = severity
            measurement.verification_status = "anomalous"
            measurement.verification_notes = reason

        db.session.add(measurement)
        db.session.flush()

        if is_anomaly:
            db.session.add(
                Alert(
                    user_id=user.id,
                    alert_type="anomaly",
                    severity=severity,
                    title=f"Unusual {measurement_type.value.replace('_', ' ')} reading",
                    message=reason,
                    measurement_id=measurement.id,
                    recommendation="Verify the reading and seek medical advice if symptoms are present.",
                )
            )

        db.session.add(
            AuditLog(
                user_id=user.id,
                action="create_measurement",
                resource_type="measurement",
                resource_id=measurement.id,
                details={
                    "measurement_type": measurement_type.value,
                    "value": value,
                    "timestamp": timestamp.isoformat(),
                    "is_anomaly": is_anomaly,
                },
                ip_address=request.remote_addr,
                user_agent=request.headers.get("User-Agent"),
            )
        )

        stability_payload = None
        prediction_payload = None
        stable_points = MetabolicStabilityEngine._glucose_measurements(user.id, 90)
        if len(stable_points) >= 10:
            record = MetabolicStabilityEngine.calculate_stability_score(user.id)
            stability_payload = record.to_dict()
            prediction_payload = MetabolicStabilityEngine.predict_trajectory(user.id)

        db.session.commit()

        if stability_payload:
            latest_alerts = [a.to_dict() for a in Alert.query.filter_by(user_id=user.id, is_read=False).order_by(Alert.created_at.desc()).limit(5).all()]
            MetabolicStabilityEngine.publish_snapshot(user.id, stability_payload, None if "error" in (prediction_payload or {}) else prediction_payload, latest_alerts)

        return jsonify({"measurement": measurement.to_dict(), "is_anomaly": is_anomaly, "anomaly_message": reason if is_anomaly else None}), 201
    except Exception:
        db.session.rollback()
        raise


@measurements_bp.route("/measurements", methods=["GET"])
@token_required
def get_measurements():
    user = request.current_user
    days = int(request.args.get("days", 30))
    if days < 1 or days > 365:
        return jsonify({"error": "days must be between 1 and 365"}), 422
    include_anomalies = request.args.get("include_anomalies", "false").lower() == "true"
    measurement_type = request.args.get("type")
    cutoff = datetime.utcnow() - timedelta(days=days)

    query = Measurement.query.filter(Measurement.user_id == user.id, Measurement.timestamp >= cutoff)
    if measurement_type:
        try:
            query = query.filter_by(measurement_type=MeasurementType(measurement_type))
        except ValueError:
            return jsonify({"error": "Invalid measurement type"}), 422
    if not include_anomalies:
        query = query.filter(Measurement.is_anomaly.is_(False))
    rows = query.order_by(Measurement.timestamp.desc()).all()
    return jsonify([row.to_dict() for row in rows]), 200


@measurements_bp.route("/measurements/stability", methods=["GET"])
@token_required
def get_stability_report():
    user = request.current_user
    latest = StabilityRecord.query.filter_by(user_id=user.id).order_by(StabilityRecord.calculated_at.desc()).first()
    if not latest or (datetime.utcnow() - latest.calculated_at) >= timedelta(days=1):
        try:
            latest = MetabolicStabilityEngine.calculate_stability_score(user.id)
            db.session.commit()
        except ValueError as exc:
            db.session.rollback()
            data_quality = MetabolicStabilityEngine.calculate_data_quality(user.id)
            alerts = Alert.query.filter_by(user_id=user.id, is_read=False).order_by(Alert.created_at.desc()).limit(5).all()
            return jsonify({
                "stability": None,
                "prediction": {"error": "insufficient_data", "message": str(exc)},
                "alerts": [alert.to_dict() for alert in alerts],
                "data_quality": data_quality,
                "insufficient_data": True,
                "message": f"Need at least 10 glucose measurements in the last 90 days for stability analysis. Currently have {len(MetabolicStabilityEngine._glucose_measurements(user.id, 90))} measurements."
            }), 200

    prediction = MetabolicStabilityEngine.predict_trajectory(user.id)
    db.session.commit()
    alerts = Alert.query.filter_by(user_id=user.id, is_read=False).order_by(Alert.created_at.desc()).limit(5).all()
    return jsonify({"stability": latest.to_dict() if hasattr(latest, "to_dict") else latest, "prediction": None if "error" in prediction else prediction, "alerts": [alert.to_dict() for alert in alerts], "data_quality": MetabolicStabilityEngine.calculate_data_quality(user.id)}), 200


@measurements_bp.route("/measurements/stability/history", methods=["GET"])
@token_required
def get_stability_history():
    user = request.current_user
    history = StabilityRecord.query.filter_by(user_id=user.id).order_by(StabilityRecord.calculated_at.asc()).all()
    return jsonify([item.to_dict() for item in history]), 200


@measurements_bp.route("/measurements/food-log", methods=["POST"])
@token_required
def log_meal():
    user = request.current_user
    timestamp = parse_iso_timestamp(request.form.get("timestamp") or datetime.utcnow().isoformat())
    carbs_estimate = request.form.get("carbs_grams", type=float)
    analysis = None

    if "image" in request.files and request.files["image"].filename:
        uploaded = request.files["image"]
        if not (uploaded.mimetype or "").startswith("image/"):
            return jsonify({"error": "Meal upload must be an image"}), 422
        analysis = ImageProcessor.analyze_food_image(uploaded)
        if carbs_estimate is None:
            carbs_estimate = analysis["estimated_carbs_grams"]

    if carbs_estimate is None:
        carbs_estimate = 0

    measurement = Measurement(
        user_id=user.id,
        measurement_type=MeasurementType.CARBS_GRAMS,
        value=carbs_estimate,
        unit="g",
        meal_context=MealType(request.form.get("meal_type", "post_meal_2h")),
        timestamp=timestamp,
        source="food_log",
        verification_status="raw",
        verification_notes=analysis["analysis_notes"] if analysis else None,
    )
    db.session.add(measurement)
    db.session.add(
        AuditLog(
            user_id=user.id,
            action="log_meal",
            resource_type="measurement",
            details={"carbs_grams": carbs_estimate, "analysis": analysis},
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent"),
        )
    )
    db.session.commit()
    return jsonify({"message": "Meal logged successfully", "measurement": measurement.to_dict(), "nutritional_estimate": analysis}), 201
