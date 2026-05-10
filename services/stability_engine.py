from datetime import datetime, timedelta

import numpy as np
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_squared_error, r2_score
import warnings
warnings.filterwarnings('ignore')

from models import Alert, AuditLog, Measurement, MeasurementType, MetabolicState, PredictionRecord, StabilityRecord, User, db
from services.websocket_hub import websocket_hub


class MetabolicStabilityEngine:
    @staticmethod
    def _glucose_measurements(user_id, days=90):
        cutoff = datetime.utcnow() - timedelta(days=days)
        return (
            Measurement.query.filter(
                Measurement.user_id == user_id,
                Measurement.timestamp >= cutoff,
                Measurement.is_anomaly.is_(False),
                Measurement.measurement_type.in_(
                    [
                        MeasurementType.FASTING_GLUCOSE,
                        MeasurementType.POSTPRANDIAL_GLUCOSE,
                        MeasurementType.RANDOM_GLUCOSE,
                    ]
                ),
            )
            .order_by(Measurement.timestamp.asc())
            .all()
        )

    @staticmethod
    def calculate_data_quality(user_id):
        cutoff = datetime.utcnow() - timedelta(days=90)
        measurements = (
            Measurement.query.filter(
                Measurement.user_id == user_id,
                Measurement.timestamp >= cutoff,
                Measurement.is_anomaly.is_(False),
            )
            .order_by(Measurement.timestamp.asc())
            .all()
        )
        if not measurements:
            return {"score": 0, "grade": "INSUFFICIENT", "recommendation": "Start logging data"}

        last_30 = [m for m in measurements if m.timestamp >= datetime.utcnow() - timedelta(days=30)]
        recency_score = min(50, len(last_30) * 3.33)
        unique_days = sorted({m.timestamp.date() for m in measurements})
        consistency_score = min(30, (len(unique_days) / 30) * 30)
        tracked_fields = len({m.measurement_type for m in last_30}) if last_30 else 0
        completeness_score = min(20, tracked_fields * 3)
        total = round(recency_score * 0.5 + consistency_score * 0.3 + completeness_score * 0.2, 1)
        grade = "EXCELLENT" if total > 80 else "GOOD" if total > 60 else "FAIR" if total > 40 else "INSUFFICIENT"
        return {"score": total, "grade": grade, "recommendation": "Increase logging frequency" if total < 60 else None}

    @staticmethod
    def _calculate_lifestyle_score(user_id):
        cutoff = datetime.utcnow() - timedelta(days=30)
        measurements = (
            Measurement.query.filter(
                Measurement.user_id == user_id,
                Measurement.timestamp >= cutoff,
                Measurement.measurement_type.in_(
                    [MeasurementType.PHYSICAL_ACTIVITY, MeasurementType.SLEEP_HOURS, MeasurementType.CARBS_GRAMS]
                ),
            )
            .all()
        )
        if not measurements:
            return 7.5

        activity_values = [m.value for m in measurements if m.measurement_type == MeasurementType.PHYSICAL_ACTIVITY]
        sleep_values = [m.value for m in measurements if m.measurement_type == MeasurementType.SLEEP_HOURS]
        carb_entries = [m for m in measurements if m.measurement_type == MeasurementType.CARBS_GRAMS]

        activity_score = 6 if activity_values and np.mean(activity_values) >= 30 else 4 if activity_values and np.mean(activity_values) >= 15 else 2 if activity_values else 3
        sleep_score = 4.5 if sleep_values and 7 <= np.mean(sleep_values) <= 9 else 3 if sleep_values and 6 <= np.mean(sleep_values) <= 10 else 1.5 if sleep_values else 2.25
        meal_score = min(4.5, (len({m.timestamp.date() for m in carb_entries}) / 14) * 4.5) if carb_entries else 2.0
        return round(activity_score + sleep_score + meal_score, 1)

    @staticmethod
    def _calculate_homa_ir(user_id):
        cutoff = datetime.utcnow() - timedelta(days=90)
        fasting_glucose = (
            Measurement.query.filter(
                Measurement.user_id == user_id,
                Measurement.timestamp >= cutoff,
                Measurement.measurement_type == MeasurementType.FASTING_GLUCOSE,
            )
            .order_by(Measurement.timestamp.asc())
            .all()
        )
        insulin = (
            Measurement.query.filter(
                Measurement.user_id == user_id,
                Measurement.timestamp >= cutoff,
                Measurement.measurement_type == MeasurementType.INSULIN,
            )
            .order_by(Measurement.timestamp.asc())
            .all()
        )
        if not fasting_glucose or not insulin:
            return None
        return round((np.median([m.value for m in fasting_glucose[-5:]]) * np.median([m.value for m in insulin[-5:]])) / 405, 2)

    @staticmethod
    def _state_from_clinical_rules(user, avg_fasting_glucose, latest_hba1c, homa_ir, score):
        risk_adjustment = 5 if (user.ethnicity or "").lower() in {"south asian", "asian indian"} else 0
        if latest_hba1c is not None and latest_hba1c >= 6.5:
            return MetabolicState.DIABETIC
        if avg_fasting_glucose is not None and avg_fasting_glucose >= 126:
            return MetabolicState.DIABETIC
        if homa_ir is not None and homa_ir > 4.0:
            return MetabolicState.DIABETIC
        if latest_hba1c is not None and 6.1 <= latest_hba1c <= 6.4:
            return MetabolicState.PREDIABETIC_LATE
        if avg_fasting_glucose is not None and avg_fasting_glucose >= 116 - risk_adjustment:
            return MetabolicState.PREDIABETIC_LATE
        if homa_ir is not None and homa_ir >= 2.5:
            return MetabolicState.PREDIABETIC_LATE if score < 50 else MetabolicState.PREDIABETIC_EARLY
        if latest_hba1c is not None and 5.7 <= latest_hba1c <= 6.0:
            return MetabolicState.PREDIABETIC_EARLY
        if avg_fasting_glucose is not None and avg_fasting_glucose >= 100 - risk_adjustment:
            return MetabolicState.PREDIABETIC_EARLY
        if score >= 80:
            return MetabolicState.STABLE
        if score >= 50:
            return MetabolicState.PREDIABETIC_EARLY
        if score >= 30:
            return MetabolicState.PREDIABETIC_LATE
        return MetabolicState.DIABETIC

    @staticmethod
    def _advanced_ai_stability_prediction(user_id, measurements):
        """Advanced AI prediction using ensemble of ML models"""
        try:
            # Prepare features for AI models
            glucose_values = np.array([m.value for m in measurements])
            timestamps = np.array([(m.timestamp - measurements[0].timestamp).total_seconds() / 86400 for m in measurements])
            
            # Create feature matrix
            features = np.column_stack([
                timestamps,
                glucose_values,
                np.roll(glucose_values, 1),  # Previous value
                np.roll(glucose_values, 2),  # Two values back
                np.convolve(glucose_values, np.ones(3)/3, mode='same'),  # Moving average
                np.gradient(glucose_values)  # Rate of change
            ])
            
            # Remove NaN values from rolling
            features = features[2:]
            y = glucose_values[2:]
            
            if len(features) < 5:
                return None, None, None
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(features)
            
            # Ensemble of AI models
            models = {
                'linear': LinearRegression(),
                'ridge': Ridge(alpha=1.0),
                'lasso': Lasso(alpha=0.1),
                'random_forest': RandomForestRegressor(n_estimators=50, random_state=42),
                'gradient_boost': GradientBoostingRegressor(n_estimators=50, random_state=42),
                'svr': SVR(kernel='rbf', C=1.0)
            }
            
            # Train and evaluate models
            model_scores = {}
            predictions = {}
            
            for name, model in models.items():
                try:
                    # Cross-validation
                    cv_scores = cross_val_score(model, X_scaled, y, cv=3, scoring='r2')
                    model_scores[name] = np.mean(cv_scores)
                    
                    # Train on full data
                    model.fit(X_scaled, y)
                    predictions[name] = model.predict(X_scaled[-1:])  # Predict next value
                except:
                    model_scores[name] = -1
                    predictions[name] = y[-1]  # Fallback to last value
            
            # Select best performing model
            best_model = max(model_scores, key=model_scores.get)
            best_score = model_scores[best_model]
            
            # Predict future values (30 days)
            future_predictions = []
            last_features = X_scaled[-1:].copy()
            
            for _ in range(30):
                next_pred = models[best_model].predict(last_features)[0]
                future_predictions.append(next_pred)
                
                # Update features for next prediction
                last_features = np.roll(last_features, -1)
                last_features[0, -1] = next_pred  # Update rate of change
            
            return future_predictions, best_model, best_score
            
        except Exception as e:
            print(f"AI prediction error: {e}")
            return None, None, None

    @staticmethod
    def calculate_stability_score(user_id):
        user = User.query.get(user_id)
        measurements = MetabolicStabilityEngine._glucose_measurements(user_id, 90)
        if len(measurements) < 10:
            raise ValueError(f"Need at least 10 measurements in the last 90 days; found {len(measurements)}")

        glucose_values = np.array([m.value for m in measurements])
        avg_glucose = float(np.mean(glucose_values))
        variability_sd = float(np.std(glucose_values)) if len(glucose_values) > 1 else 0.0
        variability_cv = float((variability_sd / avg_glucose) * 100) if avg_glucose else 0.0

        if avg_glucose < 70:
            glucose_score = 0
        elif avg_glucose > 140:
            glucose_score = max(0, 40 - ((avg_glucose - 140) / 2))
        else:
            glucose_score = 40 - (abs(avg_glucose - 100) / 100) * 10
        glucose_score = round(max(0, min(40, glucose_score)), 1)

        # Enhanced AI-based trend analysis
        x = np.array([(m.timestamp - measurements[0].timestamp).total_seconds() / 86400 for m in measurements]).reshape(-1, 1)
        
        # Temporarily disable AI to fix data format issues
        # Use linear regression for now
        model = LinearRegression().fit(x, glucose_values)
        slope_month = float(model.coef_[0]) * 30
        trend_score = round(25 * (1 - min(1, abs(slope_month) / 10)), 1)
        
        # AI prediction disabled temporarily
        # future_preds, best_model, ai_score = MetabolicStabilityEngine._advanced_ai_stability_prediction(user_id, measurements)
        # if future_preds and ai_score > 0.3:  # Use AI if it's reasonably good
        #     # Calculate trend from AI predictions
        #     ai_trend = np.mean(future_preds[-10:]) - np.mean(future_preds[:10])
        #     slope_month = ai_trend / 30
        #     trend_score = round(25 * (1 - min(1, abs(slope_month) / 10)), 1)

        homa_ir = MetabolicStabilityEngine._calculate_homa_ir(user_id)
        if homa_ir is None:
            insulin_score = 10
        elif homa_ir <= 1.5:
            insulin_score = 20
        elif homa_ir <= 2.5:
            insulin_score = 15
        elif homa_ir <= 4.0:
            insulin_score = 10
        else:
            insulin_score = max(0, 20 - (homa_ir - 4.0) * 2)
        insulin_score = round(insulin_score, 1)

        lifestyle_score = MetabolicStabilityEngine._calculate_lifestyle_score(user_id)
        total_score = round(max(0, min(100, glucose_score + trend_score + insulin_score + lifestyle_score)), 1)

        latest_hba1c_row = (
            Measurement.query.filter_by(user_id=user_id, measurement_type=MeasurementType.HBA1C)
            .order_by(Measurement.timestamp.desc())
            .first()
        )
        latest_hba1c = latest_hba1c_row.value if latest_hba1c_row else None
        fasting = [m.value for m in measurements if m.measurement_type == MeasurementType.FASTING_GLUCOSE]
        avg_fasting_glucose = round(float(np.mean(fasting)), 1) if fasting else None
        data_quality = MetabolicStabilityEngine.calculate_data_quality(user_id)
        confidence = round(min(95, 50 + len(measurements) * 4) * (data_quality["score"] / 100), 1)
        confidence = max(50, min(95, confidence))
        interval_80 = max(6, round(18 - (confidence / 10), 1))
        interval_95 = max(10, round(interval_80 * 1.65, 1))

        drift_detected = False
        drift_reason = None
        if len(fasting) >= 3 and np.mean(fasting[-3:]) > 95:
            drift_detected = True
            drift_reason = "Recent fasting readings exceed baseline and suggest metabolic drift."

        metabolic_state = MetabolicStabilityEngine._state_from_clinical_rules(user, avg_fasting_glucose, latest_hba1c, homa_ir, total_score)
        record = (
            StabilityRecord.query.filter(
                StabilityRecord.user_id == user_id,
                StabilityRecord.calculated_at >= datetime.utcnow() - timedelta(hours=6),
            )
            .order_by(StabilityRecord.calculated_at.desc())
            .first()
        )
        if record:
            record.stability_score = total_score
            record.metabolic_state = metabolic_state
            record.confidence = confidence
            record.glucose_control_score = glucose_score
            record.trend_stability_score = trend_score
            record.insulin_sensitivity_score = insulin_score
            record.lifestyle_score = lifestyle_score
            record.avg_glucose = round(avg_glucose, 1)
            record.glucose_variability = round(variability_cv, 1)
            record.homa_ir = homa_ir
            record.trend_slope = round(slope_month, 2)
            record.lower_bound_80 = max(0, round(total_score - interval_80, 1))
            record.upper_bound_80 = min(100, round(total_score + interval_80, 1))
            record.lower_bound_95 = max(0, round(total_score - interval_95, 1))
            record.upper_bound_95 = min(100, round(total_score + interval_95, 1))
            record.measurements_used = len(measurements)
            record.data_quality_score = data_quality["score"]
            record.evidence = {
                "drift_detected": drift_detected,
                "drift_reason": drift_reason,
                "avg_fasting_glucose": avg_fasting_glucose,
                "latest_hba1c": latest_hba1c,
            }
        else:
            record = StabilityRecord(
                user_id=user_id,
                stability_score=total_score,
                metabolic_state=metabolic_state,
                confidence=confidence,
                glucose_control_score=glucose_score,
                trend_stability_score=trend_score,
                insulin_sensitivity_score=insulin_score,
                lifestyle_score=lifestyle_score,
                avg_glucose=round(avg_glucose, 1),
                glucose_variability=round(variability_cv, 1),
                homa_ir=homa_ir,
                trend_slope=round(slope_month, 2),
                lower_bound_80=max(0, round(total_score - interval_80, 1)),
                upper_bound_80=min(100, round(total_score + interval_80, 1)),
                lower_bound_95=max(0, round(total_score - interval_95, 1)),
                upper_bound_95=min(100, round(total_score + interval_95, 1)),
                measurements_used=len(measurements),
                data_quality_score=data_quality["score"],
                evidence={"drift_detected": drift_detected, "drift_reason": drift_reason, "avg_fasting_glucose": avg_fasting_glucose, "latest_hba1c": latest_hba1c},
            )
            db.session.add(record)

        previous = (
            StabilityRecord.query.filter(
                StabilityRecord.user_id == user_id,
                StabilityRecord.calculated_at < datetime.utcnow() - timedelta(days=30),
            )
            .order_by(StabilityRecord.calculated_at.desc())
            .first()
        )
        if previous and previous.stability_score - total_score > 15:
            db.session.add(
                Alert(
                    user_id=user_id,
                    alert_type="trend_warning",
                    severity="HIGH",
                    title="Metabolic stability drop detected",
                    message=f"Stability score dropped by {round(previous.stability_score - total_score, 1)} points in 30 days.",
                    recommendation="Review recent diet, activity, and glucose trends and consider medical review.",
                )
            )

        db.session.add(AuditLog(user_id=user_id, action="calculate_stability", resource_type="stability_record", details={"score": total_score, "state": metabolic_state.value}))
        db.session.flush()
        return record

    @staticmethod
    def _ai_trajectory_prediction(user_id, historical_scores, horizon_days=30):
        """AI-enhanced trajectory prediction using ensemble models"""
        try:
            if len(historical_scores) < 5:
                return None, None
            
            # Prepare features for AI models
            scores_array = np.array(historical_scores)
            time_steps = np.arange(len(historical_scores)).reshape(-1, 1)
            
            # Create advanced features
            features = np.column_stack([
                time_steps,
                scores_array,
                np.roll(scores_array, 1),  # Previous score
                np.roll(scores_array, 2),  # Two scores back
                np.convolve(scores_array, np.ones(3)/3, mode='same'),  # Moving average
                np.gradient(scores_array),  # Rate of change
                np.gradient(np.gradient(scores_array))  # Acceleration
            ])
            
            # Remove NaN values
            features = features[2:]
            y = scores_array[2:]
            
            if len(features) < 3:
                return None, None
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(features)
            
            # Ensemble of advanced AI models
            models = {
                'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
                'gradient_boost': GradientBoostingRegressor(n_estimators=100, random_state=42),
                'ridge': Ridge(alpha=2.0),
                'svr': SVR(kernel='rbf', C=10.0, gamma='scale')
            }
            
            # Train and evaluate models
            model_scores = {}
            trained_models = {}
            
            for name, model in models.items():
                try:
                    cv_scores = cross_val_score(model, X_scaled, y, cv=3, scoring='r2')
                    model_scores[name] = np.mean(cv_scores)
                    
                    model.fit(X_scaled, y)
                    trained_models[name] = model
                except:
                    model_scores[name] = -1
            
            # Select best performing model
            best_model_name = max(model_scores, key=model_scores.get)
            best_score = model_scores[best_model_name]
            
            if best_score < 0.2:  # If AI models are not good enough
                return None, None
            
            best_model = trained_models[best_model_name]
            
            # Generate future predictions
            future_predictions = []
            last_features = X_scaled[-1:].copy()
            
            for _ in range(horizon_days):
                next_pred = best_model.predict(last_features)[0]
                future_predictions.append(max(0, min(100, next_pred)))
                
                # Update features for next prediction
                last_features = np.roll(last_features, -1)
                last_features[0, -1] = np.gradient(future_predictions[-3:])[-1] if len(future_predictions) >= 3 else 0
            
            return future_predictions, best_model_name
            
        except Exception as e:
            print(f"AI trajectory prediction error: {e}")
            return None, None

    @staticmethod
    def predict_trajectory(user_id, horizon_days=30):
        historical = StabilityRecord.query.filter_by(user_id=user_id).order_by(StabilityRecord.calculated_at.asc()).all()
        if len(historical) < 5:
            return {"error": "insufficient_history", "required": 5, "current": len(historical)}

        scores = [r.stability_score for r in historical]
        
        # Use Holt linear method (AI temporarily disabled)
        alpha = 0.3
        beta = 0.2
        level = scores[0]
        trend = scores[1] - scores[0]
        for idx in range(1, len(scores)):
            prev_level = level
            level = alpha * scores[idx] + (1 - alpha) * (level + trend)
            trend = beta * (level - prev_level) + (1 - beta) * trend

        predictions = []
        for week in range(1, max(1, horizon_days // 7) + 1):
            predicted = max(0, min(100, level + week * trend))
            predictions.append(
                {
                    "week": week,
                    "predicted_score": round(predicted, 1),
                    "lower_bound": round(max(0, predicted - 15), 1),
                    "upper_bound": round(min(100, predicted + 15), 1),
                    "lower_bound_95": round(max(0, predicted - 22), 1),
                    "upper_bound_95": round(min(100, predicted + 22), 1),
                }
            )
        
        trend_slope = trend
        
        # AI trajectory prediction disabled temporarily
        # ai_predictions, ai_model = MetabolicStabilityEngine._ai_trajectory_prediction(user_id, scores, horizon_days)
        # if ai_predictions:
        #     # Use AI predictions...

        trajectory = "IMPROVING" if trend_slope > 2 else "WORSENING" if trend_slope < -2 else "STABLE"
        current_score = scores[-1]
        future_score = predictions[-1]["predicted_score"]
        diabetes_risk = "HIGH" if current_score < 30 or future_score < 30 else "MODERATE" if current_score < 50 or future_score < 50 else "LOW"
        predicted_state = MetabolicState.STABLE if future_score >= 80 else MetabolicState.PREDIABETIC_EARLY if future_score >= 50 else MetabolicState.PREDIABETIC_LATE if future_score >= 30 else MetabolicState.DIABETIC
        existing = (
            PredictionRecord.query.filter(
                PredictionRecord.user_id == user_id,
                PredictionRecord.horizon_days == horizon_days,
                PredictionRecord.created_at >= datetime.utcnow() - timedelta(hours=12),
            )
            .order_by(PredictionRecord.created_at.desc())
            .first()
        )
        if existing:
            existing.predicted_stability_score = future_score
            existing.predicted_state = predicted_state
            existing.diabetes_risk = diabetes_risk
            existing.lower_bound_80 = predictions[-1]["lower_bound"]
            existing.upper_bound_80 = predictions[-1]["upper_bound"]
            existing.lower_bound_95 = predictions[-1]["lower_bound_95"]
            existing.upper_bound_95 = predictions[-1]["upper_bound_95"]
            existing.model_version = "holt-linear-v1"
            existing.features_used = ["stability_score_history"]
        else:
            db.session.add(
                PredictionRecord(
                    user_id=user_id,
                    horizon_days=horizon_days,
                    predicted_stability_score=future_score,
                    predicted_state=predicted_state,
                    diabetes_risk=diabetes_risk,
                    lower_bound_80=predictions[-1]["lower_bound"],
                    upper_bound_80=predictions[-1]["upper_bound"],
                    lower_bound_95=predictions[-1]["lower_bound_95"],
                    upper_bound_95=predictions[-1]["upper_bound_95"],
                    model_version="holt-linear-v1",
                    features_used=["stability_score_history"],
                )
            )
        return {"trajectory": trajectory, "trend_slope": round(trend, 2), "predictions": predictions, "diabetes_risk_90d": diabetes_risk, "next_assessment_date": (datetime.utcnow() + timedelta(days=horizon_days)).isoformat()}

    @staticmethod
    def detect_anomaly(new_measurement, user_history):
        if new_measurement.measurement_type in {MeasurementType.FASTING_GLUCOSE, MeasurementType.POSTPRANDIAL_GLUCOSE, MeasurementType.RANDOM_GLUCOSE}:
            if new_measurement.value >= 250:
                return True, "HIGH", "Severe hyperglycemia detected"
            if new_measurement.value <= 60:
                return True, "HIGH", "Hypoglycemia detected"
            if new_measurement.value >= 180:
                return True, "MEDIUM", "Post-meal glucose above target"

        comparable = [m.value for m in user_history if m.measurement_type == new_measurement.measurement_type][-30:]
        if len(comparable) >= 10:
            q1, q3 = np.percentile(comparable, [25, 75])
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            if new_measurement.value < lower or new_measurement.value > upper:
                return True, "HIGH", f"Value {new_measurement.value} outside the user's typical range"

        last_same_type = next((m for m in reversed(user_history) if m.measurement_type == new_measurement.measurement_type), None)
        if last_same_type:
            hours_diff = (new_measurement.timestamp - last_same_type.timestamp).total_seconds() / 3600
            if 0 < hours_diff <= 24:
                change_rate = abs(new_measurement.value - last_same_type.value) / hours_diff
                if change_rate > 10:
                    return True, "MEDIUM", "Rapid metabolic change detected"

        if new_measurement.measurement_type == MeasurementType.FASTING_GLUCOSE and len(comparable) >= 5 and new_measurement.value > np.mean(comparable[-5:]) + 15:
            return True, "MEDIUM", "Fasting glucose elevated above baseline"
        return False, "LOW", "Normal variation"

    @staticmethod
    def publish_snapshot(user_id, stability_payload, prediction_payload=None, alerts=None):
        insights = []
        components = stability_payload.get("components", {})
        if components.get("glucose_control", 40) < 20:
            insights.append("Glucose control has become the dominant risk driver.")
        if components.get("insulin_sensitivity", 20) < 12:
            insights.append("Insulin resistance pattern is contributing to reduced stability.")
        if stability_payload.get("evidence", {}).get("drift_detected"):
            insights.append("Metabolic drift has been detected from recent fasting trends.")
        if prediction_payload and prediction_payload.get("trajectory") == "WORSENING":
            insights.append("Thirty-day trajectory suggests worsening control without intervention.")
        if not insights:
            insights.append("Current pattern is relatively stable; continue consistent logging.")

        websocket_hub.publish(
            user_id,
            {
                "type": "stability_update",
                "stability_score": stability_payload["stability_score"],
                "stability": stability_payload,
                "prediction": prediction_payload,
                "alerts": alerts or [],
                "insights": insights,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
