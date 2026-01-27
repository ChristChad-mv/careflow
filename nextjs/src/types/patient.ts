export type RiskLevel = 'safe' | 'warning' | 'critical';

export interface Patient {
  id: string;
  name: string;
  preferredLanguage: string; // Add this
  diagnosis: string;
  dischargeDate: string;
  contactNumber: string;
  email?: string;
  dateOfBirth?: string;
  contact?: {
    phone?: string;
    preferredMethod?: 'phone' | 'sms' | 'email';
  };
  medicationPlan: Medication[];
  currentStatus: RiskLevel;
  dischargePlan?: {
    hospitalId?: string;
    dischargingPhysician?: string;
    dischargeDate?: string;
    diagnosis?: string;
    medications?: Medication[];
    criticalSymptoms?: string[];
    warningSymptoms?: string[];
  };
  assignedNurse?: {
    name: string;
    email: string;
    phone: string;
  };
  nextAppointment?: {
    date: string;
    type: string;
    location: string;
  };
  lastCallSid?: string;
  aiBrief?: string;
}

export interface Medication {
  name: string;
  dosage: string;
  frequency: string;
  instructions?: string;
}

export interface Alert {
  id: string;
  hospitalId?: string;
  patientId: string;
  patientName: string;
  priority: RiskLevel;
  createdAt: string;
  trigger: string;
  brief?: string;
  status: 'active' | 'resolved' | 'in_progress';
  resolutionNote?: string;
  callSid?: string;
}

export interface Interaction {
  id: string;
  timestamp: string;
  sender: 'ai' | 'patient' | 'system';
  content: string;
  type?: 'message' | 'event';
  callSid?: string; // For Audio-First Reporting
}

