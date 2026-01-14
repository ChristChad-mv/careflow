import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Phone, Calendar, Pill, User, MapPin, Stethoscope, Mail, AlertTriangle } from "lucide-react";
import { getPatient } from "@/lib/db";
import { notFound } from "next/navigation";
import { format } from "date-fns";
import { EditMedicationDialog } from "@/components/patient/EditMedicationDialog";
import { EditAppointmentDialog } from "@/components/patient/EditAppointmentDialog";

export default async function PatientProfile({ params }: { params: Promise<{ patientId: string }> }) {
  const { patientId } = await params;
  const patient = await getPatient(patientId);

  if (!patient) return notFound();

  // Helper for safe date formatting
  const formatDate = (date: Date | string | undefined) => {
    if (!date) return 'N/A';
    try {
      return format(new Date(date), 'PPP');
    } catch (e) {
      return String(date);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            {patient.name}
          </h1>
          <p className="text-muted-foreground">Patient ID: {patient.id}</p>
        </div>
        <div className="flex items-center gap-3">
          <Badge className={
            patient.currentStatus === 'critical' ? 'bg-destructive' :
              patient.currentStatus === 'warning' ? 'bg-yellow-500' : 'bg-green-500'
          }>
            {patient.currentStatus.toUpperCase()}
          </Badge>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

        {/* Column 1: Demographics & Contact */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5 text-primary" />
                Patient Details
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <span className="text-sm font-medium text-muted-foreground">Date of Birth / Age</span>
                <div className="font-medium">{formatDate(patient.dateOfBirth)}</div>
              </div>

              <div>
                <span className="text-sm font-medium text-muted-foreground">Contact Information</span>
                <div className="flex items-center gap-2 mt-2">
                  <Phone className="h-4 w-4 text-muted-foreground" />
                  <span>{patient.contactNumber}</span>
                </div>
                {patient.email && (
                  <div className="flex items-center gap-2 mt-1">
                    <Mail className="h-4 w-4 text-muted-foreground" />
                    <span>{patient.email}</span>
                  </div>
                )}
                <div className="mt-2 text-xs bg-secondary text-secondary-foreground px-2 py-1 rounded inline-block">
                  Preferred: {patient.contact?.preferredMethod?.toUpperCase() || 'CALL'}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Stethoscope className="h-5 w-5 text-blue-500" />
                Care Team
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {patient.assignedNurse ? (
                <div>
                  <span className="text-sm font-medium text-muted-foreground block mb-1">Assigned Nurse</span>
                  <div className="font-semibold">{patient.assignedNurse.name}</div>
                  <div className="text-sm">{patient.assignedNurse.phone}</div>
                  <div className="text-sm text-muted-foreground">{patient.assignedNurse.email}</div>
                </div>
              ) : (
                <div className="text-muted-foreground">No nurse assigned.</div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Column 2: Clinical Status & Discharge */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ActivityIcon className="h-5 w-5 text-green-600" />
                Discharge Plan
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <span className="text-sm font-medium text-muted-foreground">Primary Diagnosis</span>
                <div className="font-bold text-lg">{patient.diagnosis}</div>
              </div>
              <div>
                <span className="text-sm font-medium text-muted-foreground">Discharge Date</span>
                <div className="font-medium">{patient.dischargeDate}</div>
              </div>
              <Separator />
              <div>
                <span className="text-sm font-medium text-muted-foreground">Discharging Physician</span>
                <div className="font-medium">{patient.dischargePlan?.dischargingPhysician || 'N/A'}</div>
                <div className="text-xs text-muted-foreground">{patient.dischargePlan?.hospitalId}</div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-yellow-400">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-yellow-500" />
                Risk Factors (Watchlist)
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <span className="text-sm font-semibold text-destructive block mb-1">Critical Symptoms</span>
                <ul className="list-disc pl-5 text-sm">
                  {patient.dischargePlan?.criticalSymptoms?.map((s: string, i: number) => (
                    <li key={i}>{s}</li>
                  )) || <li>None listed</li>}
                </ul>
              </div>
              <div>
                <span className="text-sm font-semibold text-yellow-600 block mb-1">Warning Symptoms</span>
                <ul className="list-disc pl-5 text-sm">
                  {patient.dischargePlan?.warningSymptoms?.map((s: string, i: number) => (
                    <li key={i}>{s}</li>
                  )) || <li>None listed</li>}
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Column 3: Medications & Appointments */}
        <div className="space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5 text-purple-500" />
                Next Appointment
              </CardTitle>
              <EditAppointmentDialog patient={patient} />
            </CardHeader>
            <CardContent>
              {patient.nextAppointment?.date ? (
                <div className="bg-purple-50 dark:bg-purple-950/20 p-4 rounded-lg">
                  <div className="font-bold text-lg text-purple-700 dark:text-purple-300">
                    {formatDate(patient.nextAppointment.date)}
                  </div>
                  <div className="font-medium mt-1">{patient.nextAppointment.type}</div>
                  <div className="flex items-center gap-2 mt-2 text-sm text-muted-foreground">
                    <MapPin className="h-4 w-4" />
                    {patient.nextAppointment.location}
                  </div>
                </div>
              ) : (
                <div className="text-muted-foreground italic">No upcoming appointments scheduled.</div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Pill className="h-5 w-5 text-blue-500" />
                Medication Schedule
              </CardTitle>
              <EditMedicationDialog patient={patient} />
            </CardHeader>
            <CardContent>
              <ul className="space-y-4">
                {patient.medicationPlan?.map((med, idx) => (
                  <li key={idx} className="border-b pb-3 last:border-0 last:pb-0">
                    <div className="flex justify-between items-start">
                      <div className="font-semibold">{med.name}</div>
                      <Badge variant="outline">{med.dosage}</Badge>
                    </div>
                    <div className="text-sm mt-1">{med.frequency}</div>
                    {med.instructions && (
                      <div className="text-xs text-muted-foreground mt-1 italic">
                        "{med.instructions}"
                      </div>
                    )}
                  </li>
                ))}
                {(!patient.medicationPlan || patient.medicationPlan.length === 0) && (
                  <li className="text-muted-foreground text-sm italic">
                    No medications listed. Click edit to add.
                  </li>
                )}
              </ul>
            </CardContent>
          </Card>
        </div>

      </div>
    </div>
  );
}

function ActivityIcon(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
    </svg>
  )
}
