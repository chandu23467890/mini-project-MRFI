#!/usr/bin/env python3
"""
Sample Data Generator for Diabetes Risk Management Application
Creates realistic test data for comprehensive testing
"""

import random
import json
from datetime import datetime, timedelta
from models import User, Measurement, MeasurementType, MealType, db
from run import create_app
import bcrypt

def generate_sample_users():
    """Generate diverse sample users"""
    users_data = [
        {
            "name": "Sarah Johnson",
            "email": "sarah.j@example.com",
            "password": "password123",
            "gender": "female",
            "ethnicity": "caucasian",
            "activity_level": "moderate",
            "family_history_diabetes": True,
            "age": 35
        },
        {
            "name": "Raj Patel",
            "email": "raj.p@example.com", 
            "password": "password123",
            "gender": "male",
            "ethnicity": "south asian",
            "activity_level": "low",
            "family_history_diabetes": True,
            "age": 42
        },
        {
            "name": "Maria Garcia",
            "email": "maria.g@example.com",
            "password": "password123", 
            "gender": "female",
            "ethnicity": "hispanic",
            "activity_level": "high",
            "family_history_diabetes": False,
            "age": 28
        },
        {
            "name": "James Chen",
            "email": "james.c@example.com",
            "password": "password123",
            "gender": "male", 
            "ethnicity": "east asian",
            "activity_level": "moderate",
            "family_history_diabetes": False,
            "age": 31
        },
        {
            "name": "Amanda Williams",
            "email": "amanda.w@example.com",
            "password": "password123",
            "gender": "female",
            "ethnicity": "african american", 
            "activity_level": "high",
            "family_history_diabetes": True,
            "age": 38
        }
    ]
    
    return users_data

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def generate_glucose_measurements(user_id, days=90, risk_level="moderate"):
    """Generate realistic glucose measurements"""
    measurements = []
    base_date = datetime.now() - timedelta(days=days)
    
    # Risk level affects baseline glucose values
    risk_baselines = {
        "low": {"fasting": 85, "postprandial": 110, "random": 95},
        "moderate": {"fasting": 95, "postprandial": 140, "random": 120},
        "high": {"fasting": 110, "postprandial": 180, "random": 150}
    }
    
    baseline = risk_baselines[risk_level]
    
    for day in range(days):
        current_date = base_date + timedelta(days=day)
        
        # Generate 2-4 measurements per day
        num_measurements = random.randint(2, 4)
        
        for i in range(num_measurements):
            # Random time during the day
            hour = random.randint(6, 22)
            minute = random.randint(0, 59)
            measurement_time = current_date.replace(hour=hour, minute=minute)
            
            # Determine measurement type based on time
            if hour <= 8:
                meas_type = MeasurementType.FASTING_GLUCOSE
                base_value = baseline["fasting"]
                meal_context = MealType.FASTING
                unit = "mg/dL"
            elif hour >= 20:
                meas_type = MeasurementType.RANDOM_GLUCOSE
                base_value = baseline["random"]
                meal_context = random.choice([MealType.PRE_MEAL, MealType.BEDTIME])
                unit = "mg/dL"
            else:
                meas_type = MeasurementType.POSTPRANDIAL_GLUCOSE
                base_value = baseline["postprandial"]
                meal_context = random.choice([MealType.POST_MEAL_1H, MealType.POST_MEAL_2H])
                unit = "mg/dL"
            
            # Add realistic variation
            variation = random.gauss(0, 10)  # Standard deviation of 10
            value = max(60, min(300, base_value + variation))  # Clamp between 60-300
            
            # Occasional spikes (10% chance)
            if random.random() < 0.1:
                value = min(300, value * random.uniform(1.2, 1.5))
            
            measurement = {
                "user_id": user_id,
                "measurement_type": meas_type,
                "value": round(value, 1),
                "unit": unit,
                "timestamp": measurement_time,
                "meal_context": meal_context,
                "source": "manual",
                "verification_status": "verified"
            }
            measurements.append(measurement)
    
    return measurements

def generate_other_measurements(user_id, days=90):
    """Generate other health measurements"""
    measurements = []
    base_date = datetime.now() - timedelta(days=days)
    
    for day in range(days):
        current_date = base_date + timedelta(days=day)
        
        # Weight measurements (weekly)
        if day % 7 == 0:
            weight = random.uniform(65, 85)  # kg
            measurements.append({
                "user_id": user_id,
                "measurement_type": MeasurementType.WEIGHT,
                "value": round(weight, 1),
                "unit": "kg",
                "timestamp": current_date.replace(hour=8, minute=0),
                "source": "manual",
                "verification_status": "verified"
            })
        
        # Physical activity (3-5 times per week)
        if random.random() < 0.5:
            activity = random.uniform(15, 90)  # minutes
            hour = random.randint(6, 20)
            measurements.append({
                "user_id": user_id,
                "measurement_type": MeasurementType.PHYSICAL_ACTIVITY,
                "value": round(activity, 1),
                "unit": "minutes",
                "timestamp": current_date.replace(hour=hour, minute=random.randint(0, 59)),
                "source": "manual",
                "verification_status": "verified"
            })
        
        # Sleep hours (daily)
        sleep = random.uniform(5, 9)  # hours
        measurements.append({
            "user_id": user_id,
            "measurement_type": MeasurementType.SLEEP_HOURS,
            "value": round(sleep, 1),
            "unit": "hours",
            "timestamp": current_date.replace(hour=7, minute=0),
            "source": "manual",
            "verification_status": "verified"
        })
        
        # Blood pressure (weekly)
        if day % 7 == 3:  # Mid-week
            systolic = random.uniform(110, 140)
            diastolic = random.uniform(70, 90)
            
            measurements.append({
                "user_id": user_id,
                "measurement_type": MeasurementType.SYSTOLIC_BP,
                "value": round(systolic, 1),
                "unit": "mmHg",
                "timestamp": current_date.replace(hour=9, minute=0),
                "source": "manual",
                "verification_status": "verified"
            })
            
            measurements.append({
                "user_id": user_id,
                "measurement_type": MeasurementType.DIASTOLIC_BP,
                "value": round(diastolic, 1),
                "unit": "mmHg",
                "timestamp": current_date.replace(hour=9, minute=1),
                "source": "manual",
                "verification_status": "verified"
            })
        
        # HbA1c (quarterly)
        if day % 90 == 0:
            hba1c = random.uniform(5.5, 7.5)  # %
            measurements.append({
                "user_id": user_id,
                "measurement_type": MeasurementType.HBA1C,
                "value": round(hba1c, 1),
                "unit": "%",
                "timestamp": current_date.replace(hour=10, minute=0),
                "source": "lab",
                "verification_status": "verified"
            })
    
    return measurements

def generate_meal_logs(user_id, days=90):
    """Generate meal logs with carbohydrate estimates"""
    meals = []
    base_date = datetime.now() - timedelta(days=days)
    
    meal_templates = [
        {"name": "Oatmeal with berries", "carbs": 45, "type": MealType.PRE_MEAL},
        {"name": "Grilled chicken salad", "carbs": 25, "type": MealType.POST_MEAL_2H},
        {"name": "Pasta with tomato sauce", "carbs": 65, "type": MealType.POST_MEAL_2H},
        {"name": "Brown rice and vegetables", "carbs": 55, "type": MealType.POST_MEAL_2H},
        {"name": "Greek yogurt with nuts", "carbs": 30, "type": MealType.PRE_MEAL},
        {"name": "Quinoa bowl", "carbs": 40, "type": MealType.POST_MEAL_2H},
        {"name": "Smoothie", "carbs": 35, "type": MealType.PRE_MEAL},
        {"name": "Sandwich on whole wheat", "carbs": 50, "type": MealType.POST_MEAL_2H}
    ]
    
    for day in range(days):
        current_date = base_date + timedelta(days=day)
        
        # 2-3 meals per day
        num_meals = random.randint(2, 3)
        
        for i in range(num_meals):
            hour = random.choice([7, 8, 12, 13, 18, 19, 20])
            minute = random.randint(0, 59)
            
            meal_template = random.choice(meal_templates)
            
            meal = {
                "user_id": user_id,
                "measurement_type": MeasurementType.CARBS_GRAMS,
                "value": meal_template["carbs"] + random.randint(-10, 10),
                "unit": "g",
                "timestamp": current_date.replace(hour=hour, minute=minute),
                "meal_context": meal_template["type"],
                "source": "food_log",
                "verification_status": "verified",
                "verification_notes": f"Logged: {meal_template['name']}"
            }
            meals.append(meal)
    
    return meals

def create_sample_data():
    """Create comprehensive sample data"""
    app = create_app()
    
    with app.app_context():
        print("🌟 Creating Sample Data for Diabetes Risk Management Application")
        print("=" * 60)
        
        # Clear existing data
        print("🗑️  Clearing existing data...")
        Measurement.query.delete()
        User.query.delete()
        db.session.commit()
        
        # Create users
        users_data = generate_sample_users()
        created_users = []
        
        for user_data in users_data:
            user = User(
                name=user_data["name"],
                email=user_data["email"],
                password_hash=hash_password(user_data["password"]),
                gender=user_data["gender"],
                ethnicity=user_data["ethnicity"],
                activity_level=user_data["activity_level"],
                family_history_diabetes=user_data["family_history_diabetes"],
                timezone="Asia/Calcutta"
            )
            db.session.add(user)
            db.session.flush()
            created_users.append(user)
            print(f"👤 Created user: {user.name} ({user.email})")
        
        # Generate measurements for each user
        total_measurements = 0
        for i, user in enumerate(created_users):
            print(f"\n📊 Generating data for {user.name}...")
            
            # Determine risk level based on profile
            if user.family_history_diabetes and user.ethnicity in ["south asian", "hispanic", "african american"]:
                risk_level = "high"
            elif user.family_history_diabetes or user.ethnicity in ["south asian", "hispanic"]:
                risk_level = "moderate"
            else:
                risk_level = "low"
            
            print(f"   Risk level: {risk_level}")
            
            # Generate glucose measurements
            glucose_measurements = generate_glucose_measurements(user.id, days=90, risk_level=risk_level)
            for meas_data in glucose_measurements:
                measurement = Measurement(**meas_data)
                db.session.add(measurement)
                total_measurements += 1
            
            # Generate other measurements
            other_measurements = generate_other_measurements(user.id, days=90)
            for meas_data in other_measurements:
                measurement = Measurement(**meas_data)
                db.session.add(measurement)
                total_measurements += 1
            
            # Generate meal logs
            meal_measurements = generate_meal_logs(user.id, days=90)
            for meas_data in meal_measurements:
                measurement = Measurement(**meas_data)
                db.session.add(measurement)
                total_measurements += 1
            
            user_measurements = len(glucose_measurements) + len(other_measurements) + len(meal_measurements)
            print(f"   Generated {user_measurements} measurements")
        
        # Commit all data
        db.session.commit()
        
        print(f"\n✅ Sample data creation completed!")
        print(f"   Users created: {len(created_users)}")
        print(f"   Total measurements: {total_measurements}")
        print(f"   Average measurements per user: {total_measurements // len(created_users)}")
        
        # Create test credentials file
        test_creds = {
            "users": [
                {
                    "email": user.email,
                    "password": "password123",
                    "name": user.name
                }
                for user in created_users
            ]
        }
        
        with open("test_credentials.json", "w") as f:
            json.dump(test_creds, f, indent=2)
        
        print(f"\n📄 Test credentials saved to test_credentials.json")
        print("\n🎉 Application is now populated with realistic test data!")
        print("\nTest Users:")
        for user in created_users:
            print(f"   • {user.name} - {user.email} (password: password123)")

if __name__ == "__main__":
    create_sample_data()
