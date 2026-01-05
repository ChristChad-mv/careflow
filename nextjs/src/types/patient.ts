export type RiskLevel = 'safe' | 'warning' | 'critical';

export interface Patient {
  id: string;
  name: string;
  diagnosis: string;
  dischargeDate: string;
  contactNumber: string;
  medicationPlan: Medication[];
  currentStatus: RiskLevel;
}

export interface Medication {
  name: string;
  dosage: string;
  frequency: string;
}

export interface Alert {
  id: string;
  patientId: string;
  patientName: string;
  riskLevel: RiskLevel;
  timestamp: Date;
  trigger: string;
  brief?: string;
}

export interface Interaction {
  id: string;
  timestamp: Date;
  sender: 'ai' | 'patient' | 'system';
  content: string;
  type?: 'message' | 'event';
}
