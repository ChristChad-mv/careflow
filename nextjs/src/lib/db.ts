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

    // 2. Dev Fallback (Only if no session AND in development)
    if (process.env.NODE_ENV === 'development') {
        console.warn("⚠️ No active session using MOCK [HOSP001] Sarah profile for DEV.");
        return {
            email: "sarah@hosp1.com",
            name: "Sarah Johnson, RN",
            role: "nurse",
            hospitalId: "HOSP001"
        };
    }

    // 3. No session and not dev -> Return null (will cause 401/redirect in callers)
    return null;
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
    // We fetch ALL alerts for the hospital to avoid the "10 items" limit of 'in' queries
    let query = db.collection("alerts").where('hospitalId', '==', user.hospitalId);

    // Filter by timestamp if needed, or just get latest
    const snapshot = await query.orderBy("createdAt", "desc").limit(500).get(); // Safety limit
    let alerts = snapshot.docs.map(doc => convertAlert(doc));

    // Nurse Role: Filter by assigned patients only (IN MEMORY)
    if (user.role === 'nurse') {
        const myPatients = await getPatients();
        const myPatientIds = new Set(myPatients.map(p => p.id));

        // Filter alerts where patientId is in the nurse's patient list
        alerts = alerts.filter(alert => myPatientIds.has(alert.patientId));
    }

    // Sort by priority on the server/app side
    const priorityMap: Record<string, number> = { 'critical': 3, 'warning': 2, 'safe': 1 };

    return alerts.sort((a, b) => {
        const pA = priorityMap[a.priority || 'safe'] || 0;
        const pB = priorityMap[b.priority || 'safe'] || 0;
        // Primary sort: Priority (desc)
        if (pB !== pA) return pB - pA;
        // Secondary sort: Date (desc)
        return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
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
    const user = await getCurrentUser();
    if (!user || !user.hospitalId) {
        return {
            totalPatients: 0,
            criticalAlerts: 0,
            readmissionRate: 0,
            statusCounts: { safe: 0, warning: 0, critical: 0 }
        };
    }

    const db = await getAdminDb();

    // 1. Total Patients (Aggregation)
    // Filter by hospital and assigned nurse
    let patientsQuery = db.collection("patients").where('hospitalId', '==', user.hospitalId);
    if (user.role === 'nurse') {
        patientsQuery = patientsQuery.where("assignedNurse.email", "==", user.email);
    }
    const totalPatientsSnap = await patientsQuery.count().get();
    const totalPatients = totalPatientsSnap.data().count;

    // 2. Critical Alerts (Aggregation)
    // Note: For critical alerts, we still need to respect the nurse's patient list. 
    // Since we can't do an 'in' query with >10 items, and we can't easily join in Firestore,
    // we have two options: 
    // A) Fetch all nurse's patients IDs (cheap-ish) and count alerts for them (hard with limit)
    // B) Fetch all 'critical' alerts for the hospital and filter in memory (likely small-ish number)
    // C) Just counting total critical alerts for the hospital might be misleading if it's for other nurses' patients.
    // Let's go with B for accuracy, similar to getAlerts but only for 'critical' to optimize.

    let criticalAlertsCount = 0;

    // Base alerts query
    const alertsQuery = db.collection("alerts")
        .where('hospitalId', '==', user.hospitalId)
        .where('priority', 'in', ['critical', 'CRITICAL', 'RED']); // Handle variations

    const criticalSnaps = await alertsQuery.get();

    if (user.role === 'nurse') {
        // We need the nurse's patient IDs to filter
        // Optimization: We could cache this list or assume getPatients is fast enough (it fetches docs)
        // For stats, maybe we just want the number. 
        // Let's fetch the patients query from above but we need IDs. 
        // Actually, let's just reuse getPatients() logic but optimized? 
        // No, let's keep it simple: filter the cached/fetched alerts. It's robust.

        const myPatients = await getPatients();
        const myPatientIds = new Set(myPatients.map(p => p.id));

        criticalAlertsCount = criticalSnaps.docs.filter(doc => {
            const data = doc.data();
            return myPatientIds.has(data.patientId);
        }).length;

    } else {
        criticalAlertsCount = criticalSnaps.size;
    }

    // 3. Status Counts (Aggregation)
    // We can run 3 count queries in parallel
    const statusQueries = ['safe', 'warning', 'critical'].map(status => {
        // status stored as 'currentStatus' or 'riskLevel' ? 
        // The convertPatient function maps 'riskLevel' to currentStatus.
        // We need to query the raw field. Assuming it's 'riskLevel' in Firestore based on mapRiskLevel.
        // mapRiskLevel handles RED, CRITICAL -> critical. 
        // So we need to query for multiple raw values.

        let q = patientsQuery;
        if (status === 'critical') q = q.where('riskLevel', 'in', ['RED', 'CRITICAL', 'critical']);
        else if (status === 'warning') q = q.where('riskLevel', 'in', ['YELLOW', 'WARNING', 'warning']);
        else q = q.where('riskLevel', 'in', ['GREEN', 'SAFE', 'safe']); // Default/Safe

        return q.count().get();
    });

    const [safeSnap, warningSnap, criticalSnap] = await Promise.all(statusQueries);

    return {
        totalPatients,
        criticalAlerts: criticalAlertsCount,
        readmissionRate: 12.3, // Still hardcoded for now, potential todo
        statusCounts: {
            safe: safeSnap.data().count,
            warning: warningSnap.data().count,
            critical: criticalSnap.data().count,
        }
    };
}
