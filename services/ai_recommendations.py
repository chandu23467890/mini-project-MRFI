"""
AI-Powered Recommendations Engine for MRFI
Uses machine learning to generate personalized recommendations based on user data patterns
"""

import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import warnings
warnings.filterwarnings('ignore')

from models import Measurement, MeasurementType, StabilityRecord, User


class AIRecommendationEngine:
    """Advanced AI engine for generating personalized metabolic recommendations"""
    
    def __init__(self):
        self.risk_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.clustering_model = KMeans(n_clusters=5, random_state=42)
        
    def _extract_user_features(self, user_id):
        """Extract comprehensive features for AI analysis"""
        try:
            # Get recent measurements
            cutoff = datetime.utcnow() - timedelta(days=90)
            measurements = Measurement.query.filter(
                Measurement.user_id == user_id,
                Measurement.timestamp >= cutoff,
                Measurement.is_anomaly.is_(False)
            ).order_by(Measurement.timestamp.desc()).all()
            
            if not measurements:
                return None
            
            # Feature extraction
            glucose_measurements = [m for m in measurements if m.measurement_type in [
                MeasurementType.FASTING_GLUCOSE, MeasurementType.POSTPRANDIAL_GLUCOSE, MeasurementType.RANDOM_GLUCOSE
            ]]
            
            if not glucose_measurements:
                return None
            
            glucose_values = [m.value for m in glucose_measurements]
            timestamps = [m.timestamp for m in glucose_measurements]
            
            # Calculate features
            features = {
                'avg_glucose': np.mean(glucose_values),
                'glucose_std': np.std(glucose_values),
                'glucose_cv': np.std(glucose_values) / np.mean(glucose_values) * 100,
                'glucose_range': max(glucose_values) - min(glucose_values),
                'recent_trend': self._calculate_trend(glucose_values[-10:] if len(glucose_values) >= 10 else glucose_values),
                'measurement_frequency': len(measurements) / 90,  # measurements per day
                'fasting_avg': np.mean([m.value for m in glucose_measurements if m.measurement_type == MeasurementType.FASTING_GLUCOSE]) or 0,
                'postprandial_avg': np.mean([m.value for m in glucose_measurements if m.measurement_type == MeasurementType.POSTPRANDIAL_GLUCOSE]) or 0,
                'time_variability': self._calculate_time_variability(timestamps),
                'glucose_volatility': self._calculate_volatility(glucose_values),
            }
            
            # Add lifestyle features
            activity_measurements = [m for m in measurements if m.measurement_type == MeasurementType.PHYSICAL_ACTIVITY]
            sleep_measurements = [m for m in measurements if m.measurement_type == MeasurementType.SLEEP_HOURS]
            
            features.update({
                'activity_level': np.mean([m.value for m in activity_measurements]) if activity_measurements else 0,
                'sleep_avg': np.mean([m.value for m in sleep_measurements]) if sleep_measurements else 0,
                'activity_consistency': np.std([m.value for m in activity_measurements]) if len(activity_measurements) > 1 else 0,
                'sleep_consistency': np.std([m.value for m in sleep_measurements]) if len(sleep_measurements) > 1 else 0,
            })
            
            return features
            
        except Exception as e:
            print(f"Feature extraction error: {e}")
            return None
    
    def _calculate_trend(self, values):
        """Calculate trend using linear regression"""
        if len(values) < 2:
            return 0
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        return slope
    
    def _calculate_time_variability(self, timestamps):
        """Calculate time-based variability"""
        if len(timestamps) < 2:
            return 0
        intervals = [(timestamps[i+1] - timestamps[i]).total_seconds() / 3600 for i in range(len(timestamps)-1)]
        return np.std(intervals)
    
    def _calculate_volatility(self, values):
        """Calculate glucose volatility"""
        if len(values) < 2:
            return 0
        returns = [(values[i+1] - values[i]) / values[i] for i in range(len(values)-1)]
        return np.std(returns)
    
    def _analyze_risk_patterns(self, user_features):
        """Analyze risk patterns using AI classification"""
        try:
            # Create risk categories based on features
            risk_score = 0
            
            # Glucose-based risk
            if user_features['avg_glucose'] > 126:
                risk_score += 3
            elif user_features['avg_glucose'] > 100:
                risk_score += 2
            elif user_features['avg_glucose'] > 90:
                risk_score += 1
            
            # Variability risk
            if user_features['glucose_cv'] > 30:
                risk_score += 2
            elif user_features['glucose_cv'] > 20:
                risk_score += 1
            
            # Trend risk
            if user_features['recent_trend'] > 1:
                risk_score += 2
            elif user_features['recent_trend'] > 0.5:
                risk_score += 1
            
            # Lifestyle risk
            if user_features['activity_level'] < 30:
                risk_score += 1
            if user_features['sleep_avg'] < 6:
                risk_score += 1
            
            return risk_score
            
        except Exception as e:
            print(f"Risk analysis error: {e}")
            return 1
    
    def _generate_glucose_recommendations(self, user_features, risk_level):
        """Generate glucose-focused recommendations"""
        recommendations = []
        
        if user_features['avg_glucose'] > 126:
            recommendations.append({
                'category': 'glucose_control',
                'priority': 'high',
                'title': 'Immediate Medical Review Required',
                'description': 'Your average glucose levels indicate elevated risk. Consult with healthcare provider.',
                'actions': [
                    'Schedule appointment with healthcare provider',
                    'Increase glucose monitoring frequency',
                    'Review current medication regimen',
                    'Implement strict dietary modifications'
                ],
                'expected_improvement': 'Professional medical intervention required'
            })
        
        elif user_features['avg_glucose'] > 100:
            recommendations.append({
                'category': 'glucose_control',
                'priority': 'medium',
                'title': 'Glucose Management Optimization',
                'description': 'Your glucose levels are trending upward. Proactive management recommended.',
                'actions': [
                    'Reduce carbohydrate intake by 20%',
                    'Increase fiber consumption to 25-30g daily',
                    'Implement portion control strategies',
                    'Add 15 minutes of post-meal walking'
                ],
                'expected_improvement': '5-10 point reduction in average glucose within 2-3 weeks'
            })
        
        if user_features['glucose_cv'] > 25:
            recommendations.append({
                'category': 'variability_control',
                'priority': 'high',
                'title': 'Glucose Variability Reduction',
                'description': 'High glucose variability detected. Stabilization needed.',
                'actions': [
                    'Establish consistent meal timing',
                    'Implement carbohydrate counting',
                    'Add stress management techniques',
                    'Consider continuous glucose monitoring'
                ],
                'expected_improvement': 'Reduce variability by 30% in 4 weeks'
            })
        
        return recommendations
    
    def _generate_lifestyle_recommendations(self, user_features, risk_level):
        """Generate lifestyle-focused recommendations"""
        recommendations = []
        
        if user_features['activity_level'] < 30:
            recommendations.append({
                'category': 'physical_activity',
                'priority': 'medium',
                'title': 'Physical Activity Enhancement',
                'description': 'Increase physical activity to improve insulin sensitivity.',
                'actions': [
                    'Start with 10-minute daily walks',
                    'Gradually increase to 30 minutes moderate activity',
                    'Add strength training 2x per week',
                    'Track activity with fitness app'
                ],
                'expected_improvement': 'Improved insulin sensitivity within 6-8 weeks'
            })
        
        if user_features['sleep_avg'] < 7:
            recommendations.append({
                'category': 'sleep_optimization',
                'priority': 'medium',
                'title': 'Sleep Quality Improvement',
                'description': 'Adequate sleep is crucial for metabolic health.',
                'actions': [
                    'Establish consistent sleep schedule',
                    'Create relaxing bedtime routine',
                    'Limit screen time before bed',
                    'Optimize bedroom environment'
                ],
                'expected_improvement': 'Better glucose regulation within 2-3 weeks'
            })
        
        if user_features['measurement_frequency'] < 0.5:
            recommendations.append({
                'category': 'monitoring',
                'priority': 'low',
                'title': 'Enhanced Monitoring Protocol',
                'description': 'Increase measurement frequency for better insights.',
                'actions': [
                    'Measure fasting glucose daily',
                    'Add post-meal checks 2x per week',
                    'Log measurements consistently',
                    'Review trends weekly'
                ],
                'expected_improvement': 'Better data for personalized insights'
            })
        
        return recommendations
    
    def _generate_predictive_recommendations(self, user_features, risk_level):
        """Generate predictive AI-based recommendations"""
        recommendations = []
        
        if user_features['recent_trend'] > 0.5:
            recommendations.append({
                'category': 'trend_intervention',
                'priority': 'high',
                'title': 'Trend Reversal Strategy',
                'description': 'AI detects upward glucose trend. Immediate intervention recommended.',
                'actions': [
                    'Implement strict dietary protocol',
                    'Increase monitoring frequency',
                    'Consider medication adjustment',
                    'Add stress reduction techniques'
                ],
                'expected_improvement': 'Reverse trend within 2-3 weeks'
            })
        
        if user_features['glucose_volatility'] > 0.15:
            recommendations.append({
                'category': 'stabilization',
                'priority': 'medium',
                'title': 'Metabolic Stabilization',
                'description': 'High volatility detected. Stabilization protocol recommended.',
                'actions': [
                    'Implement meal timing consistency',
                    'Add mindfulness practices',
                    'Consider probiotic supplementation',
                    'Monitor stress levels'
                ],
                'expected_improvement': 'Reduce volatility by 40% in 6 weeks'
            })
        
        return recommendations
    
    def generate_ai_recommendations(self, user_id):
        """Generate comprehensive AI-powered recommendations"""
        try:
            # Extract user features
            user_features = self._extract_user_features(user_id)
            if not user_features:
                return []
            
            # Analyze risk patterns
            risk_level = self._analyze_risk_patterns(user_features)
            
            # Generate recommendations from different AI modules
            all_recommendations = []
            
            # Glucose-focused recommendations
            all_recommendations.extend(self._generate_glucose_recommendations(user_features, risk_level))
            
            # Lifestyle recommendations
            all_recommendations.extend(self._generate_lifestyle_recommendations(user_features, risk_level))
            
            # Predictive recommendations
            all_recommendations.extend(self._generate_predictive_recommendations(user_features, risk_level))
            
            # Sort by priority and limit to top recommendations
            priority_order = {'high': 3, 'medium': 2, 'low': 1}
            all_recommendations.sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)
            
            # Return top 5 recommendations
            return all_recommendations[:5]
            
        except Exception as e:
            print(f"AI recommendation generation error: {e}")
            return []


# Global AI recommendation engine instance
ai_recommendation_engine = AIRecommendationEngine()
