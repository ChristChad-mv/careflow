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

    // 1. If Real Session exists, return it (Production / Real Login)
    if (session?.user) {
        return {
            ...session.user,
            hospitalId: (session.user as any).hospitalId || "HOSP001"
        } as any;
    }

    // 2. Dev Fallback (Only if no session)
    console.warn("⚠️ No active session using MOCK [HOSP001] Sarah profile for DEV.");
    return {
        email: "sarah@hosp1.com",
        name: "Sarah Johnson, RN",
        role: "nurse",
        hospitalId: "HOSP001"
    };
}

export async function getPatients(): Promise<Patient[]> {
    const user = await getCurrentUser();
    if (!user || !user.hospitalId) return [];

    const db = await getAdminDb();
    const patientsRef = db.collection("patients");

    // Base Query: ALWAYS filter by hospitalId first (Logical Isolation)
    let query = patientsRef.where('hospitalId', '==', user.hospitalId);

    // Nurse Role: Additional filter for assignment
    if (user.role === 'nurse') {
        query = query.where("assignedNurse.email", "==", user.email);
    }

    const snapshot = await query.get();
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
    if (!user || !user.hospitalId) return [];

    const db = await getAdminDb();

    // Base Query: ALWAYS filter by hospitalId first
    let query = db.collection("alerts").where('hospitalId', '==', user.hospitalId);

    // Nurse Role: Filter by assigned patients only
    if (user.role === 'nurse') {
        const myPatients = await getPatients();
        const patientIds = myPatients.map(p => p.id);

        if (patientIds.length === 0) return [];

        // Firestore 'in' limit is 10
        if (patientIds.length <= 10) {
            query = query.where('patientId', 'in', patientIds);
        } else {
            query = query.where('patientId', 'in', patientIds.slice(0, 10));
        }
    }

    const snapshot = await query.orderBy("createdAt", "desc").get();
    const alerts = snapshot.docs.map(doc => convertAlert(doc));

    // Sort by priority on the server/app side
    const priorityMap: Record<string, number> = { 'critical': 3, 'warning': 2, 'safe': 1 };

    return alerts.sort((a, b) => {
        const pA = priorityMap[a.priority || 'safe'] || 0;
        const pB = priorityMap[b.priority || 'safe'] || 0;
        return pB - pA;
    });
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
