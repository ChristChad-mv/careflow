
import { initializeApp, cert, getApps, applicationDefault } from 'firebase-admin/app';
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

console.log('---------------------------------------------------------');
console.log('🔥  FIREBASE CONFIGURATION CHECK');
console.log('---------------------------------------------------------');
console.log(`🆔  Project ID : ${projectId}`);
console.log(`📧  Client Email: ${clientEmail ? clientEmail : 'Not provided (Using ADC)'}`);
console.log('---------------------------------------------------------');

if (!projectId) {
    console.error('❌ Missing FIREBASE_PROJECT_ID (or NEXT_PUBLIC_FIREBASE_PROJECT_ID).');
    process.exit(1);
}

if (projectId?.includes('careflow-b7a79')) {
    console.warn('⚠️  WARNING: It looks like you are using the "careflow-b7a79" project.');
    console.warn('   The user requested NOT to use this specific project file/id if it is incorrect.');
}

// Initialize Firebase Admin
let app;
if (getApps().length === 0) {
    if (clientEmail && privateKey) {
        app = initializeApp({
            credential: cert({
                projectId,
                clientEmail,
                privateKey,
            }),
        });
        console.log('🔐 Authenticated with Service Account (Env Vars)');
    } else {
        app = initializeApp({
            projectId,
            credential: applicationDefault()
        });
        console.log('👤 Authenticated with Application Default Credentials (ADC/GCloud)');
    }
} else {
    app = getApps()[0];
}

// Connect to the specific named database
const db = getFirestore(app, 'careflow-db');
const auth = getAuth(app);

const purgeCollections = async () => {
    console.log('🗑️ Purging existing collections...');
    const collections = ['users', 'patients', 'alerts'];
    for (const colName of collections) {
        const snapshot = await db.collection(colName).get();
        if (snapshot.empty) continue;

        const batch = db.batch();
        snapshot.docs.forEach((doc) => {
            batch.delete(doc.ref);
        });
        await batch.commit();
        console.log(`   - Purged ${snapshot.size} docs from ${colName}`);
    }
};

const ensureAuthUser = async (email: string, uid: string, displayName: string) => {
    try {
        await auth.updateUser(uid, {
            email,
            displayName,
            password: 'password123', // Reset password to default for testing
            emailVerified: true
        });
        console.log(`   - Auth User updated: ${email}`);
    } catch (error: any) {
        if (error.code === 'auth/user-not-found') {
            await auth.createUser({
                uid,
                email,
                displayName,
                password: 'password123',
                emailVerified: true
            });
            console.log(`   - Auth User created: ${email}`);
        } else {
            console.error(`   ❌ Error managing auth user ${email}:`, error);
        }
    }
};

const seedUsers = async () => {
    console.log('🌱 Seeding Users...');

    const users = [
        // HOSPITAL 1: Central Hospital (Nurse Sarah)
        {
            userId: "user_nurse_sarah", // UID matches seed
            email: "sarah@hosp1.com",
            name: "Sarah Johnson, RN",
            role: "nurse",
            department: "Cardiology",
            hospitalId: "HOSP001",
            phone: "+15559876543",
            assignedPatientIds: [
                "p_h1_001"
            ],
            preferences: {
                notificationMethod: "both",
                alertSound: true,
                timezone: "America/New_York"
            },
            createdAt: Timestamp.now(),
            lastLoginAt: Timestamp.now(),
            isActive: true,
            customClaims: { role: "nurse", hospitalId: "HOSP001", department: "Cardiology" }
        },
        // HOSPITAL 2: St. Mary's Clinic (Nurse John)
        {
            userId: "user_nurse_john",
            email: "john@hosp2.com",
            name: "John Smith, RN",
            role: "nurse",
            department: "Geriatrics",
            hospitalId: "HOSP002",
            phone: "+15551234567",
            assignedPatientIds: [
                "p_h2_001", "p_h2_002"
            ],
            preferences: {
                notificationMethod: "email",
                alertSound: false,
                timezone: "America/New_York"
            },
            createdAt: Timestamp.now(),
            lastLoginAt: Timestamp.now(),
            isActive: true,
            customClaims: { role: "nurse", hospitalId: "HOSP002", department: "Geriatrics" }
        }
    ];

    for (const user of users) {
        // 1. Ensure Firebase Auth User exists
        await ensureAuthUser(user.email, user.userId, user.name);

        // 2. Set Custom Claims for RBAC
        await auth.setCustomUserClaims(user.userId, user.customClaims);

        // 3. Create in Firestore
        await db.collection('users').doc(user.userId).set({
            email: user.email,
            name: user.name,
            role: user.role,
            department: user.department,
            hospitalId: user.hospitalId,
            phone: user.phone,
            assignedPatientIds: user.assignedPatientIds,
            preferences: user.preferences,
            createdAt: user.createdAt,
            lastLoginAt: user.lastLoginAt,
            isActive: user.isActive
        });
        console.log(`✅ Upserted Firestore profile: ${user.name}`);
    }
    return users; // Return users to help next steps
};

const seedPatients = async () => {
    console.log('🌱 Seeding Patients...');

    // HOSPITAL 1 PATIENTS
    const patientsH1 = [
        {
            id: "p_h1_001",
            hospitalId: "HOSP001",
            name: "Christ Chadrak MVOUNGOU",
            email: "christ.mvoungou@email.com",
            dateOfBirth: "1990-06-25",
            contact: { phone: "+33744533386", preferredMethod: "phone" },
            assignedNurse: { name: "Sarah Johnson, RN", email: "sarah@hosp1.com", phone: "+15559876543" },
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
            riskLevel: "safe", // Green
            aiBrief: "Patient stable. Blood sugar levels well controlled. Following diet plan.",
            status: "active"
        }
    ];

    // HOSPITAL 2 PATIENTS (Empty for this test)
    const patientsH2: any[] = [];

    const allPatients = [...patientsH1, ...patientsH2];

    for (const p of allPatients) {
        await db.collection('patients').doc(p.id).set(p);
        console.log(`✅ Upserted patient: ${p.name} (${p.hospitalId})`);
    }

    // Seed Alerts based on patients
    console.log('🌱 Seeding Alerts...');
    for (const p of allPatients) {
        if (p.riskLevel === 'critical' || p.riskLevel === 'warning') {
            const alertId = `alert_${p.id}`;
            await db.collection('alerts').doc(alertId).set({
                id: alertId,
                patientId: p.id,
                hospitalId: p.hospitalId,
                patientName: p.name,
                riskLevel: p.riskLevel,
                priority: p.riskLevel, // Using new priority field
                status: 'active',
                aiBrief: p.aiBrief,
                trigger: p.riskLevel === 'critical' ? "Critical Update from Daily Round" : "Routine Check-in Flag",
                createdAt: Timestamp.now(),
                updatedAt: Timestamp.now()
            });
            console.log(`🚨 Upserted alert for: ${p.name}`);
        }
    }
};

const main = async () => {
    try {
        await purgeCollections();
        await seedUsers();
        await seedPatients();
        console.log('✨ Database seeding (Purge + Auth + Data) completed successfully.');
        process.exit(0);
    } catch (error) {
        console.error('❌ Error Seeding Database:', error);
        process.exit(1);
    }
};

main();
