export type RiskLevel = 'safe' | 'warning' | 'critical';

export interface Patient {
  id: string;
  name: string;
  diagnosis: string;
  dischargeDate: string;
  contactNumber: string;
  email?: string;
  dateOfBirth?: string;
  contact?: {
    preferredMethod?: 'call' | 'sms' | 'email';
  };
  medicationPlan: Medication[];
  currentStatus: RiskLevel;
  dischargePlan?: {
    hospitalId?: string;
    dischargingPhysician?: string;
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
  lastCallSid?: string; // For Audio-First Reporting
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
  createdAt: Date;
  trigger: string;
  brief?: string;
  status: 'active' | 'resolved' | 'in_progress';
  callSid?: string;
}

export interface Interaction {
  id: string;
  timestamp: Date;
  sender: 'ai' | 'patient' | 'system';
  content: string;
  type?: 'message' | 'event';
  callSid?: string; // For Audio-First Reporting
}

