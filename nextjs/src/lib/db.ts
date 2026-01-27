import { db } from "@/lib/firebase";
import {
    collection,
    doc as firestoreDoc,
    getDoc,
    getDocs,
    query,
    where,
    orderBy,
    limit,
    getCountFromServer,
    DocumentSnapshot
} from "firebase/firestore";
import { Patient, Alert, Interaction, RiskLevel } from "@/types/patient";

// Helper to map Firestore risk levels to frontend RiskLevel type
const mapRiskLevel = (level: string): RiskLevel => {
    const normalized = level?.toUpperCase();
    if (normalized === 'RED' || normalized === 'CRITICAL') return 'critical';
    if (normalized === 'YELLOW' || normalized === 'WARNING') return 'warning';
    return 'safe'; // Default to safe (GREEN)
};

// Helper to convert Firestore data to Patient object
const convertPatient = (doc: DocumentSnapshot): Patient => {
    const rawData = doc.data();
    if (!rawData) throw new Error("Document not found");

    // Recursively convert all timestamps first
    const data = convertTimestamps(rawData);

    // Handle nested discharge plan (now safely converted)
    const dischargePlan = data.dischargePlan || {};
    const contact = data.contact || {};

    // Format discharge date safely (handle both flattened and legacy nested fields)
    const rawDischargeDate = data.dischargeDate || dischargePlan.dischargeDate;
    let formattedDischargeDate = "N/A";
    if (rawDischargeDate) {
        try {
            const date = new Date(rawDischargeDate);
            formattedDischargeDate = date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
        } catch (e) {
            formattedDischargeDate = String(rawDischargeDate);
        }
    }

    // Safe date conversion helper
    const toIsoString = (val: any) => {
        if (!val) return undefined;
        if (val instanceof Date) return val.toISOString();
        return String(val);
    };

    return {
        id: doc.id,
        name: data.name || "Unknown Patient",
        preferredLanguage: data.preferredLanguage || "en-US",
        // Prefer top-level fields (Unified), fallback to legacy dischargePlan
        diagnosis: data.diagnosis || dischargePlan.diagnosis || "No diagnosis",
        dischargeDate: formattedDischargeDate,
        contactNumber: data.contactNumber || contact.phone || "No contact",
        email: data.email,
        dateOfBirth: toIsoString(data.dateOfBirth),
        contact: data.contact,
        medicationPlan: data.medicationPlan || dischargePlan.medications || [],
        currentStatus: mapRiskLevel(data.riskLevel || 'GREEN'),
        dischargePlan: {
            ...dischargePlan,
            diagnosis: data.diagnosis || dischargePlan.diagnosis,
            medications: data.medicationPlan || dischargePlan.medications,
            criticalSymptoms: data.criticalSymptoms || dischargePlan.criticalSymptoms,
            warningSymptoms: data.warningSymptoms || dischargePlan.warningSymptoms,
            dischargeDate: formattedDischargeDate,
        },
        assignedNurse: data.assignedNurse,
        nextAppointment: data.nextAppointment ? {
            ...data.nextAppointment,
            date: toIsoString(data.nextAppointment.date)
        } : undefined,
        lastCallSid: data.lastCallSid,
        aiBrief: data.aiBrief
    };
};

// Helper to recursively convert Firestore Timestamps to Dates
const convertTimestamps = (data: any): any => {
    if (data === null || data === undefined) return data;

    // Handle Client Firestore Timestamp
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
const convertDoc = <T>(doc: DocumentSnapshot): T => {
    const data = doc.data();
    if (!data) throw new Error("Document not found");

    return { id: doc.id, ...convertTimestamps(data) } as T;
};

// Helper to convert Firestore data to Alert object with normalization
const convertAlert = (doc: DocumentSnapshot): Alert => {
    const raw = convertDoc<any>(doc);
    // Prioritize 'priority' field, fallback to 'riskLevel' for legacy data
    const rawLevel = raw.priority || raw.riskLevel || 'GREEN';

    // Ensure createdAt is a valid Date object
    let date = raw.createdAt || raw.timestamp;

    // If it's a Firestore Timestamp that wasn't converted (unlikely with convertDoc, but safe)
    if (date && typeof date.toDate === 'function') {
        date = date.toDate();
    }
    // If it's a string
    else if (typeof date === 'string') {
        date = new Date(date);
    }

    // If missing or invalid
    if (!date || !(date instanceof Date) || isNaN(date.getTime())) {
        date = new Date(); // Fallback to 'now' to prevent crash
    }

    return {
        ...raw,
        priority: mapRiskLevel(rawLevel),
        createdAt: date.toISOString(), // Always convert to ISO string for React safety
        callSid: raw.callSid // Map callSid
    };
};

export interface UserContext {
    hospitalId?: string;
    role?: string;
    email?: string;
}

export async function getPatients(user: UserContext): Promise<Patient[]> {
    if (!user || !user.hospitalId) return [];

    const patientsRef = collection(db, "patients");

    // Base Query: ALWAYS filter by hospitalId first (Logical Isolation)
    let q = query(patientsRef, where('hospitalId', '==', user.hospitalId));

    // Nurse Role: Additional filter for assignment
    if (user.role === 'nurse' && user.email) {
        q = query(q, where("assignedNurse.email", "==", user.email));
    }

    const snapshot = await getDocs(q);
    return snapshot.docs.map(doc => convertPatient(doc));
}

export async function getPatient(id: string, user: UserContext): Promise<Patient | null> {
    if (!user || !user.hospitalId) return null;

    const docRef = firestoreDoc(db, "patients", id);
    const docSnap = await getDoc(docRef);
    if (!docSnap.exists()) return null;

    // Enforce multi-tenancy: ensure the patient belongs to the user's hospital
    if (docSnap.data()?.hospitalId !== user.hospitalId) {
        console.warn(`Attempted to access patient ${id} from hospital ${docSnap.data()?.hospitalId} by user from ${user.hospitalId}`);
        return null;
    }

    return convertPatient(docSnap);
}

export async function getAlerts(user: UserContext): Promise<Alert[]> {
    if (!user || !user.hospitalId) return [];

    const alertsRef = collection(db, "alerts");

    // Base Query: ALWAYS filter by hospitalId first
    // We fetch ALL alerts for the hospital to avoid the "10 items" limit of 'in' queries
    let q = query(alertsRef, where('hospitalId', '==', user.hospitalId));

    // Filter by timestamp if needed, or just get latest
    // Note: Removed orderBy("createdAt", "desc") to avoid needing a composite index for (hospitalId, createdAt)
    // We sort in memory below anyway.
    const snapshot = await getDocs(query(q, limit(500))); // Safety limit
    let alerts = snapshot.docs.map(doc => convertAlert(doc));

    // Nurse Role: Filter by assigned patients only (IN MEMORY)
    if (user.role === 'nurse') {
        const myPatients = await getPatients(user);
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

export async function getAlert(alertId: string, user: UserContext): Promise<Alert | null> {
    if (!user || !user.hospitalId) return null;

    const docRef = firestoreDoc(db, "alerts", alertId);
    const docSnap = await getDoc(docRef);
    if (!docSnap.exists()) return null;

    // Enforce multi-tenancy: ensure the alert belongs to the user's hospital
    if (docSnap.data()?.hospitalId !== user.hospitalId) {
        console.warn(`Attempted to access alert ${alertId} from hospital ${docSnap.data()?.hospitalId} by user from ${user.hospitalId}`);
        return null;
    }

    return convertAlert(docSnap);
}

export async function getPatientAlerts(patientId: string, user: UserContext): Promise<Alert[]> {
    if (!user || !user.hospitalId) return [];

    // First, verify the patient belongs to the user's hospital
    const patient = await getPatient(patientId, user);
    if (!patient) {
        console.warn(`Patient ${patientId} not found or not accessible by user from ${user.hospitalId}. Cannot fetch alerts.`);
        return [];
    }

    const alertsRef = collection(db, "alerts");
    const q = query(
        alertsRef,
        where("patientId", "==", patientId),
        where('hospitalId', '==', user.hospitalId), // Explicitly filter by hospitalId
        orderBy("createdAt", "desc")
    );
    const snapshot = await getDocs(q);
    return snapshot.docs.map(doc => convertAlert(doc));
}

export async function getInteractions(patientId: string, user: UserContext): Promise<Interaction[]> {
    if (!user || !user.hospitalId) return [];

    // First, verify the patient belongs to the user's hospital
    const patient = await getPatient(patientId, user);
    if (!patient) {
        console.warn(`Patient ${patientId} not found or not accessible by user from ${user.hospitalId}. Cannot fetch interactions.`);
        return [];
    }

    const interactionsRef = collection(db, "patients", patientId, "interactions");
    const q = query(interactionsRef, orderBy("timestamp", "desc"));
    const snapshot = await getDocs(q);

    return snapshot.docs.map(doc => {
        const item = convertDoc<any>(doc);
        return {
            ...item,
            timestamp: item.timestamp instanceof Date ? item.timestamp.toISOString() : String(item.timestamp)
        } as Interaction;
    });
}

export async function getDashboardStats(user: UserContext) {
    if (!user || !user.hospitalId) {
        return {
            totalPatients: 0,
            criticalAlerts: 0,
            readmissionRate: 0,
            statusCounts: { safe: 0, warning: 0, critical: 0 }
        };
    }

    // 1. Total Patients (Aggregation)
    const patientsRef = collection(db, "patients");
    // Filter by hospital and assigned nurse
    let patientsQuery = query(patientsRef, where('hospitalId', '==', user.hospitalId));
    if (user.role === 'nurse' && user.email) {
        patientsQuery = query(patientsQuery, where("assignedNurse.email", "==", user.email));
    }
    const totalPatientsSnap = await getCountFromServer(patientsQuery);
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
    const alertsRef = collection(db, "alerts");
    const alertsQuery = query(alertsRef,
        where('hospitalId', '==', user.hospitalId),
        where('priority', 'in', ['critical', 'CRITICAL', 'RED']) // Handle variations
    );

    const criticalSnaps = await getDocs(alertsQuery);

    if (user.role === 'nurse') {
        // We need the nurse's patient IDs to filter
        // Optimization: We could cache this list or assume getPatients is fast enough (it fetches docs)
        // For stats, maybe we just want the number.
        // Let's fetch the patients query from above but we need IDs.
        // Actually, let's just reuse getPatients() logic but optimized?
        // No, let's keep it simple: filter the cached/fetched alerts. It's robust.

        const myPatients = await getPatients(user);
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
    const statusQueries = ['safe', 'warning', 'critical'].map(async (status) => {
        // status stored as 'currentStatus' or 'riskLevel' ?
        // The convertPatient function maps 'riskLevel' to currentStatus.
        // We need to query the raw field. Assuming it's 'riskLevel' in Firestore based on mapRiskLevel.
        // mapRiskLevel handles RED, CRITICAL -> critical.
        // So we need to query for multiple raw values.

        let q = patientsQuery;
        if (status === 'critical') q = query(q, where('riskLevel', 'in', ['RED', 'CRITICAL', 'critical']));
        else if (status === 'warning') q = query(q, where('riskLevel', 'in', ['YELLOW', 'WARNING', 'warning']));
        else q = query(q, where('riskLevel', 'in', ['GREEN', 'SAFE', 'safe'])); // Default/Safe

        const snap = await getCountFromServer(q);
        return snap.data().count;
    });

    const [safeCount, warningCount, criticalCount] = await Promise.all(statusQueries);

    return {
        totalPatients,
        criticalAlerts: criticalAlertsCount,
        readmissionRate: 12.3, // Still hardcoded for now, potential todo
        statusCounts: {
            safe: safeCount,
            warning: warningCount,
            critical: criticalCount,
        }
    };
}
