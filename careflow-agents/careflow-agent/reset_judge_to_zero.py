import firebase_admin
from firebase_admin import credentials, firestore, auth
from google.cloud import firestore as google_firestore
from datetime import datetime, timezone
import os

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
db = google_firestore.Client(project='careflow-478811', database='careflow-db')

def clear_data():
    judge_email = "judge-hackaton@careflow.demo"
    judge_uid = "user_nurse_sarah"
    
    print(f"🧹 Cleaning all data for {judge_email}...")

    # 1. Delete Patients assigned to this judge
    patients_ref = db.collection("patients").where("assignedNurse.email", "==", judge_email).stream()
    count_p = 0
    for doc in patients_ref:
        # Delete associated alerts first
        alerts_ref = db.collection("alerts").where("patientId", "==", doc.id).stream()
        for a_doc in alerts_ref:
            a_doc.reference.delete()
        
        doc.reference.delete()
        count_p += 1
    
    print(f"   - Deleted {count_p} patients and their alerts.")

    # 2. Reset the Judge User Document
    user_ref = db.collection("users").document(judge_uid)
    user_doc = user_ref.get()
    
    if user_doc.exists:
        user_ref.update({
            "assignedPatientIds": [],
            "lastLoginAt": datetime.now(timezone.utc)
        })
        print("   - Judge dashboard reset to ZERO.")
    else:
        # Create the judge account if it doesn't exist at all
        user_ref.set({
            "userId": judge_uid,
            "email": judge_email,
            "name": "Sarah Johnson, RN",
            "role": "nurse",
            "hospitalId": "HOSP001",
            "assignedPatientIds": [],
            "isActive": True,
            "createdAt": datetime.now(timezone.utc)
        })
        print("   - Judge account created (empty).")

    print("\n✨ Ready for the Judges! Dashboard is clean.")

if __name__ == "__main__":
    clear_data()
