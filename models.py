from datetime import date, datetime, timedelta
from enum import Enum

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class MetabolicState(str, Enum):
    STABLE = "STABLE"
    PREDIABETIC_EARLY = "PREDIABETIC_EARLY"
    PREDIABETIC_LATE = "PREDIABETIC_LATE"
    DIABETIC = "DIABETIC"


class MeasurementType(str, Enum):
    FASTING_GLUCOSE = "fasting_glucose"
    POSTPRANDIAL_GLUCOSE = "postprandial_glucose"
    RANDOM_GLUCOSE = "random_glucose"
    HBA1C = "hba1c"
    INSULIN = "insulin"
    SYSTOLIC_BP = "systolic_bp"
    DIASTOLIC_BP = "diastolic_bp"
    WEIGHT = "weight"
    HEIGHT = "height"
    PHYSICAL_ACTIVITY = "physical_activity"
    SLEEP_HOURS = "sleep_hours"
    CALORIES_INTAKE = "calories_intake"
    CARBS_GRAMS = "carbs_grams"


class MealType(str, Enum):
    FASTING = "fasting"
    PRE_MEAL = "pre_meal"
    POST_MEAL_1H = "post_meal_1h"
    POST_MEAL_2H = "post_meal_2h"
    BEDTIME = "bedtime"


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(20))
    ethnicity = db.Column(db.String(50))
    timezone = db.Column(db.String(50), default="Asia/Calcutta")

    diabetes_diagnosis_date = db.Column(db.Date, nullable=True)
    family_history_diabetes = db.Column(db.Boolean, default=False)
    gestational_diabetes_history = db.Column(db.Boolean, default=False)
    hypertension_diagnosis = db.Column(db.Boolean, default=False)
    pregnancy_flag = db.Column(db.Boolean, default=False)
    is_type1_diabetes = db.Column(db.Boolean, default=False)
    medications = db.Column(db.JSON, default=list)
    comorbidities = db.Column(db.JSON, default=list)

    dietary_preference = db.Column(db.String(50))
    cultural_food_preferences = db.Column(db.JSON, default=list)
    activity_level = db.Column(db.String(20))
    sleep_schedule = db.Column(db.String(50))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    measurements = db.relationship("Measurement", backref="user", lazy="dynamic")
    stability_records = db.relationship("StabilityRecord", backref="user", lazy="dynamic")
    interventions = db.relationship("Intervention", backref="user", lazy="dynamic")

    def calculate_age(self):
        if not self.date_of_birth:
            return None
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "age": self.calculate_age(),
            "gender": self.gender,
            "ethnicity": self.ethnicity,
            "timezone": self.timezone,
            "family_history_diabetes": self.family_history_diabetes,
            "dietary_preference": self.dietary_preference,
            "activity_level": self.activity_level,
            "pregnancy_flag": self.pregnancy_flag,
            "is_type1_diabetes": self.is_type1_diabetes,
            "medications": self.medications or [],
            "comorbidities": self.comorbidities or [],
        }


class Measurement(db.Model):
    __tablename__ = "measurements"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    measurement_type = db.Column(db.Enum(MeasurementType), nullable=False)
    value = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    meal_context = db.Column(db.Enum(MealType), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    verification_status = db.Column(db.String(20), default="raw")
    verification_notes = db.Column(db.Text, nullable=True)
    is_anomaly = db.Column(db.Boolean, default=False)
    anomaly_severity = db.Column(db.String(20), nullable=True)
    source = db.Column(db.String(50), default="manual")
    device_id = db.Column(db.String(100), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)

    __table_args__ = (
        db.Index("idx_measurements_user_timestamp", "user_id", "timestamp"),
        db.Index("idx_measurements_type_timestamp", "measurement_type", "timestamp"),
    )

    def get_status(self):
        if self.is_anomaly and self.anomaly_severity == "HIGH":
            return "critical"
        if self.measurement_type == MeasurementType.FASTING_GLUCOSE:
            if self.value < 60 or self.value >= 126:
                return "critical"
            if self.value >= 100:
                return "warning"
            return "normal"
        if self.measurement_type == MeasurementType.POSTPRANDIAL_GLUCOSE:
            if self.value >= 180:
                return "critical"
            if self.value >= 140:
                return "warning"
            return "normal"
        if self.measurement_type == MeasurementType.HBA1C:
            if self.value >= 6.5:
                return "critical"
            if self.value >= 5.7:
                return "warning"
            return "normal"
        if self.measurement_type == MeasurementType.SYSTOLIC_BP:
            if self.value >= 140:
                return "critical"
            if self.value >= 120:
                return "warning"
            return "normal"
        if self.measurement_type == MeasurementType.DIASTOLIC_BP:
            if self.value >= 90:
                return "critical"
            if self.value >= 80:
                return "warning"
            return "normal"
        return "normal"

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.measurement_type.value,
            "value": self.value,
            "unit": self.unit,
            "meal_context": self.meal_context.value if self.meal_context else None,
            "timestamp": self.timestamp.isoformat(),
            "status": self.get_status(),
            "verification_status": self.verification_status,
            "verification_notes": self.verification_notes,
            "is_anomaly": self.is_anomaly,
            "anomaly_severity": self.anomaly_severity,
        }


class StabilityRecord(db.Model):
    __tablename__ = "stability_records"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    stability_score = db.Column(db.Float, nullable=False)
    metabolic_state = db.Column(db.Enum(MetabolicState), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    glucose_control_score = db.Column(db.Float)
    trend_stability_score = db.Column(db.Float)
    insulin_sensitivity_score = db.Column(db.Float)
    lifestyle_score = db.Column(db.Float)
    avg_glucose = db.Column(db.Float)
    glucose_variability = db.Column(db.Float)
    homa_ir = db.Column(db.Float)
    trend_slope = db.Column(db.Float)
    lower_bound_80 = db.Column(db.Float)
    upper_bound_80 = db.Column(db.Float)
    lower_bound_95 = db.Column(db.Float)
    upper_bound_95 = db.Column(db.Float)
    measurements_used = db.Column(db.Integer, default=0)
    data_quality_score = db.Column(db.Float)
    evidence = db.Column(db.JSON, default=dict)
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)
    valid_until = db.Column(
        db.DateTime, default=lambda: datetime.utcnow() + timedelta(days=7)
    )

    __table_args__ = (db.Index("idx_stability_user_date", "user_id", "calculated_at"),)

    def to_dict(self):
        return {
            "id": self.id,
            "stability_score": round(self.stability_score, 1),
            "metabolic_state": self.metabolic_state.value,
            "confidence": round(self.confidence, 1),
            "components": {
                "glucose_control": round(self.glucose_control_score or 0, 1),
                "trend_stability": round(self.trend_stability_score or 0, 1),
                "insulin_sensitivity": round(self.insulin_sensitivity_score or 0, 1),
                "lifestyle": round(self.lifestyle_score or 0, 1),
            },
            "metrics": {
                "avg_glucose": self.avg_glucose,
                "glucose_variability": self.glucose_variability,
                "homa_ir": self.homa_ir,
                "trend_slope": self.trend_slope,
            },
            "confidence_intervals": {
                "80": {"lower": self.lower_bound_80, "upper": self.upper_bound_80},
                "95": {"lower": self.lower_bound_95, "upper": self.upper_bound_95},
            },
            "evidence": self.evidence or {},
            "measurements_used": self.measurements_used,
            "data_quality_score": self.data_quality_score,
            "calculated_at": self.calculated_at.isoformat(),
            "valid_until": self.valid_until.isoformat(),
        }


class PredictionRecord(db.Model):
    __tablename__ = "predictions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    prediction_date = db.Column(db.DateTime, default=datetime.utcnow)
    horizon_days = db.Column(db.Integer, nullable=False)
    predicted_stability_score = db.Column(db.Float)
    predicted_state = db.Column(db.Enum(MetabolicState))
    diabetes_risk = db.Column(db.String(20))
    lower_bound_80 = db.Column(db.Float)
    upper_bound_80 = db.Column(db.Float)
    lower_bound_95 = db.Column(db.Float)
    upper_bound_95 = db.Column(db.Float)
    model_version = db.Column(db.String(50))
    features_used = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "prediction_date": self.prediction_date.isoformat(),
            "horizon_days": self.horizon_days,
            "predicted_stability_score": self.predicted_stability_score,
            "predicted_state": self.predicted_state.value if self.predicted_state else None,
            "diabetes_risk": self.diabetes_risk,
            "confidence_intervals": {
                "80": {"lower": self.lower_bound_80, "upper": self.upper_bound_80},
                "95": {"lower": self.lower_bound_95, "upper": self.upper_bound_95},
            },
        }


class Intervention(db.Model):
    __tablename__ = "interventions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    recommendation_id = db.Column(db.String(100))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    actions = db.Column(db.JSON, nullable=False)
    expected_improvement = db.Column(db.String(200))
    expected_timeline_days = db.Column(db.Integer)
    status = db.Column(db.String(20), default="recommended")
    adherence_score = db.Column(db.Float, nullable=True)
    rationale = db.Column(db.Text, nullable=True)
    warning_signs = db.Column(db.JSON, default=list)
    recommended_at = db.Column(db.DateTime, default=datetime.utcnow)
    accepted_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    user_rating = db.Column(db.Integer, nullable=True)
    user_feedback = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "actions": self.actions,
            "expected_improvement": self.expected_improvement,
            "expected_timeline_days": self.expected_timeline_days,
            "status": self.status,
            "adherence_score": self.adherence_score,
            "rationale": self.rationale,
            "warning_signs": self.warning_signs or [],
            "recommended_at": self.recommended_at.isoformat(),
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
        }


class Alert(db.Model):
    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    measurement_id = db.Column(db.Integer, db.ForeignKey("measurements.id"), nullable=True)
    recommendation = db.Column(db.Text, nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    is_acknowledged = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(
        db.DateTime, default=lambda: datetime.utcnow() + timedelta(days=7)
    )

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.alert_type,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "recommendation": self.recommendation,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat(),
        }


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50))
    resource_id = db.Column(db.Integer)
    details = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.Index("idx_audit_user_time", "user_id", "created_at"),
        db.Index("idx_audit_resource", "resource_type", "resource_id"),
    )
