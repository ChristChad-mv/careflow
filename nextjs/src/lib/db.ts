import { initAdmin } from "@/lib/firebase-admin";
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
    const data = doc.data();
    if (!data) throw new Error("Document not found");

    // Handle nested discharge plan
    const dischargePlan = data.dischargePlan || {};
    const contact = data.contact || {};

    // Format discharge date
    let dischargeDate = "N/A";
    if (dischargePlan.dischargeDate) {
        const date = dischargePlan.dischargeDate.toDate ? dischargePlan.dischargeDate.toDate() : new Date(dischargePlan.dischargeDate);
        dischargeDate = date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    }

    return {
        id: doc.id,
        name: data.name || "Unknown Patient",
        diagnosis: dischargePlan.diagnosis || "No diagnosis",
        dischargeDate: dischargeDate,
        contactNumber: contact.phone || "No contact",
        medicationPlan: dischargePlan.medications || [],
        currentStatus: mapRiskLevel(data.riskLevel || 'GREEN'),
    };
};

// Helper to convert Firestore data to typed objects (generic fallback)
const convertDoc = <T>(doc: FirebaseFirestore.DocumentSnapshot): T => {
    const data = doc.data();
    if (!data) throw new Error("Document not found");

    // Convert Timestamps to Dates
    const converted = Object.fromEntries(
        Object.entries(data).map(([key, value]) => {
            if (value && typeof value === 'object' && 'toDate' in value) {
                return [key, (value as any).toDate()];
            }
            return [key, value];
        })
    );

    return { id: doc.id, ...converted } as T;
};

export async function getPatients(): Promise<Patient[]> {
    const admin = await initAdmin();
    const snapshot = await admin.firestore().collection("patients").get();
    return snapshot.docs.map(doc => convertPatient(doc));
}

export async function getPatient(id: string): Promise<Patient | null> {
    const admin = await initAdmin();
    const doc = await admin.firestore().collection("patients").doc(id).get();
    if (!doc.exists) return null;
    return convertPatient(doc);
}

export async function getAlerts(): Promise<Alert[]> {
    const admin = await initAdmin();
    const snapshot = await admin.firestore()
        .collection("alerts")
        .orderBy("timestamp", "desc")
        .get();
    return snapshot.docs.map(doc => convertDoc<Alert>(doc));
}

export async function getPatientAlerts(patientId: string): Promise<Alert[]> {
    const admin = await initAdmin();
    const snapshot = await admin.firestore()
        .collection("alerts")
        .where("patientId", "==", patientId)
        .orderBy("timestamp", "desc")
        .get();
    return snapshot.docs.map(doc => convertDoc<Alert>(doc));
}

export async function getInteractions(patientId: string): Promise<Interaction[]> {
    const admin = await initAdmin();
    const snapshot = await admin.firestore()
        .collection("patients")
        .doc(patientId)
        .collection("interactions")
        .orderBy("timestamp", "desc")
        .get();
    return snapshot.docs.map(doc => convertDoc<Interaction>(doc));
}

export async function getDashboardStats() {
    const patients = await getPatients();
    const alerts = await getAlerts();

    const totalPatients = patients.length;
    const criticalAlerts = alerts.filter(a => a.riskLevel === 'critical').length;

    // Calculate status counts
    const statusCounts = {
        safe: patients.filter(p => p.currentStatus === 'safe').length,
        warning: patients.filter(p => p.currentStatus === 'warning').length,
        critical: patients.filter(p => p.currentStatus === 'critical').length,
    };

    return {
        totalPatients,
        criticalAlerts,
        readmissionRate: 12.3, // Still hardcoded for now as we don't have historical data
        statusCounts
    };
}
