/**
 * Script simple pour ajouter le patient Christ Chadrak MVOUNGOU dans Firestore
 * Sans toucher à Firebase Auth (évite les problèmes de quota ADC)
 */

import { initializeApp, getApps, applicationDefault } from 'firebase-admin/app';
import { getFirestore, Timestamp } from 'firebase-admin/firestore';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Load .env
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const envPath = path.resolve(__dirname, '../.env');

if (fs.existsSync(envPath)) {
    const envConfig = fs.readFileSync(envPath, 'utf8');
    envConfig.split('\n').forEach((line) => {
        const match = line.match(/^([^=]+)=(.*)$/);
        if (match) {
            const key = match[1].trim();
            let value = match[2].trim();
            if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
                value = value.slice(1, -1);
            }
            process.env[key] = value;
        }
    });
    console.log('✅ Loaded .env file');
}

const projectId = process.env.FIREBASE_PROJECT_ID || process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID;

if (!projectId) {
    console.error('❌ Missing FIREBASE_PROJECT_ID');
    process.exit(1);
}

// Initialize Firebase
let app;
if (getApps().length === 0) {
    app = initializeApp({
        projectId,
        credential: applicationDefault()
    });
} else {
    app = getApps()[0];
}

const db = getFirestore(app, 'careflow-db');

const main = async () => {
    console.log('🩺 Adding patient Christ Chadrak MVOUNGOU...');

    const patient = {
        id: "p_h1_001",
        hospitalId: "HOSP001",
        name: "Christ Chadrak MVOUNGOU",
        email: "christ.mvoungou@email.com",
        dateOfBirth: "1990-06-25",
        contact: { phone: "+33744533386", preferredMethod: "phone" },
        assignedNurse: { name: "Sarah Johnson, RN", email: "judge-hackathon@careflow.demo", phone: "+15559876543" },
        dischargePlan: {
            diagnosis: "Type 2 Diabetes",
            dischargeDate: Timestamp.now(),
            hospitalId: "HOSP001",
            dischargingPhysician: "Dr. A. Carter",
            medications: [
                { name: "Metformin", dosage: "500mg", frequency: "Twice daily", instructions: "Take with meals", scheduleHour: 8, startDate: Timestamp.now() },
                { name: "Glipizide", dosage: "5mg", frequency: "Once daily", instructions: "Take before breakfast", scheduleHour: 7, startDate: Timestamp.now() }
            ],
            criticalSymptoms: ["Blood sugar > 300 mg/dL", "Confusion or dizziness", "Severe thirst"],
            warningSymptoms: ["Frequent urination", "Fatigue", "Blurred vision"]
        },
        nextAppointment: { date: "2026-02-15T10:00:00Z", type: "Follow-up", location: "Diabetes Care Center" },
        riskLevel: "safe",
        aiBrief: "Patient stable. Blood sugar levels well controlled. Following diet plan.",
        status: "active",
        lastAssessmentDate: Timestamp.now()
    };

    try {
        await db.collection('patients').doc(patient.id).set(patient);
        console.log(`✅ Patient added: ${patient.name}`);
        console.log(`   📞 Phone: ${patient.contact.phone}`);
        console.log(`   🏥 Hospital: ${patient.hospitalId}`);
        console.log(`   💉 Diagnosis: ${patient.dischargePlan.diagnosis}`);
        console.log('✨ Done!');
        process.exit(0);
    } catch (error) {
        console.error('❌ Error:', error);
        process.exit(1);
    }
};

main();
