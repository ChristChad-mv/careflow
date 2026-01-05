import { initializeApp, cert, getApps } from 'firebase-admin/app';
import { getFirestore, Timestamp } from 'firebase-admin/firestore';
import { getAuth } from 'firebase-admin/auth';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Manually load .env file
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
            // Remove quotes if present
            if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
                value = value.slice(1, -1);
            }
            process.env[key] = value;
        }
    });
    console.log('✅ Loaded .env file');
} else {
    console.warn('⚠️ .env file not found at:', envPath);
}

// Load environment variables
const projectId = process.env.FIREBASE_PROJECT_ID || process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID;
const clientEmail = process.env.FIREBASE_CLIENT_EMAIL;
const privateKey = process.env.FIREBASE_PRIVATE_KEY?.replace(/\\n/g, '\n');

if (!projectId || !clientEmail || !privateKey) {
    console.error('❌ Missing Firebase credentials in environment variables.');
    console.error('Required: FIREBASE_PROJECT_ID, FIREBASE_CLIENT_EMAIL, FIREBASE_PRIVATE_KEY');
    process.exit(1);
}

// Initialize Firebase Admin
if (getApps().length === 0) {
    initializeApp({
        credential: cert({
            projectId,
            clientEmail,
            privateKey,
        }),
    });
}

const db = getFirestore();
const auth = getAuth();

const seedUsers = async () => {
    console.log('🌱 Seeding Users...');

    const users = [
        {
            userId: "user_nurse_sarah_123",
            email: "nurse@careflow.com",
            name: "Sarah Johnson, RN",
            role: "nurse",
            department: "Cardiology",
            hospitalId: "HOSP001",
            phone: "+15559876543",
            assignedPatientIds: ["550e8400-e29b-41d4-a716-446655440000"],
            preferences: {
                notificationMethod: "both",
                alertSound: true,
                timezone: "America/New_York"
            },
            createdAt: Timestamp.now(),
            lastLoginAt: Timestamp.now(),
            isActive: true
        },
        {
            userId: "user_coordinator_michael_456",
            email: "coordinator@careflow.com",
            name: "Michael Chen",
            role: "coordinator",
            department: "Patient Care",
            hospitalId: "HOSP001",
            phone: "+15551112222",
            assignedPatientIds: [],
            preferences: {
                notificationMethod: "email",
                alertSound: false,
                timezone: "America/New_York"
            },
            createdAt: Timestamp.now(),
            lastLoginAt: Timestamp.now(),
            isActive: true
        },
        {
            userId: "user_admin_emily_789",
            email: "admin@careflow.com",
            name: "Dr. Emily Rodriguez",
            role: "admin",
            hospitalId: "HOSP001",
            phone: "+15553334444",
            assignedPatientIds: [],
            preferences: {
                notificationMethod: "email",
                alertSound: false,
                timezone: "America/New_York"
            },
            createdAt: Timestamp.now(),
            lastLoginAt: Timestamp.now(),
            isActive: true
        }
    ];

    for (const user of users) {
        // 1. Create/Update Firestore Document
        await db.collection('users').doc(user.userId).set(user);
        console.log(`✅ Firestore: Created user profile for ${user.name}`);

        // 2. Create/Update Firebase Auth User
        try {
            let authUser;
            try {
                authUser = await auth.getUserByEmail(user.email);
                console.log(`ℹ️ Auth: User ${user.email} already exists. Updating...`);
                await auth.updateUser(authUser.uid, {
                    displayName: user.name,
                    emailVerified: true,
                });
            } catch (e: unknown) {
                const error = e as { code?: string };
                if (error.code === 'auth/user-not-found') {
                    console.log(`cw Auth: Creating new user ${user.email}...`);
                    authUser = await auth.createUser({
                        uid: user.userId, // Sync UID with Firestore ID
                        email: user.email,
                        emailVerified: true,
                        password: 'password123',
                        displayName: user.name,
                        disabled: false,
                    });
                } else {
                    throw e;
                }
            }

            // 3. Set Custom Claims (Role, HospitalId)
            await auth.setCustomUserClaims(authUser.uid, {
                role: user.role,
                hospitalId: user.hospitalId,
                department: user.department
            });
            console.log(`✅ Auth: Set custom claims for ${user.email}`);

        } catch (error) {
            console.error(`❌ Error managing Auth user ${user.email}:`, error);
        }
    }
};

const seedPatients = async () => {
    console.log('🌱 Seeding Patients...');

    const patientData = {
        patientId: "550e8400-e29b-41d4-a716-446655440000",
        name: "Sarah Mitchell",
        dateOfBirth: Timestamp.fromDate(new Date('1978-03-15')),
        contact: {
            phone: "+15551234567",
            email: "sarah.mitchell@email.com",
            preferredMethod: "voice"
        },
        dischargePlan: {
            dischargeDate: Timestamp.fromDate(new Date('2025-11-10')),
            diagnosis: "Post-operative cardiac surgery (CABG)",
            dischargingPhysician: "Dr. Emily Rodriguez",
            hospitalId: "HOSP001",
            medications: [
                {
                    name: "Aspirin",
                    dosage: "81mg",
                    frequency: "Once daily at 8:00 AM",
                    scheduleHour: 8,
                    startDate: Timestamp.now()
                },
                {
                    name: "Metoprolol",
                    dosage: "50mg",
                    frequency: "Twice daily at 8:00 AM and 8:00 PM",
                    scheduleHour: 8,
                    startDate: Timestamp.now()
                }
            ],
            criticalSymptoms: ["chest pain", "shortness of breath", "dizziness", "irregular heartbeat"],
            warningSymptoms: ["increased swelling", "persistent fatigue", "mild chest discomfort"]
        },
        riskLevel: "RED", // Set to RED to demonstrate alert
        lastAssessmentDate: Timestamp.now(),
        alert: {
            isCritical: true,
            reason: "Patient reports chest pain radiating to left arm and dizziness",
            timestamp: Timestamp.now(),
            assignedTo: "user_nurse_sarah_123",
            assignedAt: Timestamp.now(),
            status: "in_progress"
        },
        assignedNurse: {
            userId: "user_nurse_sarah_123",
            name: "Sarah Johnson, RN",
            phone: "+15559876543",
            email: "sarah.johnson@hospital.com"
        },
        aiBrief: "URGENT: Patient reports concerning cardiac symptoms consistent with post-CABG complications. Immediate assessment required.",
        createdAt: Timestamp.now(),
        updatedAt: Timestamp.now(),
        status: "active"
    };

    await db.collection('patients').doc(patientData.patientId).set(patientData);
    console.log(`✅ Created patient: ${patientData.name}`);

    // Create an alert for this patient
    const alertData = {
        alertId: "alert_550e8400abc",
        patientId: patientData.patientId,
        patientName: patientData.name,
        riskLevel: "RED",
        trigger: "Chest pain radiating to left arm and dizziness",
        aiBrief: patientData.aiBrief,
        status: "in_progress",
        assignedTo: {
            userId: "user_nurse_sarah_123",
            userName: "Sarah Johnson, RN",
            assignedAt: Timestamp.now()
        },
        createdAt: Timestamp.now(),
        resolvedAt: null,
        resolutionNote: null,
        patientRef: `patients/${patientData.patientId}` // Store as string path for simplicity in this seed
    };

    await db.collection('alerts').doc(alertData.alertId).set(alertData);
    console.log(`✅ Created alert: ${alertData.trigger}`);
};

const main = async () => {
    try {
        await seedUsers();
        await seedPatients();
        console.log('✨ Database seeding completed successfully!');
        process.exit(0);
    } catch (error) {
        console.error('❌ Error seeding database:', error);
        process.exit(1);
    }
};

main();
