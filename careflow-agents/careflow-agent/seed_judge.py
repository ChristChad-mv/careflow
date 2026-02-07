import firebase_admin
from firebase_admin import credentials, firestore, auth
from google.cloud import firestore as google_firestore
from datetime import datetime, timezone, timedelta
import os
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize with ADC
print("Initializing Firebase Admin with ADC...")
try:
    app = firebase_admin.get_app()
except ValueError:
    cred = credentials.ApplicationDefault()
    app = firebase_admin.initialize_app(cred, {
        'projectId': 'careflow-478811',
    })

# Connect to specific database
print("Connecting to Firestore database: careflow-db")
db = google_firestore.Client(project='careflow-478811', database='careflow-db')

def seed_data():
    print("🚀 Starting seeding for Sarah Johnson, RN and Christ Chadrak MVOUNGOU...")    
    
    # Configuration based on the provided image
    uid = "user_nurse_sarah"
    email = "judge-hackathon@careflow.demo"
    password = os.environ.get("JUDGE_PASSWORD")
    name = "Sarah Johnson, RN"
    phone = "+15559876543"
    hospital_id = "HOSP001"
    department = "Care Coordination"
    p_id = "p_h1_001"

    # 1. Configure Firebase Auth
    try:
        try:
            auth.get_user(uid)
            auth.update_user(uid, email=email, password=password, display_name=name)
            print(f"✅ Auth User updated: {email}")
        except auth.UserNotFoundError:
            auth.create_user(uid=uid, email=email, password=password, display_name=name)
            print(f"✅ Auth User created: {email}")
        
        auth.set_custom_user_claims(uid, {
            "role": "nurse", 
            "hospitalId": hospital_id, 
            "department": department
        })
    except Exception as e:
        print(f"⚠️ Auth error: {e}")

    # 2. Seed 'users' collection (matches image exactly)
    user_doc = {
        "userId": uid,
        "name": name,
        "email": email,
        "phone": phone,
        "role": "nurse",
        "hospitalId": hospital_id,
        "department": department,
        "isActive": True,
        "assignedPatientIds": [],
        "preferences": {
            "alertSound": True,
            "notificationMethod": "both",
            "timezone": "America/New_York"
        },
        "createdAt": datetime.now(timezone.utc),
        "lastLoginAt": datetime.now(timezone.utc)
    }
    
    try:
        db.collection("users").document(uid).set(user_doc)
        print(f"✅ Firestore User configured: {uid}")
    except Exception as e:
        print(f"⚠️ Firestore User error: {e}")

    # 3. Seed 'patients' collection
    patient_data = {
        "id": p_id,
        "hospitalId": hospital_id,
        "name": "Christ Chadrak MVOUNGOU",
        "email": "christ.mvoungou@email.com",
        "dateOfBirth": "1990-06-25",
        "contact": { "phone": "+33744533386", "preferredMethod": "phone" },
        "assignedNurse": { 
            "name": name, 
            "email": email, 
            "phone": phone 
        },
        "dischargePlan": {
            "diagnosis": "Type 2 Diabetes",
            "dischargeDate": datetime.now(),
            "hospitalId": "HOSP001",
            "dischargingPhysician": "Dr. A. Carter",
            "medications": [
                { "name": "Metformin", "dosage": "500mg", "frequency": "Twice daily", "instructions": "Take with meals", "scheduleHour": 8, "startDate": datetime.now() },
                { "name": "Glipizide", "dosage": "5mg", "frequency": "Once daily", "instructions": "Take before breakfast", "scheduleHour": 7, "startDate": datetime.now() }
            ],
            "criticalSymptoms": ["Blood sugar > 300 mg/dL", "Confusion or dizziness", "Severe thirst"],
            "warningSymptoms": ["Frequent urination", "Fatigue", "Blurred vision"]
        },
        "nextAppointment": { "date": "2026-02-15T10:00:00Z", "type": "Follow-up", "location": "Diabetes Care Center" },
        "riskLevel": "safe",
        "aiBrief": "Patient stable. Blood sugar levels well controlled. Following diet plan.",
        "status": "active",
        "lastAssessmentDate": datetime.now()
    }
        
    db.collection("patients").document(p_id).set(patient_data)
    print(f"✅ Patient data seeded: {p_id}")

if __name__ == "__main__":
    seed_data()
