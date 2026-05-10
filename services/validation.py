from datetime import datetime, timedelta, timezone

from models import Measurement, MeasurementType

PHYSIOLOGICAL_RANGES = {
    MeasurementType.FASTING_GLUCOSE: (40, 500, "mg/dL"),
    MeasurementType.POSTPRANDIAL_GLUCOSE: (40, 600, "mg/dL"),
    MeasurementType.RANDOM_GLUCOSE: (40, 600, "mg/dL"),
    MeasurementType.HBA1C: (4.0, 15.0, "%"),
    MeasurementType.INSULIN: (1, 100, "uU/mL"),
    MeasurementType.SYSTOLIC_BP: (60, 250, "mmHg"),
    MeasurementType.DIASTOLIC_BP: (30, 150, "mmHg"),
    MeasurementType.WEIGHT: (20, 300, "kg"),
    MeasurementType.HEIGHT: (100, 250, "cm"),
    MeasurementType.PHYSICAL_ACTIVITY: (0, 1000, "minutes"),
    MeasurementType.SLEEP_HOURS: (0, 24, "hours"),
    MeasurementType.CALORIES_INTAKE: (0, 10000, "kcal"),
    MeasurementType.CARBS_GRAMS: (0, 1000, "g"),
}


def default_unit_for(measurement_type):
    range_def = PHYSIOLOGICAL_RANGES.get(measurement_type)
    return range_def[2] if range_def else "unit"


def parse_iso_timestamp(raw_value):
    if not raw_value:
        raise ValueError("Timestamp is required")
    normalized = raw_value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(tzinfo=None)


def validate_measurement_value(measurement_type, value):
    if measurement_type not in PHYSIOLOGICAL_RANGES:
        return True, None
    min_val, max_val, _ = PHYSIOLOGICAL_RANGES[measurement_type]
    if value < min_val or value > max_val:
        return False, f"Value {value} outside physiological range ({min_val}-{max_val})"
    return True, None


def validate_measurement_timing(user_id, timestamp):
    now = datetime.utcnow()
    if timestamp > now + timedelta(minutes=10):
        return False, "Cannot log future measurements"
    if timestamp < now - timedelta(days=30):
        return False, "Measurements older than 30 days are not accepted"
    duplicate = Measurement.query.filter_by(user_id=user_id, timestamp=timestamp).first()
    if duplicate:
        return False, "Measurement already recorded for this time"
    return True, "OK"


def bmi_from_height_weight(height_cm, weight_kg):
    if not height_cm or not weight_kg:
        return None
    height_m = height_cm / 100
    if height_m <= 0:
        return None
    return round(weight_kg / (height_m * height_m), 1)
