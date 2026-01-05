import { Patient, Alert, Interaction } from "@/types/patient";

export const mockPatients: Patient[] = [
  {
    id: "P001",
    name: "Sarah Mitchell",
    diagnosis: "Post-operative cardiac surgery (CABG)",
    dischargeDate: "2025-11-10",
    contactNumber: "+1 (555) 123-4567",
    medicationPlan: [
      { name: "Aspirin", dosage: "81mg", frequency: "Once daily" },
      { name: "Metoprolol", dosage: "50mg", frequency: "Twice daily" },
      { name: "Atorvastatin", dosage: "40mg", frequency: "Once daily at bedtime" },
    ],
    currentStatus: "critical",
  },
  {
    id: "P002",
    name: "James Rodriguez",
    diagnosis: "Pneumonia with respiratory complications",
    dischargeDate: "2025-11-12",
    contactNumber: "+1 (555) 234-5678",
    medicationPlan: [
      { name: "Amoxicillin", dosage: "500mg", frequency: "Three times daily" },
      { name: "Albuterol inhaler", dosage: "2 puffs", frequency: "Every 4-6 hours as needed" },
    ],
    currentStatus: "warning",
  },
  {
    id: "P003",
    name: "Maria Chen",
    diagnosis: "Type 2 Diabetes management",
    dischargeDate: "2025-11-08",
    contactNumber: "+1 (555) 345-6789",
    medicationPlan: [
      { name: "Metformin", dosage: "1000mg", frequency: "Twice daily with meals" },
      { name: "Insulin glargine", dosage: "20 units", frequency: "Once daily at bedtime" },
    ],
    currentStatus: "safe",
  },
];

export const mockAlerts: Alert[] = [
  {
    id: "A001",
    patientId: "P001",
    patientName: "Sarah Mitchell",
    riskLevel: "critical",
    timestamp: new Date(Date.now() - 5 * 60 * 1000), // 5 minutes ago
    trigger: "High fever (39.5°C) and shortness of breath reported",
    brief: "Patient reports persistent fever of 39.5°C for the past 6 hours, accompanied by significant shortness of breath and chest tightness. She missed her afternoon Metoprolol dose. Vital signs indicate potential post-operative complication. IMMEDIATE INTERVENTION REQUIRED.",
  },
  {
    id: "A002",
    patientId: "P002",
    patientName: "James Rodriguez",
    riskLevel: "critical",
    timestamp: new Date(Date.now() - 15 * 60 * 1000), // 15 minutes ago
    trigger: "Severe difficulty breathing, oxygen saturation 88%",
    brief: "Patient experiencing severe respiratory distress with O2 sat at 88%. Reports inability to complete sentences without gasping. Emergency assessment needed.",
  },
  {
    id: "A003",
    patientId: "P001",
    patientName: "Sarah Mitchell",
    riskLevel: "critical",
    timestamp: new Date(Date.now() - 45 * 60 * 1000), // 45 minutes ago
    trigger: "Chest pain radiating to left arm",
    brief: "New onset chest pain with radiation pattern consistent with cardiac concern. Patient is post-CABG day 4. Requires immediate cardiac assessment.",
  },
];

export const mockInteractions: Record<string, Interaction[]> = {
  P001: [
    {
      id: "I001",
      timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000),
      sender: "system",
      content: "Patient status changed from WARNING to CRITICAL",
      type: "event",
    },
    {
      id: "I002",
      timestamp: new Date(Date.now() - 5.5 * 60 * 60 * 1000),
      sender: "ai",
      content: "Good afternoon, Sarah. This is CareFlow checking in on your recovery. How are you feeling today? Any changes in your symptoms?",
      type: "message",
    },
    {
      id: "I003",
      timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000),
      sender: "patient",
      content: "Not good. I have a high fever (39.5) and I'm having trouble breathing. My chest feels tight.",
      type: "message",
    },
    {
      id: "I004",
      timestamp: new Date(Date.now() - 4.8 * 60 * 60 * 1000),
      sender: "ai",
      content: "I understand this must be concerning. Have you taken your temperature multiple times? When did the breathing difficulty start?",
      type: "message",
    },
    {
      id: "I005",
      timestamp: new Date(Date.now() - 4.5 * 60 * 60 * 1000),
      sender: "patient",
      content: "Yes, checked 3 times in the last hour. All around 39.5. Breathing has been getting worse since this morning. It's scary.",
      type: "message",
    },
    {
      id: "I006",
      timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000),
      sender: "system",
      content: "Medication reminder: Metoprolol 50mg missed (afternoon dose)",
      type: "event",
    },
    {
      id: "I007",
      timestamp: new Date(Date.now() - 3.5 * 60 * 60 * 1000),
      sender: "ai",
      content: "Sarah, based on your symptoms and the severity, I'm escalating this to your care team immediately. A nurse coordinator will contact you shortly. In the meantime, please rest and avoid any strenuous activity.",
      type: "message",
    },
  ],
  P002: [
    {
      id: "I201",
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
      sender: "ai",
      content: "Hello James, how is your breathing today? Have you needed to use your rescue inhaler?",
      type: "message",
    },
    {
      id: "I202",
      timestamp: new Date(Date.now() - 1.8 * 60 * 60 * 1000),
      sender: "patient",
      content: "Breathing is very bad. Used inhaler 4 times already today. Getting worse.",
      type: "message",
    },
    {
      id: "I203",
      timestamp: new Date(Date.now() - 1.5 * 60 * 60 * 1000),
      sender: "system",
      content: "Patient status escalated to CRITICAL",
      type: "event",
    },
  ],
};
