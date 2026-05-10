from models import Measurement, MeasurementType

VARIABILITY_INTERVENTIONS = [
    {
        "id": "high_variability_balanced_meals",
        "title": "Balanced Meal Composition",
        "description": "Reduce glucose swings by balancing carbohydrate exposure with protein and fiber.",
        "actions": [
            "Include 20-30g of protein with each main meal.",
            "Limit carbohydrates to about 45g per meal until post-meal readings stabilize.",
            "Add high-fiber vegetables to lunch and dinner every day.",
        ],
        "expected_improvement": "20-30% reduction in glucose spikes within 2 weeks",
        "expected_timeline_days": 14,
        "priority_rank": 1,
        "warning_signs": ["Post-meal glucose above 180 mg/dL", "Persistent afternoon fatigue"],
    },
    {
        "id": "timing_consistency",
        "title": "Consistent Meal Timing",
        "description": "Regular meal timing can reduce fasting drift and unpredictable variability.",
        "actions": [
            "Keep meals within the same 60-minute window each day.",
            "Avoid late-night eating after 8 PM on most days.",
            "Space main meals about 4-5 hours apart.",
        ],
        "expected_improvement": "15-20% reduction in variability within 1 week",
        "expected_timeline_days": 7,
        "priority_rank": 2,
        "warning_signs": ["Rising fasting glucose", "Frequent evening snacking"],
    },
]

INSULIN_SENSITIVITY_INTERVENTIONS = [
    {
        "id": "post_meal_walks",
        "title": "Post-Meal Physical Activity",
        "description": "Short movement sessions after meals improve glucose disposal and insulin response.",
        "actions": [
            "Walk for 15 minutes after your largest meal.",
            "Add light resistance moves every 2-3 hours during sedentary days.",
            "Aim for 8000 steps on at least 5 days per week.",
        ],
        "expected_improvement": "10-15% HOMA-IR reduction in 4 weeks",
        "expected_timeline_days": 28,
        "priority_rank": 1,
        "warning_signs": ["Fasting insulin above 15 uU/mL", "Post-meal readings slow to recover"],
    },
    {
        "id": "overnight_fasting",
        "title": "Overnight Fasting Routine",
        "description": "A consistent overnight fast can improve fasting glucose and insulin sensitivity.",
        "actions": [
            "Maintain a 12-hour overnight fast between dinner and breakfast.",
            "Avoid calorie-containing snacks between meals.",
            "If tolerated, extend to a 14-hour fast twice a week.",
        ],
        "expected_improvement": "15-20% improvement in insulin sensitivity",
        "expected_timeline_days": 28,
        "priority_rank": 2,
        "warning_signs": ["Morning glucose continues to rise", "Frequent overnight snacking"],
    },
]

WEIGHT_INTERVENTIONS = [
    {
        "id": "metabolic_deficit",
        "title": "Caloric Deficit with Metabolic Focus",
        "description": "A modest calorie reduction can improve weight trend and glycemic control together.",
        "actions": [
            "Reduce meal portions by about 20% while preserving protein.",
            "Replace refined carbohydrates with legumes or whole grains.",
            "Track meals consistently for 2 weeks to identify trigger foods.",
        ],
        "expected_improvement": "0.5-1 kg per week weight loss",
        "expected_timeline_days": 21,
        "priority_rank": 2,
        "warning_signs": ["Weight gain above 5% in 30 days", "Increasing waistline despite stable activity"],
    }
]


class RecommendationEngine:
    @staticmethod
    def generate_interventions(user, latest_stability):
        recommendations = []
        components = latest_stability.to_dict()["components"]
        metrics = latest_stability.to_dict()["metrics"]

        if metrics.get("glucose_variability", 0) and metrics["glucose_variability"] > 25:
            recommendations.extend(VARIABILITY_INTERVENTIONS)

        if (latest_stability.homa_ir or 0) > 2.5 or components["insulin_sensitivity"] < 12:
            recommendations.extend(INSULIN_SENSITIVITY_INTERVENTIONS)

        recent_weight = (
            Measurement.query.filter_by(
                user_id=user.id, measurement_type=MeasurementType.WEIGHT
            )
            .order_by(Measurement.timestamp.desc())
            .limit(2)
            .all()
        )
        if len(recent_weight) == 2 and recent_weight[0].value > recent_weight[1].value * 1.03:
            recommendations.extend(WEIGHT_INTERVENTIONS)

        if components["lifestyle"] < 8:
            recommendations.append(
                {
                    "id": "foundation_reset",
                    "title": "Lifestyle Foundation Reset",
                    "description": "Stabilize routine inputs before making more advanced metabolic changes.",
                    "actions": [
                        "Target 7-8 hours of sleep on most nights.",
                        "Keep breakfast and dinner times consistent.",
                        "Log all meals, glucose checks, and exercise for the next 14 days.",
                    ],
                    "expected_improvement": "5-10 point stability score increase",
                    "expected_timeline_days": 14,
                    "priority_rank": 2,
                    "warning_signs": ["Sleep under 6 hours", "Skipping meals followed by overeating"],
                }
            )

        if not recommendations:
            recommendations.append(
                {
                    "id": "maintenance_plan",
                    "title": "Metabolic Maintenance Plan",
                    "description": "Current stability is relatively preserved, so focus on maintaining trajectory.",
                    "actions": [
                        "Continue current meal and activity routine.",
                        "Check fasting glucose at least 3 times per week.",
                        "Review stability trend weekly for early drift.",
                    ],
                    "expected_improvement": "Sustain current stability and detect drift early",
                    "expected_timeline_days": 21,
                    "priority_rank": 3,
                    "warning_signs": ["Score drop above 10 points", "Two fasting readings above baseline"],
                }
            )

        recommendations.sort(key=lambda item: item.get("priority_rank", 99))
        return recommendations[:3]
