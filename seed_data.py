from datetime import datetime, timedelta

from middleware.auth import hash_password
from models import MealType, Measurement, MeasurementType, MetabolicState, StabilityRecord, User, db
from run import create_app
from services.stability_engine import MetabolicStabilityEngine


def add_measurement(user_id, measurement_type, value, timestamp, unit, meal_context=None, source="seed"):
    db.session.add(
        Measurement(
            user_id=user_id,
            measurement_type=measurement_type,
            value=value,
            unit=unit,
            meal_context=meal_context,
            timestamp=timestamp,
            source=source,
            verification_status="verified",
        )
    )


def seed_user(profile):
    existing = User.query.filter_by(email=profile["email"]).first()
    if existing:
        return existing

    user = User(
        name=profile["name"],
        email=profile["email"],
        password_hash=hash_password(profile["password"]),
        ethnicity=profile["ethnicity"],
        dietary_preference=profile["dietary_preference"],
        activity_level=profile["activity_level"],
        family_history_diabetes=profile["family_history_diabetes"],
        timezone="Asia/Calcutta",
    )
    db.session.add(user)
    db.session.flush()
    return user


def seed_measurement_history(user, profile):
    now = datetime.utcnow().replace(hour=6, minute=30, second=0, microsecond=0)
    for day_offset in range(84, -1, -3):
        ts = now - timedelta(days=day_offset)
        progress = (84 - day_offset) / 84

        fasting = round(profile["fasting_start"] + (profile["fasting_end"] - profile["fasting_start"]) * progress, 1)
        post_meal = round(profile["post_meal_start"] + (profile["post_meal_end"] - profile["post_meal_start"]) * progress, 1)
        insulin = round(profile["insulin_start"] + (profile["insulin_end"] - profile["insulin_start"]) * progress, 1)
        weight = round(profile["weight_start"] + (profile["weight_end"] - profile["weight_start"]) * progress, 1)
        activity = round(profile["activity_start"] + (profile["activity_end"] - profile["activity_start"]) * progress, 1)
        sleep = round(profile["sleep_start"] + (profile["sleep_end"] - profile["sleep_start"]) * progress, 1)
        carbs = round(profile["carbs_start"] + (profile["carbs_end"] - profile["carbs_start"]) * progress, 1)

        add_measurement(user.id, MeasurementType.FASTING_GLUCOSE, fasting, ts, "mg/dL", MealType.FASTING)
        add_measurement(user.id, MeasurementType.POSTPRANDIAL_GLUCOSE, post_meal, ts + timedelta(hours=2), "mg/dL", MealType.POST_MEAL_2H)
        add_measurement(user.id, MeasurementType.INSULIN, insulin, ts + timedelta(minutes=10), "uU/mL", MealType.FASTING)
        add_measurement(user.id, MeasurementType.WEIGHT, weight, ts + timedelta(hours=1), "kg")
        add_measurement(user.id, MeasurementType.PHYSICAL_ACTIVITY, activity, ts + timedelta(hours=12), "minutes")
        add_measurement(user.id, MeasurementType.SLEEP_HOURS, sleep, ts + timedelta(hours=13), "hours")
        add_measurement(user.id, MeasurementType.CARBS_GRAMS, carbs, ts + timedelta(hours=8), "g", MealType.POST_MEAL_2H)

    add_measurement(user.id, MeasurementType.HBA1C, profile["hba1c"], now - timedelta(days=2), "%")


def seed_stability_history(user, trajectory_scores):
    base_time = datetime.utcnow() - timedelta(days=35)
    state_for_score = (
        lambda score: MetabolicState.STABLE
        if score >= 80
        else MetabolicState.PREDIABETIC_EARLY
        if score >= 50
        else MetabolicState.PREDIABETIC_LATE
        if score >= 30
        else MetabolicState.DIABETIC
    )

    for index, score in enumerate(trajectory_scores):
        record = StabilityRecord(
            user_id=user.id,
            stability_score=score,
            metabolic_state=state_for_score(score),
            confidence=82,
            glucose_control_score=round(score * 0.4, 1),
            trend_stability_score=round(score * 0.25, 1),
            insulin_sensitivity_score=round(score * 0.2, 1),
            lifestyle_score=round(score * 0.15, 1),
            avg_glucose=95 + max(0, 85 - score),
            glucose_variability=12 + index,
            homa_ir=1.4 + (85 - score) / 20,
            trend_slope=-1.5 if index and score < trajectory_scores[index - 1] else 0.8,
            lower_bound_80=max(0, score - 8),
            upper_bound_80=min(100, score + 8),
            lower_bound_95=max(0, score - 14),
            upper_bound_95=min(100, score + 14),
            measurements_used=24,
            data_quality_score=78,
            evidence={"seeded": True},
            calculated_at=base_time + timedelta(days=index * 7),
            valid_until=base_time + timedelta(days=index * 7 + 7),
        )
        db.session.add(record)


def main():
    app = create_app()
    with app.app_context():
        db.create_all()

        profiles = [
            {
                "name": "Asha Stable",
                "email": "stable@example.com",
                "password": "Password123!",
                "ethnicity": "South Asian",
                "dietary_preference": "vegetarian",
                "activity_level": "moderate",
                "family_history_diabetes": False,
                "fasting_start": 88,
                "fasting_end": 92,
                "post_meal_start": 118,
                "post_meal_end": 126,
                "insulin_start": 6.5,
                "insulin_end": 7.2,
                "weight_start": 62,
                "weight_end": 62.5,
                "activity_start": 42,
                "activity_end": 48,
                "sleep_start": 7.3,
                "sleep_end": 7.1,
                "carbs_start": 38,
                "carbs_end": 41,
                "hba1c": 5.4,
                "trajectory_scores": [87, 86, 88, 85, 86],
            },
            {
                "name": "Rohan Drift",
                "email": "early@example.com",
                "password": "Password123!",
                "ethnicity": "South Asian",
                "dietary_preference": "omnivore",
                "activity_level": "light",
                "family_history_diabetes": True,
                "fasting_start": 96,
                "fasting_end": 109,
                "post_meal_start": 132,
                "post_meal_end": 156,
                "insulin_start": 10,
                "insulin_end": 14,
                "weight_start": 76,
                "weight_end": 80,
                "activity_start": 24,
                "activity_end": 18,
                "sleep_start": 7.0,
                "sleep_end": 6.4,
                "carbs_start": 50,
                "carbs_end": 61,
                "hba1c": 5.9,
                "trajectory_scores": [74, 69, 66, 61, 57],
            },
            {
                "name": "Meera Late",
                "email": "late@example.com",
                "password": "Password123!",
                "ethnicity": "South Asian",
                "dietary_preference": "omnivore",
                "activity_level": "sedentary",
                "family_history_diabetes": True,
                "fasting_start": 112,
                "fasting_end": 124,
                "post_meal_start": 158,
                "post_meal_end": 188,
                "insulin_start": 16,
                "insulin_end": 22,
                "weight_start": 84,
                "weight_end": 89,
                "activity_start": 16,
                "activity_end": 8,
                "sleep_start": 6.5,
                "sleep_end": 5.8,
                "carbs_start": 62,
                "carbs_end": 76,
                "hba1c": 6.3,
                "trajectory_scores": [53, 49, 44, 39, 34],
            },
        ]

        for profile in profiles:
            user = seed_user(profile)
            if user.measurements.count() == 0:
                seed_measurement_history(user, profile)
                seed_stability_history(user, profile["trajectory_scores"])

        db.session.commit()

        for profile in profiles:
            user = User.query.filter_by(email=profile["email"]).first()
            try:
                MetabolicStabilityEngine.calculate_stability_score(user.id)
                MetabolicStabilityEngine.predict_trajectory(user.id)
                db.session.commit()
            except Exception:
                db.session.rollback()
                raise

        print("Seeded demo users:")
        for profile in profiles:
            print(f"- {profile['email']} / {profile['password']}")


if __name__ == "__main__":
    main()
