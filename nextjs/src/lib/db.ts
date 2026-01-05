import { getAdminDb } from "@/lib/firebase-admin";
import { Patient, Alert, Interaction, RiskLevel } from "@/types/patient";

// Helper to map Firestore risk levels to frontend RiskLevel type
const mapRiskLevel = (level: string): RiskLevel => {
    const normalized = level?.toUpperCase();
    if (normalized === 'RED' || normalized === 'CRITICAL') return 'critical';
    if (normalized === 'YELLOW' || normalized === 'WARNING') return 'warning';
    return 'safe'; // Default to safe (GREEN)
};

// Helper to convert Firestore data to Patient object
const convertPatient = (doc: FirebaseFirestore.DocumentSnapshot): Patient => {
    const rawData = doc.data();
    if (!rawData) throw new Error("Document not found");

    // Recursively convert all timestamps first
    const data = convertTimestamps(rawData);

    // Handle nested discharge plan (now safely converted)
    const dischargePlan = data.dischargePlan || {};
    const contact = data.contact || {};

    // Format discharge date safely (it's already a Date object or string from convertTimestamps)
    let dischargeDate = "N/A";
    if (dischargePlan.dischargeDate) {
        try {
            const date = new Date(dischargePlan.dischargeDate);
            dischargeDate = date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
        } catch (e) {
            dischargeDate = String(dischargePlan.dischargeDate);
        }
    }

    return {
        id: doc.id,
        name: data.name || "Unknown Patient",
        diagnosis: dischargePlan.diagnosis || "No diagnosis",
        dischargeDate: dischargeDate,
        contactNumber: contact.phone || "No contact",
        email: data.email,
        dateOfBirth: data.dateOfBirth,
        contact: data.contact,
        medicationPlan: dischargePlan.medications || [],
        currentStatus: mapRiskLevel(data.riskLevel || 'GREEN'),
        dischargePlan: dischargePlan,
        assignedNurse: data.assignedNurse,
        nextAppointment: data.nextAppointment
    };
};

// Helper to recursively convert Firestore Timestamps to Dates
const convertTimestamps = (data: any): any => {
    if (data === null || data === undefined) return data;

    // Handle Firestore Timestamp
    if (typeof data === 'object' && typeof data.toDate === 'function') {
        return data.toDate();
    }

    // Handle Arrays
    if (Array.isArray(data)) {
        return data.map(item => convertTimestamps(item));
    }

    // Handle Objects
    if (typeof data === 'object') {
        const converted: any = {};
        for (const [key, value] of Object.entries(data)) {
            converted[key] = convertTimestamps(value);
        }
        return converted;
    }

    return data;
};

// Helper to convert Firestore data to typed objects (generic fallback)
const convertDoc = <T>(doc: FirebaseFirestore.DocumentSnapshot): T => {
    const data = doc.data();
    if (!data) throw new Error("Document not found");

    return { id: doc.id, ...convertTimestamps(data) } as T;
};

// Helper to convert Firestore data to Alert object with normalization
const convertAlert = (doc: FirebaseFirestore.DocumentSnapshot): Alert => {
    const raw = convertDoc<any>(doc);
    // Prioritize 'priority' field, fallback to 'riskLevel' for legacy data
    const rawLevel = raw.priority || raw.riskLevel || 'GREEN';
    return {
        ...raw,
        priority: mapRiskLevel(rawLevel),
        createdAt: raw.createdAt || raw.timestamp, // Fallback if mixed data
    };
};

import { auth } from "@/lib/auth";

// Helper to get current user context
async function getCurrentUser() {
    const session = await auth();
    // For development/demo purposes without a real login, we fallback to the seeded nurse
    if (!session?.user?.email) {
        console.warn("⚠️ No active session found. Using MOCK nurse profile for development.");
        return {
            email: "nurse@careflow.com",
            role: "nurse"
        };
    }
    console.log(`✅ Session active for: ${session.user.email} (${session.user.role})`);
    return session.user;
}

export async function getPatients(): Promise<Patient[]> {
    const user = await getCurrentUser();
    const db = await getAdminDb();

    // Director/Admin sees everything
    if (user.role === 'admin' || user.role === 'coordinator') {
        const snapshot = await db.collection("patients").get();
        return snapshot.docs.map(doc => convertPatient(doc));
    }

    // Nurses only see assigned patients
    const snapshot = await db.collection("patients")
        .where("assignedNurse.email", "==", user.email)
        .get();

    return snapshot.docs.map(doc => convertPatient(doc));
}

export async function getPatient(id: string): Promise<Patient | null> {
    const db = await getAdminDb();
    const doc = await db.collection("patients").doc(id).get();
    if (!doc.exists) return null;
    return convertPatient(doc);
}

export async function getAlerts(): Promise<Alert[]> {
    const user = await getCurrentUser();
    const db = await getAdminDb();

    // Director/Admin sees all alerts
    if (user.role === 'admin' || user.role === 'coordinator') {
        const snapshot = await db.collection("alerts")
            .orderBy("createdAt", "desc")
            .get();
        return snapshot.docs.map(doc => convertAlert(doc));
    }

    // 1. Get patients assigned to this nurse
    // We reuse getPatients() which already handles the filtering based on the same user context
    const patients = await getPatients();
    const patientIds = patients.map(p => p.id);

    if (patientIds.length === 0) return [];

    // 2. Query alerts for these patients
    // Firestore 'in' query supports up to 10 items. For production, we'd batch or valid structure.
    // For this prototype with <10 patients, it works fine.
    const snapshot = await db
        .collection("alerts")
        .where("patientId", "in", patientIds.slice(0, 10)) // Limit to 10 for safety
        .orderBy("createdAt", "desc")
        .get();

    return snapshot.docs.map(doc => convertAlert(doc));
}

export async function getAlert(alertId: string): Promise<Alert | null> {
    const db = await getAdminDb();
    const doc = await db.collection("alerts").doc(alertId).get();
    if (!doc.exists) return null;
    return convertAlert(doc);
}

export async function getPatientAlerts(patientId: string): Promise<Alert[]> {
    const db = await getAdminDb();
    const snapshot = await db
        .collection("alerts")
        .where("patientId", "==", patientId)
        .orderBy("createdAt", "desc")
        .get();
    return snapshot.docs.map(doc => convertAlert(doc));
}

export async function getInteractions(patientId: string): Promise<Interaction[]> {
    const db = await getAdminDb();
    const snapshot = await db
        .collection("patients")
        .doc(patientId)
        .collection("interactions")
        .orderBy("timestamp", "desc")
        .get();
    return snapshot.docs.map(doc => convertDoc<Interaction>(doc));
}

export async function getDashboardStats() {
    // These functions now internally call getCurrentUser() to filter data
    const patients = await getPatients();
    const alerts = await getAlerts();

    const totalPatients = patients.length;

    // Count alerts belonging to these patients
    const criticalAlerts = alerts.filter(a => a.priority === 'critical').length;

    // Calculate status counts
    const statusCounts = {
        safe: patients.filter(p => p.currentStatus === 'safe').length,
        warning: patients.filter(p => p.currentStatus === 'warning').length,
        critical: patients.filter(p => p.currentStatus === 'critical').length,
    };

    return {
        totalPatients,
        criticalAlerts,
        readmissionRate: 12.3,
        statusCounts
    };
}
